from services.database import get_session, IntegratedRecord

session = get_session()

# Check specific option ID
option_id = 92582844462
record = session.query(IntegratedRecord).filter(IntegratedRecord.option_id == option_id).first()

print(f"=== Checking Option ID: {option_id} ===")
print(f"Found in DB: {record is not None}")

if record:
    print(f"\nProduct: {record.product_name}")
    print(f"Option Name: {record.option_name}")
    print(f"Sales Amount: {record.sales_amount:,.0f}원")
    print(f"Sales Quantity: {record.sales_quantity}개")
    print(f"Ad Cost: {record.ad_cost:,.0f}원")
    print(f"Impressions: {record.impressions}")
    print(f"Clicks: {record.clicks}")
    print(f"\n=== Analysis ===")
    if record.ad_cost == 0:
        print("❌ 광고비가 0원입니다 - 광고 파일에서 매칭 실패")
        print("\n가능한 원인:")
        print("1. 광고 파일에 이 옵션ID가 없음")
        print("2. 광고 파일의 옵션ID 컬럼명이 다름 ('광고 집행 옵션 ID')")
        print("3. 광고 파일에서 옵션ID 값이 숫자가 아닌 문자로 되어있음")
    else:
        print(f"✅ 광고비가 정상적으로 매칭됨: {record.ad_cost:,.0f}원")
else:
    print("❌ 데이터베이스에서 레코드를 찾을 수 없습니다")
    print("\n판매 파일에 이 옵션ID가 있는지 확인해주세요")

session.close()
