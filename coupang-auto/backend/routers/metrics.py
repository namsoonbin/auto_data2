# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
import logging

from models.schemas import MetricsResponse, DailyMetric, ProductMetric, SummaryResponse
from services.database import get_db, IntegratedRecord, FakePurchase
from services.adjustment_service import build_fake_purchase_adjustments, apply_fake_purchase_adjustment
from models.auth import User, Tenant
from auth.dependencies import get_current_user, get_current_tenant
from utils.query_helpers import escape_like_pattern
from utils.performance import monitor_performance, PerformanceTracker

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics", response_model=MetricsResponse)
@monitor_performance(threshold_ms=1000)  # 1초 이상 소요 시 경고
async def get_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    product: Optional[str] = Query(None),
    group_by: str = Query('option', regex='^(option|product)$'),
    include_fake_purchase_adjustment: bool = Query(False, description="가구매 조정 포함 여부"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="최대 레코드 수 (성능 보호)"),
    offset: int = Query(0, ge=0, description="건너뛸 레코드 수 (페이지네이션)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    판매 성과 메트릭 조회 및 분석

    통합 데이터(IntegratedRecord)에서 일별/상품별 판매 성과를 집계하고 분석합니다.
    가구매 조정 기능을 통해 실제 판매 수치를 정확하게 계산할 수 있습니다.

    Args:
        start_date: 조회 시작일 (없으면 전체 기간)
        end_date: 조회 종료일 (없으면 전체 기간)
        product: 상품명 필터 (부분 일치 검색)
        group_by: 그룹핑 방식
            - 'option': 옵션별 개별 표시 (기본값)
            - 'product': 상품명별 통합 표시
        include_fake_purchase_adjustment: 가구매 조정 포함 여부
            - False (기본값): 원본 데이터 그대로 사용
            - True: 가구매 수량/매출을 차감하고 비용 절감분을 이익에 반영

    Returns:
        MetricsResponse:
            - period: 조회 기간
            - total_sales: 총 매출액
            - total_profit: 총 순이익
            - total_ad_cost: 총 광고비
            - total_quantity: 총 판매 수량
            - avg_margin_rate: 평균 마진율 (%)
            - daily_trend: 일별 추이 데이터
            - by_product: 상품별/옵션별 집계 데이터

    Business Logic:
        가구매 조정 시 각 레코드에 대해:
        1. 매출 조정: sales_amount - (가구매_수량 × 단가)
        2. 수량 조정: sales_quantity - 가구매_수량
        3. 이익 조정: net_profit - 매출차감 + 비용절감 - 가구매비용
           - 비용절감 = 가구매_수량 × (도매가 + 수수료 + 부가세)
           - 가구매비용 = (단가 × 12%) + 4,500원 (광고비 성격, 부가세 미적용)
           - 가구매는 실제 비용 발생 없이 재고 복원되므로 비용 절감 효과
        4. 광고비 조정: ad_cost + 가구매비용
           - 가구매 서비스 비용을 광고비에 포함
    """

    # Build query - filter by tenant
    query = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id)

    # Apply filters
    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)
    if product:
        query = query.filter(IntegratedRecord.product_name.like(f"%{escape_like_pattern(product)}%"))

    # Apply pagination
    if limit:
        query = query.limit(limit).offset(offset)

    records = query.all()

    # 가구매 조정 로직 (서비스 함수 사용)
    unit_cost_map, fake_purchase_adjustments = build_fake_purchase_adjustments(
        db=db,
        tenant_id=current_tenant.id,
        records=records,
        start_date=start_date,
        end_date=end_date,
        product=product,
        include_adjustment=include_fake_purchase_adjustment
    )

    if not records:
        return MetricsResponse(
            period=f"{start_date or 'all'} to {end_date or 'all'}",
            total_sales=0.0,
            total_profit=0.0,
            total_ad_cost=0.0,
            total_quantity=0,
            avg_margin_rate=0.0,
            daily_trend=[],
            by_product=[]
        )

    # Single-pass aggregation: Calculate both daily and product metrics in one iteration
    daily_metrics = {}
    product_metrics = {}

    for record in records:
        # Calculate adjustments once per record
        adjustment_key = (record.date, record.option_id)
        adjustment = fake_purchase_adjustments.get(adjustment_key, {})

        sales_deduction = adjustment.get('sales_deduction', 0)
        quantity_deduction = adjustment.get('quantity_deduction', 0)
        cost_saved = adjustment.get('cost_saved', 0)
        fake_purchase_cost = adjustment.get('fake_purchase_cost', 0)

        # Apply adjustments (계산은 한 번만)
        adjusted_sales = record.sales_amount - sales_deduction
        adjusted_quantity = record.sales_quantity - quantity_deduction
        adjusted_profit = record.net_profit - sales_deduction + cost_saved - fake_purchase_cost
        adjusted_ad_cost = record.ad_cost + fake_purchase_cost
        adjusted_total_cost = record.total_cost - cost_saved

        # 음수 수량 검증 (가구매 수량이 실제 판매 초과)
        if adjusted_quantity < 0:
            logger.warning(
                f"음수 수량 발생: date={record.date}, option_id={record.option_id}, "
                f"sales_quantity={record.sales_quantity}, quantity_deduction={quantity_deduction}"
            )

        # Build daily metrics
        date_key = record.date
        if date_key not in daily_metrics:
            daily_metrics[date_key] = {
                'date': date_key,
                'total_sales': 0.0,
                'total_profit': 0.0,
                'ad_cost': 0.0,
                'total_quantity': 0,
                'margin_rate': 0.0
            }

        daily_metrics[date_key]['total_sales'] += adjusted_sales
        daily_metrics[date_key]['total_profit'] += adjusted_profit
        daily_metrics[date_key]['ad_cost'] += adjusted_ad_cost
        daily_metrics[date_key]['total_quantity'] += adjusted_quantity

        # Build product metrics (group_by dependent)
        if group_by == 'option':
            # 옵션별로 개별 표시
            option_id = record.option_id
            if option_id not in product_metrics:
                product_metrics[option_id] = {
                    'option_id': option_id,
                    'option_name': record.option_name or '',
                    'product_name': record.product_name,
                    'total_sales': 0.0,
                    'total_profit': 0.0,
                    'total_quantity': 0,
                    'total_ad_cost': 0.0,
                    'total_cost': 0.0,
                    'margin_rate': 0.0,
                    'cost_rate': 0.0,
                    'ad_cost_rate': 0.0
                }

            product_metrics[option_id]['total_sales'] += adjusted_sales
            product_metrics[option_id]['total_profit'] += adjusted_profit
            product_metrics[option_id]['total_quantity'] += adjusted_quantity
            product_metrics[option_id]['total_ad_cost'] += adjusted_ad_cost
            product_metrics[option_id]['total_cost'] += adjusted_total_cost
        else:
            # 상품별로 통합 표시 (product_name 기준 그룹핑)
            product_name = record.product_name
            if product_name not in product_metrics:
                product_metrics[product_name] = {
                    'option_id': 0,
                    'option_name': '',
                    'option_names': [],
                    'product_name': product_name,
                    'total_sales': 0.0,
                    'total_profit': 0.0,
                    'total_quantity': 0,
                    'total_ad_cost': 0.0,
                    'total_cost': 0.0,
                    'margin_rate': 0.0,
                    'cost_rate': 0.0,
                    'ad_cost_rate': 0.0
                }

            product_metrics[product_name]['total_sales'] += adjusted_sales
            product_metrics[product_name]['total_profit'] += adjusted_profit
            product_metrics[product_name]['total_quantity'] += adjusted_quantity
            product_metrics[product_name]['total_ad_cost'] += adjusted_ad_cost
            product_metrics[product_name]['total_cost'] += adjusted_total_cost

            # Collect unique option names
            if record.option_name and record.option_name not in product_metrics[product_name]['option_names']:
                product_metrics[product_name]['option_names'].append(record.option_name)

    # Post-processing for product mode: join option names
    if group_by == 'product':
        for metrics in product_metrics.values():
            if metrics['option_names']:
                metrics['option_name'] = ', '.join(metrics['option_names'])
            del metrics['option_names']

    # Calculate margin rates for daily metrics
    # 일별 순이익률 = (일별 순이익 / 일별 매출) × 100
    for metrics in daily_metrics.values():
        if metrics['total_sales'] > 0:
            metrics['margin_rate'] = (metrics['total_profit'] / metrics['total_sales']) * 100

    # Sort daily trend by date
    daily_trend = [
        DailyMetric(**metrics)
        for metrics in sorted(daily_metrics.values(), key=lambda x: x['date'])
    ]

    # Calculate margin rate, cost rate, ad cost rate for product metrics
    #
    # 마진율 계산 공식:
    # - margin_rate: 순이익률 = (순이익 / 매출) × 100
    #   → 최종적으로 남는 이익의 비율 (모든 비용 차감 후)
    #
    # - cost_rate: 원가이익률 = ((매출 - 총비용) / 매출) × 100
    #   → total_cost에는 원가 + 수수료 + 부가세 + 배송비가 포함됨
    #   → 광고비를 제외한 비용 차감 후 남는 이익률
    #
    # - ad_cost_rate: 광고비율 = ((광고비 × 1.1) / 매출) × 100
    #   → 1.1 = 부가세 10% 포함
    #   → 매출 대비 광고비 지출 비율
    #
    # 주의: margin_rate = cost_rate - ad_cost_rate 관계 성립
    for metrics in product_metrics.values():
        if metrics['total_sales'] != 0:
            metrics['margin_rate'] = (metrics['total_profit'] / metrics['total_sales']) * 100
            metrics['cost_rate'] = ((metrics['total_sales'] - metrics['total_cost']) / metrics['total_sales']) * 100
            metrics['ad_cost_rate'] = ((metrics['total_ad_cost'] * 1.1) / metrics['total_sales']) * 100

    # Filter out records with 0 sales (매출이 0인 레코드 제외, 음수는 포함)
    filtered_metrics = [
        metrics for metrics in product_metrics.values()
        if metrics['total_sales'] != 0
    ]

    # 정렬 전 디버그 로깅 (개발 시에만 필요)
    logger.debug(f"Sorting metrics: group_by={group_by}, filtered_records={len(filtered_metrics)}")
    if logger.isEnabledFor(logging.DEBUG) and len(filtered_metrics) > 0:
        top_10 = list(filtered_metrics)[:10]
        logger.debug(f"Top 10 before sorting: {[(m['product_name'][:30], m['total_sales']) for m in top_10]}")

    # Sort products by sales
    sorted_metrics = sorted(
        filtered_metrics,
        key=lambda x: x['total_sales'],
        reverse=True
    )

    # 정렬 후 디버그 로깅
    if logger.isEnabledFor(logging.DEBUG) and len(sorted_metrics) > 0:
        top_10 = sorted_metrics[:10]
        logger.debug(f"Top 10 after sorting: {[(m['product_name'][:30], m['total_sales']) for m in top_10]}")

    by_product = [
        ProductMetric(**metrics)
        for metrics in sorted_metrics
    ]

    # Calculate overall summary
    total_sales = sum(m.total_sales for m in daily_trend)
    total_ad_cost = sum(m.ad_cost for m in daily_trend)
    total_profit = sum(m.total_profit for m in daily_trend)
    total_quantity = sum(m.total_quantity for m in daily_trend)  # 가구매 조정 반영
    avg_margin_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0

    # Build response
    response = MetricsResponse(
        period=f"{start_date or 'all'} to {end_date or 'all'}",
        total_sales=round(total_sales, 2),
        total_profit=round(total_profit, 2),
        total_ad_cost=round(total_ad_cost, 2),
        total_quantity=total_quantity,
        avg_margin_rate=round(avg_margin_rate, 2),
        daily_trend=daily_trend,
        by_product=by_product
    )

    return response


@router.get("/metrics/weekly")
async def get_weekly_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get weekly aggregated metrics"""

    query = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id)

    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)

    records = query.all()

    weekly_data = {}
    for record in records:
        iso_year, iso_week, _ = record.date.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        if week_key not in weekly_data:
            weekly_data[week_key] = {
                'week': week_key,
                'sales': 0.0,
                'quantity': 0,
                'profit': 0.0,
                'ad_cost': 0.0,
                'roas': 0.0
            }

        weekly_data[week_key]['sales'] += record.sales_amount
        weekly_data[week_key]['quantity'] += record.sales_quantity
        weekly_data[week_key]['profit'] += record.net_profit
        weekly_data[week_key]['ad_cost'] += record.ad_cost

    # Calculate ROAS for each week
    for data in weekly_data.values():
        if data['ad_cost'] > 0:
            data['roas'] = data['sales'] / data['ad_cost']

    weekly_list = sorted(weekly_data.values(), key=lambda x: x['week'])

    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "weekly_data": weekly_list
    }


@router.get("/metrics/summary", response_model=SummaryResponse)
async def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get overall summary statistics"""

    records = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id).all()

    if not records:
        return SummaryResponse(
            total_sales=0.0,
            total_profit=0.0,
            total_ad_cost=0.0,
            avg_margin_rate=0.0,
            total_quantity=0,
            unique_products=0,
            date_range=""
        )

    # Calculate totals
    total_sales = sum(r.sales_amount for r in records)
    total_ad_cost = sum(r.ad_cost for r in records)
    total_profit = sum(r.net_profit for r in records)
    total_quantity = sum(r.sales_quantity for r in records)

    avg_margin_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0

    # Count unique products for this tenant
    product_count = db.query(func.count(func.distinct(IntegratedRecord.product_name))).filter(
        IntegratedRecord.tenant_id == current_tenant.id
    ).scalar() or 0

    # Get date range
    dates = [r.date for r in records if r.date]
    date_range = ""
    if dates:
        min_date = min(dates)
        max_date = max(dates)
        date_range = f"{min_date.isoformat()} to {max_date.isoformat()}"

    return SummaryResponse(
        total_sales=round(total_sales, 2),
        total_profit=round(total_profit, 2),
        total_ad_cost=round(total_ad_cost, 2),
        avg_margin_rate=round(avg_margin_rate, 2),
        total_quantity=total_quantity,
        unique_products=product_count,
        date_range=date_range
    )


@router.get("/metrics/products")
async def get_product_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get list of all products with their metrics"""

    products = db.query(
        IntegratedRecord.product_name,
        func.sum(IntegratedRecord.sales_amount).label('total_sales'),
        func.sum(IntegratedRecord.net_profit).label('total_profit'),
        func.sum(IntegratedRecord.sales_quantity).label('total_quantity'),
        func.sum(IntegratedRecord.ad_cost).label('total_ad_cost'),
        func.max(IntegratedRecord.date).label('last_sale_date')
    ).filter(
        IntegratedRecord.tenant_id == current_tenant.id
    ).group_by(IntegratedRecord.product_name).all()

    product_list = []
    for p in products:
        roas = (p.total_sales / p.total_ad_cost) if p.total_ad_cost and p.total_ad_cost > 0 else 0
        margin_rate = (p.total_profit / p.total_sales * 100) if p.total_sales and p.total_sales > 0 else 0

        product_list.append({
            "product_name": p.product_name,
            "total_sales": round(p.total_sales or 0, 2),
            "total_profit": round(p.total_profit or 0, 2),
            "total_quantity": p.total_quantity or 0,
            "total_ad_cost": round(p.total_ad_cost or 0, 2),
            "roas": round(roas, 2),
            "margin_rate": round(margin_rate, 2),
            "last_sale_date": p.last_sale_date.isoformat() if p.last_sale_date else None
        })

    # Sort by total sales
    product_list.sort(key=lambda x: x['total_sales'], reverse=True)

    return {
        "products": product_list,
        "count": len(product_list)
    }


@router.get("/metrics/product-trend")
async def get_product_trend(
    product_name: str = Query(..., description="Product name to filter"),
    option_id: Optional[int] = Query(None, description="Optional option ID to filter"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_fake_purchase_adjustment: bool = Query(False, description="가구매 조정 포함 여부"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get daily trend for a specific product"""

    query = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id)

    # Filter by product name
    query = query.filter(IntegratedRecord.product_name == product_name)

    # Optional: filter by option_id
    if option_id:
        query = query.filter(IntegratedRecord.option_id == option_id)

    # Apply date filters
    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)

    records = query.all()

    if not records:
        return {
            "product_name": product_name,
            "daily_trend": []
        }

    # 가구매 조정 로직 (서비스 함수 사용)
    unit_cost_map, fake_purchase_adjustments = build_fake_purchase_adjustments(
        db=db,
        tenant_id=current_tenant.id,
        records=records,
        start_date=start_date,
        end_date=end_date,
        product=product_name,
        option_id=option_id,
        include_adjustment=include_fake_purchase_adjustment,
        exact_match=True  # product_name을 정확히 일치
    )

    # Group by date and sum values
    daily_metrics = {}
    for record in records:
        date_key = record.date
        if date_key not in daily_metrics:
            daily_metrics[date_key] = {
                'date': date_key,
                'total_sales': 0.0,
                'total_profit': 0.0,
                'ad_cost': 0.0,
                'total_quantity': 0
            }

        # Apply fake purchase adjustments
        adjustment_key = (record.date, record.option_id)
        adjustment = fake_purchase_adjustments.get(adjustment_key, {})

        sales_deduction = adjustment.get('sales_deduction', 0)
        quantity_deduction = adjustment.get('quantity_deduction', 0)
        cost_saved = adjustment.get('cost_saved', 0)
        fake_purchase_cost = adjustment.get('fake_purchase_cost', 0)

        adjusted_sales = record.sales_amount - sales_deduction
        adjusted_quantity = record.sales_quantity - quantity_deduction

        # 음수 수량 검증
        if adjusted_quantity < 0:
            logger.warning(
                f"음수 수량 발생 (trend): date={record.date}, option_id={record.option_id}, "
                f"sales_quantity={record.sales_quantity}, quantity_deduction={quantity_deduction}"
            )

        adjusted_profit = record.net_profit - sales_deduction + cost_saved - fake_purchase_cost
        adjusted_ad_cost = record.ad_cost + fake_purchase_cost

        daily_metrics[date_key]['total_sales'] += adjusted_sales
        daily_metrics[date_key]['total_profit'] += adjusted_profit
        daily_metrics[date_key]['ad_cost'] += adjusted_ad_cost
        daily_metrics[date_key]['total_quantity'] += adjusted_quantity

    # Sort by date
    daily_trend = sorted(daily_metrics.values(), key=lambda x: x['date'])

    return {
        "product_name": product_name,
        "daily_trend": daily_trend
    }


@router.get("/metrics/roas")
async def get_roas_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get ROAS (Return on Ad Spend) metrics"""

    query = db.query(IntegratedRecord).filter(
        IntegratedRecord.tenant_id == current_tenant.id,
        IntegratedRecord.ad_cost > 0
    )

    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)

    records = query.all()

    if not records:
        return {
            "overall_roas": 0.0,
            "total_conversion_sales": 0.0,
            "total_ad_cost": 0.0,
            "by_product": []
        }

    total_conversion_sales = sum(r.conversion_sales for r in records)
    total_ad_cost = sum(r.ad_cost for r in records)
    overall_roas = (total_conversion_sales / total_ad_cost * 100) if total_ad_cost > 0 else 0

    # ROAS by product
    product_roas = {}
    for record in records:
        product_name = record.product_name
        if product_name not in product_roas:
            product_roas[product_name] = {
                'product_name': product_name,
                'conversion_sales': 0.0,
                'ad_cost': 0.0,
                'roas': 0.0
            }

        product_roas[product_name]['conversion_sales'] += record.conversion_sales
        product_roas[product_name]['ad_cost'] += record.ad_cost

    # Calculate ROAS for each product (전환 매출액 / 광고비 × 100)
    for data in product_roas.values():
        if data['ad_cost'] > 0:
            data['roas'] = (data['conversion_sales'] / data['ad_cost']) * 100

    # Sort by ROAS
    by_product = sorted(product_roas.values(), key=lambda x: x['roas'], reverse=True)

    return {
        "overall_roas": round(overall_roas, 2),
        "total_conversion_sales": round(total_conversion_sales, 2),
        "total_ad_cost": round(total_ad_cost, 2),
        "by_product": by_product
    }
