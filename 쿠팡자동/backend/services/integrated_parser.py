# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
from typing import BinaryIO, Tuple, List
from sqlalchemy.orm import Session
from uuid import UUID

from services.database import IntegratedRecord, ProductMargin


def get_margin_data_from_db(db: Session, tenant_id: UUID) -> pd.DataFrame:
    """
    ProductMargin 테이블에서 해당 tenant의 마진 데이터를 DataFrame으로 변환

    Args:
        db: Database session
        tenant_id: Tenant UUID

    Returns:
        DataFrame with columns: option_id, cost_price, selling_price,
                                margin_amount, margin_rate, fee_rate,
                                fee_amount, vat
    """
    # Query margin records for this tenant
    margins = db.query(ProductMargin).filter(ProductMargin.tenant_id == tenant_id).all()

    if not margins:
        # Return empty DataFrame with proper columns
        print("WARNING: No margin data found in database. Continuing without margin data.")
        return pd.DataFrame(columns=[
            'option_id', 'cost_price', 'selling_price', 'margin_amount',
            'margin_rate', 'fee_rate', 'fee_amount', 'vat'
        ])

    # Convert to DataFrame
    margin_data = []
    for m in margins:
        margin_data.append({
            'option_id': m.option_id,
            'cost_price': m.cost_price,
            'selling_price': m.selling_price,
            'margin_amount': m.margin_amount,
            'margin_rate': m.margin_rate,
            'fee_rate': m.fee_rate,
            'fee_amount': m.fee_amount,
            'vat': m.vat
        })

    df = pd.DataFrame(margin_data)
    df['option_id'] = df['option_id'].astype('int64')

    print(f"Loaded {len(df)} margin records from database")
    return df


async def parse_integrated_files(
    sales_file: BinaryIO,
    ads_file: BinaryIO,
    db: Session,
    tenant_id: UUID,
    data_date: datetime.date = None
) -> Tuple[int, int, int, List[str]]:
    """
    Parse and integrate 2 Excel files (sales, ads) with margin data from database

    Args:
        sales_file: Sales Excel file
        ads_file: Ads Excel file
        db: Database session
        tenant_id: Tenant UUID object
        data_date: Data date (optional)

    Returns:
        (total_records, matched_with_ads, matched_with_margin, warnings)
    """
    warnings = []

    # 1. Parse Sales Data
    try:
        sales_df = pd.read_excel(sales_file)
        # Column mapping for sales file
        sales_columns = {
            '옵션 ID': 'option_id',
            '옵션명': 'option_name',
            '상품명': 'product_name',
            '매출(원)': 'sales_amount',
            '판매량': 'sales_quantity',
            '주문': 'order_count',
            '총 매출(원)': 'total_sales',
            '총 판매수': 'total_sales_quantity'
        }

        # Check if columns exist
        missing_cols = [col for col in sales_columns.keys() if col not in sales_df.columns]
        if missing_cols:
            raise ValueError(f"Sales file missing columns: {missing_cols}")

        sales_df = sales_df[list(sales_columns.keys())].rename(columns=sales_columns)

        # Convert option_id to int64
        sales_df['option_id'] = pd.to_numeric(sales_df['option_id'], errors='coerce')
        sales_df = sales_df.dropna(subset=['option_id'])
        sales_df['option_id'] = sales_df['option_id'].astype('int64')

        print(f"Parsed {len(sales_df)} sales records")

    except Exception as e:
        raise ValueError(f"Failed to parse sales file: {str(e)}")

    # 2. Parse Ads Data
    try:
        ads_df = pd.read_excel(ads_file)
        # Column mapping for ads file
        ads_columns = {
            '광고 집행 옵션 ID': 'option_id',
            '광고비(원)': 'ad_cost',
            '노출수': 'impressions',
            '클릭수': 'clicks',
            '총 판매 수량 (1일)': 'ad_sales_quantity',
            '총 전환 매출액 (1일)(원)': 'conversion_sales'
        }

        # Check if columns exist
        missing_cols = [col for col in ads_columns.keys() if col not in ads_df.columns]
        if missing_cols:
            warnings.append(f"Ads file missing columns: {missing_cols}. Using empty ad data.")
            ads_df = pd.DataFrame(columns=['option_id', 'ad_cost', 'impressions', 'clicks', 'ad_sales_quantity', 'conversion_sales'])
        else:
            ads_df = ads_df[list(ads_columns.keys())].rename(columns=ads_columns)

            # Convert option_id to int64
            ads_df['option_id'] = pd.to_numeric(ads_df['option_id'], errors='coerce')
            ads_df = ads_df.dropna(subset=['option_id'])
            ads_df['option_id'] = ads_df['option_id'].astype('int64')

            # Group by option_id and sum all numeric columns
            # This handles cases where same option_id appears multiple times (different campaigns/periods)
            print(f"Parsed {len(ads_df)} ad records (before grouping)")
            ads_df = ads_df.groupby('option_id', as_index=False).agg({
                'ad_cost': 'sum',
                'impressions': 'sum',
                'clicks': 'sum',
                'ad_sales_quantity': 'sum',
                'conversion_sales': 'sum'
            })

        print(f"Parsed {len(ads_df)} unique ad records (after grouping by option_id)")

        # DEBUG: Show sample ad data
        if len(ads_df) > 0:
            print("\n=== AD DATA SAMPLE (first 3 rows) ===")
            print(ads_df.head(3).to_string())
            print(f"\nAd data columns: {ads_df.columns.tolist()}")
            print(f"Ad cost stats: min={ads_df['ad_cost'].min()}, max={ads_df['ad_cost'].max()}, mean={ads_df['ad_cost'].mean()}")

    except Exception as e:
        warnings.append(f"Failed to parse ads file: {str(e)}. Continuing without ad data.")
        ads_df = pd.DataFrame(columns=['option_id', 'ad_cost', 'impressions', 'clicks', 'ad_sales_quantity', 'conversion_sales'])

    # 3. Load Margin Data from Database
    print("\n=== LOADING MARGIN DATA FROM DATABASE ===")
    margin_df = get_margin_data_from_db(db, tenant_id)

    if len(margin_df) == 0:
        warnings.append("No margin data found in database. Please add margin data in the Margin Management page.")

    # 4. Merge Sales + Ads
    merged_df = pd.merge(
        sales_df,
        ads_df,
        on='option_id',
        how='left',
        suffixes=('', '_ad')
    )

    matched_with_ads = merged_df['ad_cost'].notna().sum()
    print(f"Matched {matched_with_ads} records with ad data")

    # DEBUG: Show merged data sample
    print("\n=== MERGED DATA SAMPLE (first 3 rows with ad data) ===")
    ads_merged = merged_df[merged_df['ad_cost'].notna()].head(3)
    if len(ads_merged) > 0:
        print(ads_merged[['option_id', 'product_name', 'sales_amount', 'ad_cost', 'impressions', 'clicks']].to_string())
    else:
        print("No records with ad data found!")
        print("\nAll merged data (first 3):")
        print(merged_df[['option_id', 'product_name', 'sales_amount', 'ad_cost']].head(3).to_string())

    # 5. Merge (Sales + Ads) + Margin
    merged_df = pd.merge(
        merged_df,
        margin_df,
        on='option_id',
        how='left',
        suffixes=('', '_margin')
    )

    matched_with_margin = merged_df['cost_price'].notna().sum()
    print(f"Matched {matched_with_margin} records with margin data")

    # Fill NaN values with 0
    numeric_columns = [
        'sales_amount', 'sales_quantity', 'order_count', 'total_sales', 'total_sales_quantity',
        'ad_cost', 'impressions', 'clicks', 'ad_sales_quantity', 'conversion_sales',
        'cost_price', 'selling_price', 'margin_amount', 'margin_rate', 'fee_rate', 'fee_amount', 'vat'
    ]

    for col in numeric_columns:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(0)

    # Remove duplicates (keep first occurrence)
    merged_df = merged_df.drop_duplicates(subset=['option_id'], keep='first')
    print(f"After removing duplicates: {len(merged_df)} unique records")

    # Filter out records where sales, quantity, and ad_cost are all 0
    # Keep records with meaningful data (including negative values for returns/refunds)
    before_filter = len(merged_df)
    merged_df = merged_df[
        (merged_df['sales_amount'] != 0) |
        (merged_df['sales_quantity'] != 0) |
        (merged_df['ad_cost'] != 0)
    ]
    filtered_count = before_filter - len(merged_df)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} records with all zero values (sales=0, quantity=0, ad_cost=0)")
    print(f"Final records to save: {len(merged_df)} (including negative values for returns)")

    # 6. Save to Database
    saved_count = 0
    skipped_count = 0

    for _, row in merged_df.iterrows():
        try:
            # Convert numeric fields, handle '-' and NaN values
            def safe_int(value, default=0):
                if pd.isna(value) or value == '-' or value == '':
                    return default
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return default

            def safe_float(value, default=0.0):
                if pd.isna(value) or value == '-' or value == '':
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default

            # Check if record already exists for this option_id, date AND tenant
            record_date = data_date or datetime.now().date()
            existing = db.query(IntegratedRecord).filter(
                IntegratedRecord.tenant_id == tenant_id,
                IntegratedRecord.option_id == int(row['option_id']),
                IntegratedRecord.date == record_date
            ).first()

            if existing:
                # Update existing record
                existing.option_name = str(row.get('option_name', ''))
                existing.product_name = str(row.get('product_name', ''))
                existing.date = data_date or datetime.now().date()

                # Sales data
                existing.sales_amount = safe_float(row.get('sales_amount'))
                existing.sales_quantity = safe_int(row.get('sales_quantity'))
                existing.order_count = safe_int(row.get('order_count'))
                existing.total_sales = safe_float(row.get('total_sales'))
                existing.total_sales_quantity = safe_int(row.get('total_sales_quantity'))

                # Ad data
                existing.ad_cost = safe_float(row.get('ad_cost'))
                existing.impressions = safe_int(row.get('impressions'))
                existing.clicks = safe_int(row.get('clicks'))
                existing.ad_sales_quantity = safe_int(row.get('ad_sales_quantity'))
                existing.conversion_sales = safe_float(row.get('conversion_sales'))

                # Margin data
                existing.cost_price = safe_float(row.get('cost_price'))
                existing.selling_price = safe_float(row.get('selling_price'))
                existing.margin_amount = safe_float(row.get('margin_amount'))
                existing.margin_rate = safe_float(row.get('margin_rate'))
                existing.fee_rate = safe_float(row.get('fee_rate'))
                existing.fee_amount = safe_float(row.get('fee_amount'))
                existing.vat = safe_float(row.get('vat'))

                # Calculate metrics
                existing.calculate_metrics()
                existing.updated_at = datetime.now()

            else:
                # Create new record
                record = IntegratedRecord(
                    tenant_id=tenant_id,
                    option_id=int(row['option_id']),
                    option_name=str(row.get('option_name', '')),
                    product_name=str(row.get('product_name', '')),
                    date=data_date or datetime.now().date(),

                    # Sales data
                    sales_amount=safe_float(row.get('sales_amount')),
                    sales_quantity=safe_int(row.get('sales_quantity')),
                    order_count=safe_int(row.get('order_count')),
                    total_sales=safe_float(row.get('total_sales')),
                    total_sales_quantity=safe_int(row.get('total_sales_quantity')),

                    # Ad data
                    ad_cost=safe_float(row.get('ad_cost')),
                    impressions=safe_int(row.get('impressions')),
                    clicks=safe_int(row.get('clicks')),
                    ad_sales_quantity=safe_int(row.get('ad_sales_quantity')),
                    conversion_sales=safe_float(row.get('conversion_sales')),

                    # Margin data
                    cost_price=safe_float(row.get('cost_price')),
                    selling_price=safe_float(row.get('selling_price')),
                    margin_amount=safe_float(row.get('margin_amount')),
                    margin_rate=safe_float(row.get('margin_rate')),
                    fee_rate=safe_float(row.get('fee_rate')),
                    fee_amount=safe_float(row.get('fee_amount')),
                    vat=safe_float(row.get('vat'))
                )

                # Calculate metrics
                record.calculate_metrics()
                db.add(record)

            saved_count += 1

        except Exception as e:
            print(f"Error saving record {row.get('option_id')}: {str(e)}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            skipped_count += 1
            continue

    # Commit all changes
    try:
        db.commit()
        print(f"Successfully saved {saved_count} records to database")
        if skipped_count > 0:
            warnings.append(f"Skipped {skipped_count} records due to errors")
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to commit to database: {str(e)}")

    return (saved_count, matched_with_ads, matched_with_margin, warnings)
