# -*- coding: utf-8 -*-
from typing import Dict, Optional


# Coupang Fee Constants
PAYMENT_FEE_RATE = 0.029  # 2.9%
VAT_RATE = 0.10  # 10%
DEFAULT_COMMISSION_RATE = 0.10  # 10%
MONTHLY_FEE = 55000  # Monthly platform fee (KRW)


# Main Calculation Function
def calculate_fees_and_profit(
    sale_price: float,
    quantity: int = 1,
    cost_price: float = 0.0,
    ad_cost: float = 0.0,
    shipping_cost: float = 0.0,
    commission_rate: Optional[float] = None,
    include_monthly_fee: bool = False
) -> Dict[str, float]:
    """
    Calculate fees and profit for a single sale record

    Returns dict with: commission, payment_fee, vat, total_fee,
                      total_cost, profit, margin_rate
    """
    if commission_rate is None:
        commission_rate = DEFAULT_COMMISSION_RATE

    total_sales = sale_price * quantity

    # 1. Sales commission
    commission = total_sales * commission_rate

    # 2. Payment fee (2.9%)
    payment_fee = total_sales * PAYMENT_FEE_RATE

    # 3. VAT (10% on fees)
    vat = (commission + payment_fee) * VAT_RATE

    # 4. Total platform fee
    total_fee = commission + payment_fee + vat

    # 5. Monthly fee (optional)
    monthly_fee = MONTHLY_FEE if include_monthly_fee else 0.0

    # 6. Total cost price
    total_cost_price = cost_price * quantity

    # 7. Total cost (cost + fees + ad + shipping + monthly)
    total_cost = total_cost_price + total_fee + ad_cost + shipping_cost + monthly_fee

    # 8. Net profit
    profit = total_sales - total_cost

    # 9. Margin rate (%)
    margin_rate = (profit / total_sales * 100) if total_sales > 0 else 0

    return {
        'commission': round(commission, 2),
        'payment_fee': round(payment_fee, 2),
        'vat': round(vat, 2),
        'total_fee': round(total_fee, 2),
        'ad_cost': round(ad_cost, 2),
        'shipping_cost': round(shipping_cost, 2),
        'total_cost': round(total_cost, 2),
        'profit': round(profit, 2),
        'margin_rate': round(margin_rate, 2)
    }


# Category-specific Commission Rates
CATEGORY_COMMISSION_RATES = {
    'Fashion Clothing': 0.15,
    'Fashion Accessories': 0.15,
    'Beauty': 0.12,
    'Food': 0.08,
    'Electronics': 0.10,
    'Furniture': 0.12,
    'Digital': 0.10,
    'Sports': 0.12,
    'Baby': 0.13,
    'Pet': 0.12,
    'Books': 0.08,
    'Other': 0.10,
}


def get_commission_rate_by_category(category: str) -> float:
    """Get commission rate by category name"""
    return CATEGORY_COMMISSION_RATES.get(category, DEFAULT_COMMISSION_RATE)


# Ad Efficiency Metrics
def calculate_ad_metrics(
    ad_cost: float,
    conversions: int,
    total_sales: float,
    clicks: int = 0,
    impressions: int = 0
) -> Dict[str, float]:
    """
    Calculate advertising efficiency metrics

    Returns: roas, cpc, ctr, cvr, cpa
    """
    # ROAS (Return On Ad Spend)
    roas = (total_sales / ad_cost) if ad_cost > 0 else 0

    # CPC (Cost Per Click)
    cpc = (ad_cost / clicks) if clicks > 0 else 0

    # CTR (Click Through Rate)
    ctr = (clicks / impressions * 100) if impressions > 0 else 0

    # CVR (Conversion Rate)
    cvr = (conversions / clicks * 100) if clicks > 0 else 0

    # CPA (Cost Per Acquisition)
    cpa = (ad_cost / conversions) if conversions > 0 else 0

    return {
        'roas': round(roas, 2),
        'cpc': round(cpc, 2),
        'ctr': round(ctr, 2),
        'cvr': round(cvr, 2),
        'cpa': round(cpa, 2)
    }


# Period Summary Calculation
def calculate_period_summary(
    sales_records: list,
    ad_records: list = None
) -> Dict:
    """Calculate summary metrics for a period"""
    if not sales_records:
        return {
            'total_sales': 0,
            'total_quantity': 0,
            'total_profit': 0,
            'total_ad_cost': 0,
            'avg_margin_rate': 0,
            'product_count': 0
        }

    total_sales = 0
    total_quantity = 0
    total_cost = 0
    total_ad_cost = 0

    # Aggregate sales
    for record in sales_records:
        quantity = record.get('quantity', 0)
        sale_price = record.get('sale_price', 0)
        cost_price = record.get('cost_price', 0)
        shipping_cost = record.get('shipping_cost', 0)

        total_sales += sale_price * quantity
        total_quantity += quantity

        calc_result = calculate_fees_and_profit(
            sale_price=sale_price,
            quantity=quantity,
            cost_price=cost_price,
            shipping_cost=shipping_cost
        )

        total_cost += calc_result['total_cost']

    # Aggregate ad costs
    if ad_records:
        for record in ad_records:
            total_ad_cost += record.get('ad_cost', 0)

    # Calculate profit and margin
    total_profit = total_sales - total_cost - total_ad_cost
    avg_margin_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0

    # Count unique products
    product_count = len(set(r.get('product_name') for r in sales_records))

    return {
        'total_sales': round(total_sales, 2),
        'total_quantity': total_quantity,
        'total_profit': round(total_profit, 2),
        'total_ad_cost': round(total_ad_cost, 2),
        'avg_margin_rate': round(avg_margin_rate, 2),
        'product_count': product_count
    }


# Weekly Grouping
def group_by_week(records: list, date_field: str = 'date') -> Dict:
    """Group records by week (ISO week)"""
    from collections import defaultdict
    import datetime

    weekly_groups = defaultdict(list)

    for record in records:
        date = record.get(date_field)
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

        iso_year, iso_week, _ = date.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        weekly_groups[week_key].append(record)

    return dict(weekly_groups)
