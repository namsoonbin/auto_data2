# -*- coding: utf-8 -*-
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session

from services.database import get_session, SalesRecord, AdRecord, ProductMaster


# Parse Sales Excel File
async def parse_sales_file(upload_file) -> List[Dict]:
    """
    Parse sales Excel file and save to database
    Expected columns: date, store, product_name, quantity, sale_price, cost_price, shipping_cost
    """
    content = await upload_file.read()
    excel_data = BytesIO(content)

    try:
        df = pd.read_excel(excel_data)
        df.columns = df.columns.str.strip()

        # Column mapping (Korean and English)
        column_mapping = {
            '날짜': 'date', '일자': 'date', 'date': 'date',
            '스토어': 'store', '상점': 'store', 'store': 'store',
            '상품명': 'product_name', '제품명': 'product_name', 'product_name': 'product_name',
            '판매수량': 'quantity', '수량': 'quantity', 'quantity': 'quantity',
            '판매가': 'sale_price', '가격': 'sale_price', 'price': 'sale_price', 'sale_price': 'sale_price',
            '원가': 'cost_price', '원가격': 'cost_price', 'cost': 'cost_price', 'cost_price': 'cost_price',
            '배송비': 'shipping_cost', '택배비': 'shipping_cost', 'shipping': 'shipping_cost', 'shipping_cost': 'shipping_cost',
        }

        df.rename(columns=column_mapping, inplace=True)

        # Convert date format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Handle numeric columns
        numeric_columns = ['quantity', 'sale_price', 'cost_price', 'shipping_cost']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Handle string columns
        string_columns = ['store', 'product_name']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)

        records = df.to_dict(orient='records')

        # Save to database
        db = get_session()
        try:
            saved_count = 0
            for record in records:
                # Check required fields
                if not record.get('date') or pd.isna(record.get('date')):
                    continue
                if not record.get('product_name'):
                    continue

                sales_record = SalesRecord(
                    date=record.get('date'),
                    store=record.get('store', ''),
                    product_name=record.get('product_name', ''),
                    quantity=int(record.get('quantity', 0)),
                    sale_price=float(record.get('sale_price', 0.0)),
                    cost_price=float(record.get('cost_price', 0.0)),
                    shipping_cost=float(record.get('shipping_cost', 0.0))
                )

                db.add(sales_record)
                saved_count += 1

            db.commit()
            print(f"Saved {saved_count} sales records")

        finally:
            db.close()

        upload_file.file.close()
        return records

    except Exception as e:
        print(f"Sales parsing error: {str(e)}")
        raise


# Parse Ads Excel File
async def parse_ads_file(upload_file) -> List[Dict]:
    """
    Parse advertising Excel file and save to database
    Expected columns: date, store, product_name, impressions, clicks, conversions, ad_cost
    """
    content = await upload_file.read()
    excel_data = BytesIO(content)

    try:
        df = pd.read_excel(excel_data)
        df.columns = df.columns.str.strip()

        # Column mapping
        column_mapping = {
            '날짜': 'date', '일자': 'date', 'date': 'date',
            '스토어': 'store', 'store': 'store',
            '상품명': 'product_name', 'product_name': 'product_name',
            '노출수': 'impressions', 'impressions': 'impressions',
            '클릭수': 'clicks', 'clicks': 'clicks',
            '전환수': 'conversions', '광고전환수': 'conversions', 'conversions': 'conversions',
            '광고비': 'ad_cost', '광고비용': 'ad_cost', 'ad_cost': 'ad_cost',
            '총 전환 매출액 (1일)(원)': 'conversion_sales', '전환매출액': 'conversion_sales', 'conversion_sales': 'conversion_sales',
        }

        df.rename(columns=column_mapping, inplace=True)

        # Convert date format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Handle numeric columns
        numeric_columns = ['impressions', 'clicks', 'conversions', 'ad_cost', 'conversion_sales']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Handle string columns
        string_columns = ['store', 'product_name']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)

        records = df.to_dict(orient='records')

        # Save to database
        db = get_session()
        try:
            saved_count = 0
            for record in records:
                # Check required fields
                if not record.get('date') or pd.isna(record.get('date')):
                    continue
                if not record.get('product_name'):
                    continue

                ad_record = AdRecord(
                    date=record.get('date'),
                    store=record.get('store', ''),
                    product_name=record.get('product_name', ''),
                    impressions=int(record.get('impressions', 0)),
                    clicks=int(record.get('clicks', 0)),
                    conversions=int(record.get('conversions', 0)),
                    ad_cost=float(record.get('ad_cost', 0.0)),
                    conversion_sales=float(record.get('conversion_sales', 0.0))
                )

                db.add(ad_record)
                saved_count += 1

            db.commit()
            print(f"Saved {saved_count} ad records")

        finally:
            db.close()

        upload_file.file.close()
        return records

    except Exception as e:
        print(f"Ad parsing error: {str(e)}")
        raise


# Parse Product Master Excel File
async def parse_product_master_file(upload_file) -> List[Dict]:
    """
    Parse product master data and save to database (with upsert)
    Expected columns: product_code, product_name, cost_price, commission_rate, exchange_rate
    """
    content = await upload_file.read()
    excel_data = BytesIO(content)

    try:
        df = pd.read_excel(excel_data)
        df.columns = df.columns.str.strip()

        # Column mapping
        column_mapping = {
            '상품코드': 'product_code', 'product_code': 'product_code',
            '상품명': 'product_name', 'product_name': 'product_name',
            '원가': 'cost_price', 'cost_price': 'cost_price',
            '수수료율': 'commission_rate', 'commission_rate': 'commission_rate',
            '환율': 'exchange_rate', 'exchange_rate': 'exchange_rate',
        }

        df.rename(columns=column_mapping, inplace=True)

        # Handle numeric columns
        numeric_columns = ['cost_price', 'commission_rate', 'exchange_rate']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        records = df.to_dict(orient='records')

        # Save to database (upsert)
        db = get_session()
        try:
            saved_count = 0
            for record in records:
                if not record.get('product_code'):
                    continue

                # Check if record exists (upsert logic)
                existing = db.query(ProductMaster).filter(
                    ProductMaster.product_code == record['product_code']
                ).first()

                if existing:
                    # Update existing record
                    for key, value in record.items():
                        if hasattr(existing, key) and key != 'id':
                            setattr(existing, key, value)
                else:
                    # Create new record
                    product = ProductMaster(
                        product_code=record.get('product_code'),
                        product_name=record.get('product_name', ''),
                        cost_price=float(record.get('cost_price', 0.0)),
                        commission_rate=float(record.get('commission_rate', 0.10)) if record.get('commission_rate') else None,
                        exchange_rate=float(record.get('exchange_rate', 1.0)) if record.get('exchange_rate') else None
                    )
                    db.add(product)

                saved_count += 1

            db.commit()
            print(f"Saved {saved_count} product master records")

        finally:
            db.close()

        upload_file.file.close()
        return records

    except Exception as e:
        print(f"Product master parsing error: {str(e)}")
        raise
