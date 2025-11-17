# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import date, datetime, timedelta
from typing import Optional, List
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from models.schemas import MetricsResponse, DailyMetric, ProductMetric, SummaryResponse
from services.database import get_db, IntegratedRecord, FakePurchase
from models.auth import User, Tenant
from auth.dependencies import get_current_user, get_current_tenant

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    product: Optional[str] = Query(None),
    group_by: str = Query('option', regex='^(option|product)$'),
    include_fake_purchase_adjustment: bool = Query(False, description="가구매 조정 포함 여부"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get performance metrics for a date range

    Args:
        group_by: 'option' (default) - group by option_id, 'product' - group by product_name
        include_fake_purchase_adjustment: If True, adjust metrics by deducting fake purchases
    """

    # Build query - filter by tenant
    query = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id)

    # Apply filters
    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)
    if product:
        query = query.filter(IntegratedRecord.product_name.like(f"%{product}%"))

    records = query.all()

    # 가구매 조정 로직
    fake_purchase_adjustments = {}  # {(date, option_id): {sales_deduction, quantity_deduction, cost_saved}}

    # IntegratedRecord에서 단위당 비용 정보를 미리 조회
    unit_cost_map = {}  # {(date, option_id): (cost_price, fee_amount, vat)}
    for record in records:
        key = (record.date, record.option_id)
        unit_cost_map[key] = (record.cost_price or 0, record.fee_amount or 0, record.vat or 0)

    if include_fake_purchase_adjustment:
        # Query fake purchases for the same date range
        fake_query = db.query(FakePurchase).filter(FakePurchase.tenant_id == current_tenant.id)

        if start_date:
            fake_query = fake_query.filter(FakePurchase.date >= start_date)
        if end_date:
            fake_query = fake_query.filter(FakePurchase.date <= end_date)
        if product:
            fake_query = fake_query.filter(FakePurchase.product_name.like(f"%{product}%"))

        fake_purchases = fake_query.all()

        # Build adjustments dictionary
        for fp in fake_purchases:
            key = (fp.date, fp.option_id)

            # Calculate sales deduction (quantity × unit_price)
            sales_deduction = (fp.quantity or 0) * (fp.unit_price or 0)

            # Calculate cost saved (가구매는 실제로 비용이 발생하지 않았으므로)
            # 비용 절감 = 가구매 수량 × (도매가 + 수수료 + 부가세)
            cost_saved = 0
            if key in unit_cost_map:
                cost_price, fee_amount, vat = unit_cost_map[key]
                unit_cost = cost_price + fee_amount + vat
                cost_saved = (fp.quantity or 0) * unit_cost

            fake_purchase_adjustments[key] = {
                'sales_deduction': sales_deduction,
                'quantity_deduction': fp.quantity or 0,
                'cost_saved': cost_saved  # 실제로 지불하지 않은 비용 (이익에 더해져야 함)
            }

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

    # Calculate daily metrics
    daily_metrics = {}
    for record in records:
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

        # Apply fake purchase adjustments if needed
        adjustment_key = (record.date, record.option_id)
        adjustment = fake_purchase_adjustments.get(adjustment_key, {})

        sales_deduction = adjustment.get('sales_deduction', 0)
        quantity_deduction = adjustment.get('quantity_deduction', 0)
        cost_saved = adjustment.get('cost_saved', 0)

        # Adjust sales and quantity (차감)
        adjusted_sales = record.sales_amount - sales_deduction
        adjusted_quantity = record.sales_quantity - quantity_deduction

        # Adjust profit
        # - 매출 감소: sales_deduction 만큼 이익 감소
        # + 비용 절감: 실제로 물건을 받지 않았으므로 cost_saved 만큼 이익 증가
        adjusted_profit = record.net_profit - sales_deduction + cost_saved

        # Adjust ad cost (가구매는 광고비와 무관)
        adjusted_ad_cost = record.ad_cost

        daily_metrics[date_key]['total_sales'] += adjusted_sales
        daily_metrics[date_key]['total_profit'] += adjusted_profit
        daily_metrics[date_key]['ad_cost'] += adjusted_ad_cost
        daily_metrics[date_key]['total_quantity'] += adjusted_quantity

    # Calculate margin rate for each day
    for metrics in daily_metrics.values():
        if metrics['total_sales'] > 0:
            metrics['margin_rate'] = (metrics['total_profit'] / metrics['total_sales']) * 100

    # Sort daily trend by date
    daily_trend = [
        DailyMetric(**metrics)
        for metrics in sorted(daily_metrics.values(), key=lambda x: x['date'])
    ]

    # Calculate product metrics
    product_metrics = {}

    if group_by == 'option':
        # 옵션별로 개별 표시 (기존 방식)
        for record in records:
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

            # Apply fake purchase adjustments if needed
            adjustment_key = (record.date, record.option_id)
            adjustment = fake_purchase_adjustments.get(adjustment_key, {})

            sales_deduction = adjustment.get('sales_deduction', 0)
            quantity_deduction = adjustment.get('quantity_deduction', 0)
            cost_saved = adjustment.get('cost_saved', 0)

            # Adjust values
            adjusted_sales = record.sales_amount - sales_deduction
            adjusted_quantity = record.sales_quantity - quantity_deduction
            adjusted_profit = record.net_profit - sales_deduction + cost_saved
            adjusted_ad_cost = record.ad_cost
            adjusted_total_cost = record.total_cost - cost_saved  # 실제로 지불하지 않은 비용 제외

            product_metrics[option_id]['total_sales'] += adjusted_sales
            product_metrics[option_id]['total_profit'] += adjusted_profit
            product_metrics[option_id]['total_quantity'] += adjusted_quantity
            product_metrics[option_id]['total_ad_cost'] += adjusted_ad_cost
            product_metrics[option_id]['total_cost'] += adjusted_total_cost
    else:
        # 상품별로 통합 표시 (product_name 기준 그룹핑)
        for record in records:
            product_name = record.product_name
            if product_name not in product_metrics:
                product_metrics[product_name] = {
                    'option_id': 0,  # Dummy value for grouped view
                    'option_name': '',
                    'option_names': [],  # Collect all option names
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

            # Apply fake purchase adjustments if needed
            adjustment_key = (record.date, record.option_id)
            adjustment = fake_purchase_adjustments.get(adjustment_key, {})

            sales_deduction = adjustment.get('sales_deduction', 0)
            quantity_deduction = adjustment.get('quantity_deduction', 0)
            cost_saved = adjustment.get('cost_saved', 0)

            # Adjust values
            adjusted_sales = record.sales_amount - sales_deduction
            adjusted_quantity = record.sales_quantity - quantity_deduction
            adjusted_profit = record.net_profit - sales_deduction + cost_saved
            adjusted_ad_cost = record.ad_cost
            adjusted_total_cost = record.total_cost - cost_saved  # 실제로 지불하지 않은 비용 제외

            product_metrics[product_name]['total_sales'] += adjusted_sales
            product_metrics[product_name]['total_profit'] += adjusted_profit
            product_metrics[product_name]['total_quantity'] += adjusted_quantity
            product_metrics[product_name]['total_ad_cost'] += adjusted_ad_cost
            product_metrics[product_name]['total_cost'] += adjusted_total_cost

            # Collect unique option names
            if record.option_name and record.option_name not in product_metrics[product_name]['option_names']:
                product_metrics[product_name]['option_names'].append(record.option_name)

        # Join option names
        for metrics in product_metrics.values():
            if metrics['option_names']:
                metrics['option_name'] = ', '.join(metrics['option_names'])
            del metrics['option_names']  # Remove temporary field

    # Calculate margin rate, cost rate, ad cost rate
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

    # DEBUG: Show sales values before sorting
    print(f"\n=== SORTING DEBUG (group_by={group_by}) ===")
    print(f"Total filtered records: {len(filtered_metrics)}")
    if len(filtered_metrics) > 0:
        print("Sales values before sorting (first 10):")
        for i, m in enumerate(list(filtered_metrics)[:10]):
            print(f"  {i+1}. {m['product_name'][:30]:30s} - Sales: {m['total_sales']:,.0f}")

    # Sort products by sales
    sorted_metrics = sorted(
        filtered_metrics,
        key=lambda x: x['total_sales'],
        reverse=True
    )

    # DEBUG: Show sales values after sorting
    print("\nSales values after sorting (first 10):")
    for i, m in enumerate(sorted_metrics[:10]):
        print(f"  {i+1}. {m['product_name'][:30]:30s} - Sales: {m['total_sales']:,.0f}")
    print("=== END SORTING DEBUG ===\n")

    by_product = [
        ProductMetric(**metrics)
        for metrics in sorted_metrics
    ]

    # Calculate overall summary
    total_sales = sum(m.total_sales for m in daily_trend)
    total_ad_cost = sum(m.ad_cost for m in daily_trend)
    total_profit = sum(m.total_profit for m in daily_trend)
    total_quantity = sum(record.sales_quantity for record in records)
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

    # Build fake purchase adjustments dictionary
    fake_purchase_adjustments = {}

    # IntegratedRecord에서 단위당 비용 정보를 미리 조회
    unit_cost_map = {}  # {(date, option_id): (cost_price, fee_amount, vat)}
    for record in records:
        key = (record.date, record.option_id)
        unit_cost_map[key] = (record.cost_price or 0, record.fee_amount or 0, record.vat or 0)

    if include_fake_purchase_adjustment:
        fake_query = db.query(FakePurchase).filter(FakePurchase.tenant_id == current_tenant.id)
        fake_query = fake_query.filter(FakePurchase.product_name == product_name)

        if option_id:
            fake_query = fake_query.filter(FakePurchase.option_id == option_id)
        if start_date:
            fake_query = fake_query.filter(FakePurchase.date >= start_date)
        if end_date:
            fake_query = fake_query.filter(FakePurchase.date <= end_date)

        fake_purchases = fake_query.all()

        for fp in fake_purchases:
            key = (fp.date, fp.option_id)
            sales_deduction = (fp.quantity or 0) * (fp.unit_price or 0)

            # Calculate cost saved (가구매는 실제로 비용이 발생하지 않았으므로)
            cost_saved = 0
            if key in unit_cost_map:
                cost_price, fee_amount, vat = unit_cost_map[key]
                unit_cost = cost_price + fee_amount + vat
                cost_saved = (fp.quantity or 0) * unit_cost

            fake_purchase_adjustments[key] = {
                'sales_deduction': sales_deduction,
                'quantity_deduction': fp.quantity or 0,
                'cost_saved': cost_saved
            }

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

        adjusted_sales = record.sales_amount - sales_deduction
        adjusted_quantity = record.sales_quantity - quantity_deduction
        adjusted_profit = record.net_profit - sales_deduction + cost_saved
        adjusted_ad_cost = record.ad_cost

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
