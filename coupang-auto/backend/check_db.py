# -*- coding: utf-8 -*-
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "coupang_integrated.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check margin data
cursor.execute('''
    SELECT option_id, product_name, cost_price, selling_price, margin_amount,
           fee_amount, vat, sales_amount, total_cost, net_profit
    FROM integrated_records
    WHERE cost_price > 0
    LIMIT 5
''')

print("=" * 120)
print("마진 데이터가 있는 레코드 샘플 (5개):")
print("=" * 120)
print(f"{'옵션ID':<15} {'도매가':>10} {'판매가':>10} {'마진':>10} {'수수료':>10} {'부가세':>10} {'매출':>12} {'총원가':>12} {'순이익':>12}")
print("-" * 120)

for row in cursor.fetchall():
    option_id, product_name, cost_price, selling_price, margin_amount, fee_amount, vat, sales_amount, total_cost, net_profit = row
    print(f"{option_id:<15} {cost_price:>10,.0f} {selling_price:>10,.0f} {margin_amount:>10,.0f} {fee_amount:>10,.0f} {vat:>10,.0f} {sales_amount:>12,.0f} {total_cost:>12,.0f} {net_profit:>12,.0f}")

# Summary
cursor.execute('''
    SELECT
        COUNT(*) as total_records,
        COUNT(CASE WHEN cost_price > 0 THEN 1 END) as with_margin,
        COUNT(CASE WHEN ad_cost > 0 THEN 1 END) as with_ads,
        COUNT(CASE WHEN cost_price > 0 AND ad_cost > 0 THEN 1 END) as fully_integrated
    FROM integrated_records
''')

total, with_margin, with_ads, fully_integrated = cursor.fetchone()
print("\n" + "=" * 120)
print("데이터 통합 현황:")
print("=" * 120)
print(f"총 레코드 수: {total}")
print(f"마진 데이터 있음: {with_margin} ({with_margin/total*100:.1f}%)")
print(f"광고 데이터 있음: {with_ads} ({with_ads/total*100:.1f}%)")
print(f"완전 통합 (마진+광고): {fully_integrated} ({fully_integrated/total*100:.1f}%)")
print("=" * 120)

conn.close()
