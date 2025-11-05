from services.database import get_session, IntegratedRecord

session = get_session()

# Check specific option ID
option_id = 89048355196
record = session.query(IntegratedRecord).filter(IntegratedRecord.option_id == option_id).first()

print(f"=== Checking Option ID: {option_id} ===")
print(f"Found: {record is not None}")

if record:
    print(f"Product: {record.product_name}")
    print(f"Sales Amount: {record.sales_amount}")
    print(f"Sales Quantity: {record.sales_quantity}")
    print(f"Ad Cost: {record.ad_cost}")
    print(f"Net Profit: {record.net_profit}")
else:
    print("Record NOT found in database!")

    # Check total records
    total = session.query(IntegratedRecord).count()
    print(f"\nTotal records in DB: {total}")

    # Show first 5 records
    if total > 0:
        print("\nFirst 5 records:")
        samples = session.query(IntegratedRecord).limit(5).all()
        for r in samples:
            print(f"  - Option ID: {r.option_id}, Sales: {r.sales_amount}")

session.close()
