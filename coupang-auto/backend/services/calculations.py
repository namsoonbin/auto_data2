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
