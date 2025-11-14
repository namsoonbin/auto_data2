# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import pandas as pd
import io

from services.database import get_db, IntegratedRecord, FakePurchase
from models.schemas import BatchDeleteRequest, BatchDeleteResponse
from models.auth import User, Tenant
from auth.dependencies import get_current_user, get_current_tenant

router = APIRouter()


@router.get("/data/records")
async def get_all_records(
    limit: Optional[int] = Query(None, description="Limit number of records"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    start_date: Optional[date] = Query(None, description="Filter from this date"),
    end_date: Optional[date] = Query(None, description="Filter to this date"),
    option_id: Optional[int] = Query(None, description="Filter by option ID"),
    product_name: Optional[str] = Query(None, description="Search by product name (partial match)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get all integrated records with optional pagination and date filtering"""

    # Special handling for product_name search - return unique products only
    if product_name and not option_id:
        # Get unique products by using subquery with DISTINCT on option_id
        from sqlalchemy import func

        subquery = db.query(
            IntegratedRecord.option_id,
            IntegratedRecord.product_name,
            IntegratedRecord.option_name,
            func.max(IntegratedRecord.date).label('latest_date'),
            func.sum(IntegratedRecord.sales_quantity).label('total_sales_quantity')
        ).filter(
            IntegratedRecord.tenant_id == current_tenant.id,
            IntegratedRecord.product_name.ilike(f"%{product_name}%")
        ).group_by(
            IntegratedRecord.option_id,
            IntegratedRecord.product_name,
            IntegratedRecord.option_name
        ).order_by(func.sum(IntegratedRecord.sales_quantity).desc())

        # Apply pagination to subquery
        if limit:
            subquery = subquery.offset(offset).limit(limit)

        results = subquery.all()

        return {
            "records": [
                {
                    "id": None,
                    "option_id": row.option_id,
                    "option_name": row.option_name,
                    "product_name": row.product_name,
                    "date": row.latest_date.isoformat() if row.latest_date else None,
                    "sales_amount": None,
                    "sales_quantity": None,
                    "ad_cost": None,
                    "net_profit": None,
                    "actual_margin_rate": None,
                    "roas": None
                }
                for row in results
            ],
            "count": len(results),
            "total": len(results)
        }

    # Normal query for other cases
    query = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id)

    # Apply option_id filtering
    if option_id:
        query = query.filter(IntegratedRecord.option_id == option_id)

    # Apply product_name filtering (partial match)
    if product_name:
        query = query.filter(IntegratedRecord.product_name.ilike(f"%{product_name}%"))

    # Apply date filtering
    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)

    # Order by date descending
    query = query.order_by(IntegratedRecord.date.desc())

    # Get total count before pagination
    total_count = query.count()

    # Apply pagination
    if limit:
        query = query.offset(offset).limit(limit)

    records = query.all()

    return {
        "records": [
            {
                "id": record.id,
                "option_id": record.option_id,
                "option_name": record.option_name,
                "product_name": record.product_name,
                "date": record.date.isoformat() if record.date else None,
                "sales_amount": record.sales_amount,
                "sales_quantity": record.sales_quantity,
                "ad_cost": record.ad_cost,
                "net_profit": record.net_profit,
                "actual_margin_rate": record.actual_margin_rate,
                "roas": record.roas
            }
            for record in records
        ],
        "count": len(records),
        "total": total_count
    }


@router.delete("/data/records/{record_id}")
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Delete a specific integrated record"""
    record = db.query(IntegratedRecord).filter(
        IntegratedRecord.id == record_id,
        IntegratedRecord.tenant_id == current_tenant.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()

    return {"message": "Record deleted successfully"}


@router.delete("/data/records")
async def delete_all_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Delete all integrated records"""
    deleted_count = db.query(IntegratedRecord).filter(
        IntegratedRecord.tenant_id == current_tenant.id
    ).delete()
    db.commit()

    return {
        "message": f"Successfully deleted {deleted_count} records",
        "deleted_count": deleted_count
    }


@router.post("/data/records/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_records(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Delete multiple integrated records by IDs"""
    if not request.ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    # Delete records with the given IDs for this tenant
    deleted_count = db.query(IntegratedRecord).filter(
        IntegratedRecord.id.in_(request.ids),
        IntegratedRecord.tenant_id == current_tenant.id
    ).delete(synchronize_session=False)

    db.commit()

    return BatchDeleteResponse(
        message=f"성공적으로 {deleted_count}개의 레코드를 삭제했습니다",
        deleted_count=deleted_count
    )


@router.get("/data/export")
async def export_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("xlsx", regex="^(xlsx|csv)$"),
    group_by: str = Query("option", regex="^(option|product)$"),
    date_grouping: str = Query("daily", regex="^(daily|total)$"),
    include_basic: bool = Query(True),
    include_sales: bool = Query(True),
    include_ads: bool = Query(True),
    include_margin: bool = Query(True),
    include_calculated: bool = Query(True),
    include_fake_purchase_adjustment: bool = Query(False, description="가구매 조정 포함 여부"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Export integrated data to Excel or CSV

    Parameters:
    - start_date: Filter records from this date
    - end_date: Filter records to this date
    - format: 'xlsx' or 'csv'
    - group_by: 'option' (default) or 'product' - how to group the data
    - date_grouping: 'daily' (default) or 'total' - show daily breakdown or total sum
    - include_basic: Include basic fields (option_id, product_name, date)
    - include_sales: Include sales data
    - include_ads: Include advertising data
    - include_margin: Include margin data
    - include_calculated: Include calculated fields
    """
    # Query records for this tenant
    query = db.query(IntegratedRecord).filter(IntegratedRecord.tenant_id == current_tenant.id)

    if start_date:
        query = query.filter(IntegratedRecord.date >= start_date)
    if end_date:
        query = query.filter(IntegratedRecord.date <= end_date)

    records = query.all()

    if not records:
        raise HTTPException(status_code=404, detail="No records found")

    # Build fake purchase adjustments dictionary
    fake_purchase_adjustments = {}

    if include_fake_purchase_adjustment:
        fake_query = db.query(FakePurchase).filter(FakePurchase.tenant_id == current_tenant.id)

        if start_date:
            fake_query = fake_query.filter(FakePurchase.date >= start_date)
        if end_date:
            fake_query = fake_query.filter(FakePurchase.date <= end_date)

        fake_purchases = fake_query.all()

        for fp in fake_purchases:
            key = (fp.date, fp.option_id)
            sales_deduction = (fp.quantity or 0) * (fp.unit_price or 0)

            fake_purchase_adjustments[key] = {
                'sales_deduction': sales_deduction,
                'quantity_deduction': fp.quantity or 0,
                'ad_cost_addition': fp.total_cost or 0
            }

    # Build DataFrame
    data = []
    for record in records:
        # Apply fake purchase adjustments
        adjustment_key = (record.date, record.option_id)
        adjustment = fake_purchase_adjustments.get(adjustment_key, {})

        sales_deduction = adjustment.get('sales_deduction', 0)
        quantity_deduction = adjustment.get('quantity_deduction', 0)
        ad_cost_addition = adjustment.get('ad_cost_addition', 0)

        # Calculate adjusted values
        adjusted_sales = record.sales_amount - sales_deduction
        adjusted_quantity = record.sales_quantity - quantity_deduction
        adjusted_ad_cost = record.ad_cost + ad_cost_addition

        # Recalculate metrics with adjusted values
        # Unit cost per item
        unit_cost = (record.cost_price or 0) + (record.fee_amount or 0) + (record.vat or 0)
        adjusted_total_cost = unit_cost * adjusted_quantity
        adjusted_net_profit = adjusted_sales - adjusted_total_cost - adjusted_ad_cost * 1.1

        # Actual margin rate (%)
        adjusted_actual_margin_rate = 0
        if adjusted_sales > 0:
            adjusted_actual_margin_rate = (adjusted_net_profit / adjusted_sales) * 100

        # Cost rate (%)
        adjusted_cost_rate = 0
        if adjusted_sales > 0:
            adjusted_cost_rate = ((adjusted_sales - adjusted_total_cost) / adjusted_sales) * 100

        # Ad cost rate (%)
        adjusted_ad_cost_rate = 0
        if adjusted_sales > 0:
            adjusted_ad_cost_rate = (adjusted_ad_cost * 1.1 / adjusted_sales) * 100

        # ROAS
        adjusted_roas = 0
        if adjusted_ad_cost > 0:
            adjusted_roas = (record.conversion_sales / adjusted_ad_cost) * 100

        row = {}

        # Basic fields
        if include_basic:
            row["옵션ID"] = record.option_id
            row["옵션명"] = record.option_name
            row["상품명"] = record.product_name
            row["날짜"] = record.date

        # Sales fields
        if include_sales:
            row["매출액"] = adjusted_sales
            row["판매량"] = adjusted_quantity
            row["주문수"] = record.order_count

        # Ads fields
        if include_ads:
            row["광고비"] = adjusted_ad_cost
            row["노출수"] = record.impressions
            row["클릭수"] = record.clicks
            row["전환매출액"] = record.conversion_sales

        # Margin fields
        if include_margin:
            row["도매가"] = record.cost_price
            row["판매가"] = record.selling_price
            row["수수료율"] = record.fee_rate
            row["총수수료액"] = record.fee_amount * adjusted_quantity  # 총 수수료액 = 단위 수수료액 × 조정된 판매량
            row["총부가세"] = record.vat * adjusted_quantity  # 총 부가세 = 단위 부가세 × 조정된 판매량

        # Calculated fields
        if include_calculated:
            row["총원가"] = adjusted_total_cost
            row["순이익"] = adjusted_net_profit
            row["마진율"] = adjusted_cost_rate
            row["광고비율"] = adjusted_ad_cost_rate
            row["이윤율"] = adjusted_actual_margin_rate
            row["ROAS"] = adjusted_roas

        # Fake purchase fields (only when adjustment is enabled)
        if include_fake_purchase_adjustment:
            row["가구매수량"] = quantity_deduction
            row["가구매비용"] = ad_cost_addition

        data.append(row)

    df = pd.DataFrame(data)

    # Group by date (total) if requested
    if date_grouping == "total":
        # Define aggregation functions for total grouping
        agg_dict = {}

        # Keep first non-null value for basic fields (except date)
        if include_basic:
            if "옵션ID" in df.columns:
                agg_dict["옵션ID"] = 'first'  # Keep first for reference
            if "옵션명" in df.columns:
                agg_dict["옵션명"] = lambda x: ", ".join(x.dropna().unique()) if len(x.dropna()) > 0 else ""
            if "상품명" in df.columns:
                agg_dict["상품명"] = 'first'
            # Remove date from aggregation - we'll add period info instead

        # Sum numeric fields
        numeric_cols = ["매출액", "판매량", "주문수", "광고비", "노출수", "클릭수", "전환매출액", "총원가", "순이익", "총수수료액", "총부가세", "가구매수량", "가구매비용"]
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = 'sum'

        # Average for margin/price fields
        avg_cols = ["도매가", "판매가", "수수료율"]
        for col in avg_cols:
            if col in df.columns:
                agg_dict[col] = 'mean'

        # Group by option_id or product_name (depending on group_by setting)
        if group_by == "option":
            group_cols = ["옵션ID", "상품명"] if "옵션ID" in df.columns and "상품명" in df.columns else ["상품명"] if "상품명" in df.columns else []
        else:
            group_cols = ["상품명"] if "상품명" in df.columns else []

        if group_cols:
            df = df.groupby(group_cols, as_index=False).agg(agg_dict)

            # Recalculate rates after aggregation
            if include_calculated:
                if "매출액" in df.columns and "총원가" in df.columns:
                    df["마진율"] = ((df["매출액"] - df["총원가"]) / df["매출액"] * 100).fillna(0)
                if "매출액" in df.columns and "광고비" in df.columns:
                    df["광고비율"] = (df["광고비"] * 1.1 / df["매출액"] * 100).fillna(0)
                if "매출액" in df.columns and "순이익" in df.columns:
                    df["이윤율"] = (df["순이익"] / df["매출액"] * 100).fillna(0)
                if "전환매출액" in df.columns and "광고비" in df.columns:
                    df["ROAS"] = (df["전환매출액"] / df["광고비"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)

        # Remove date column if exists (since we're showing totals)
        if "날짜" in df.columns:
            df = df.drop(columns=["날짜"])

    # Group by product if requested
    if group_by == "product" and date_grouping != "total":
        # Define aggregation functions for each column
        agg_dict = {}

        # Keep first non-null value for these fields
        if include_basic:
            if "옵션명" in df.columns:
                agg_dict["옵션명"] = lambda x: ", ".join(x.dropna().unique()) if len(x.dropna()) > 0 else ""

        # Sum numeric fields
        numeric_cols = ["매출액", "판매량", "주문수", "광고비", "노출수", "클릭수", "전환매출액", "총원가", "순이익", "총수수료액", "총부가세", "가구매수량", "가구매비용"]
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = 'sum'

        # Average for margin/price fields
        avg_cols = ["도매가", "판매가", "수수료율"]
        for col in avg_cols:
            if col in df.columns:
                agg_dict[col] = 'mean'

        # Group by product name and aggregate
        group_cols = ["상품명"]
        if "날짜" in df.columns:
            group_cols.append("날짜")

        df = df.groupby(group_cols, as_index=False).agg(agg_dict)

        # Recalculate rates after aggregation
        if include_calculated:
            if "매출액" in df.columns and "총원가" in df.columns:
                df["마진율"] = ((df["매출액"] - df["총원가"]) / df["매출액"] * 100).fillna(0)
            if "매출액" in df.columns and "광고비" in df.columns:
                df["광고비율"] = (df["광고비"] * 1.1 / df["매출액"] * 100).fillna(0)
            if "매출액" in df.columns and "순이익" in df.columns:
                df["이윤율"] = (df["순이익"] / df["매출액"] * 100).fillna(0)
            if "전환매출액" in df.columns and "광고비" in df.columns:
                df["ROAS"] = (df["전환매출액"] / df["광고비"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)

        # Remove option_id for product-level grouping
        if "옵션ID" in df.columns:
            df = df.drop(columns=["옵션ID"])

    # Handle case where both product grouping and total date grouping are selected
    elif group_by == "product" and date_grouping == "total":
        # First group by product_name (ignore dates and options)
        agg_dict = {}

        # Keep first non-null value for basic fields
        if include_basic:
            if "옵션명" in df.columns:
                agg_dict["옵션명"] = lambda x: ", ".join(x.dropna().unique()) if len(x.dropna()) > 0 else ""

        # Sum numeric fields
        numeric_cols = ["매출액", "판매량", "주문수", "광고비", "노출수", "클릭수", "전환매출액", "총원가", "순이익", "총수수료액", "총부가세", "가구매수량", "가구매비용"]
        for col in numeric_cols:
            if col in df.columns:
                agg_dict[col] = 'sum'

        # Average for margin/price fields
        avg_cols = ["도매가", "판매가", "수수료율"]
        for col in avg_cols:
            if col in df.columns:
                agg_dict[col] = 'mean'

        # Group by product name only
        group_cols = ["상품명"] if "상품명" in df.columns else []

        if group_cols:
            df = df.groupby(group_cols, as_index=False).agg(agg_dict)

            # Recalculate rates after aggregation
            if include_calculated:
                if "매출액" in df.columns and "총원가" in df.columns:
                    df["마진율"] = ((df["매출액"] - df["총원가"]) / df["매출액"] * 100).fillna(0)
                if "매출액" in df.columns and "광고비" in df.columns:
                    df["광고비율"] = (df["광고비"] * 1.1 / df["매출액"] * 100).fillna(0)
                if "매출액" in df.columns and "순이익" in df.columns:
                    df["이윤율"] = (df["순이익"] / df["매출액"] * 100).fillna(0)
                if "전환매출액" in df.columns and "광고비" in df.columns:
                    df["ROAS"] = (df["전환매출액"] / df["광고비"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)

        # Remove option_id and date columns
        if "옵션ID" in df.columns:
            df = df.drop(columns=["옵션ID"])
        if "날짜" in df.columns:
            df = df.drop(columns=["날짜"])

    # Reorder columns to maintain consistent order
    # Define the desired column order
    desired_order = []

    # Basic fields (in order)
    if "옵션ID" in df.columns:
        desired_order.append("옵션ID")
    if "옵션명" in df.columns:
        desired_order.append("옵션명")
    if "상품명" in df.columns:
        desired_order.append("상품명")
    if "날짜" in df.columns:
        desired_order.append("날짜")

    # Sales fields
    sales_fields = ["매출액", "판매량", "주문수"]
    for field in sales_fields:
        if field in df.columns:
            desired_order.append(field)

    # Ads fields
    ads_fields = ["광고비", "노출수", "클릭수", "전환매출액"]
    for field in ads_fields:
        if field in df.columns:
            desired_order.append(field)

    # Margin fields
    margin_fields = ["도매가", "판매가", "수수료율", "총수수료액", "총부가세"]
    for field in margin_fields:
        if field in df.columns:
            desired_order.append(field)

    # Calculated fields
    calculated_fields = ["총원가", "순이익", "마진율", "광고비율", "이윤율", "ROAS"]
    for field in calculated_fields:
        if field in df.columns:
            desired_order.append(field)

    # Fake purchase fields
    fake_purchase_fields = ["가구매수량", "가구매비용"]
    for field in fake_purchase_fields:
        if field in df.columns:
            desired_order.append(field)

    # Reorder DataFrame columns
    df = df[desired_order]

    # Create file in memory
    output = io.BytesIO()

    if format == "xlsx":
        # Excel format
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='통합데이터')

            # Apply percentage format to specific columns
            workbook = writer.book
            worksheet = writer.sheets['통합데이터']

            # Find percentage columns and apply format
            # 모든 율 필드는 이미 100 곱해진 값으로 저장되어 있음 (예: 14.5)
            # '0.0"%"' 포맷 사용 (% 기호만 추가, 100 곱하지 않음)
            percent_columns_decimal = []  # 소수로 저장된 비율 없음
            percent_columns_number = ['수수료율', '마진율', '광고비율', '이윤율', 'ROAS']  # 14.5 -> 14.5%

            for col_idx, col_name in enumerate(df.columns, start=1):
                if col_name in percent_columns_decimal:
                    # Apply percentage format (auto multiply by 100)
                    for row_idx in range(2, len(df) + 2):
                        cell = worksheet.cell(row=row_idx, column=col_idx)
                        cell.number_format = '0.0%'
                elif col_name in percent_columns_number:
                    # Apply percentage format (just add % symbol)
                    for row_idx in range(2, len(df) + 2):
                        cell = worksheet.cell(row=row_idx, column=col_idx)
                        cell.number_format = '0.0"%"'

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=coupang_data.xlsx"
            }
        )
    else:
        # CSV format
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=coupang_data.csv"
            }
        )
