"""
기존 데이터를 첫 번째 테넌트에 할당하는 마이그레이션 스크립트
"""
from sqlalchemy import create_engine, text
from services.database import DATABASE_URL

def migrate_existing_data():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # 첫 번째 테넌트 ID 가져오기
        result = conn.execute(text("SELECT id FROM tenants ORDER BY created_at LIMIT 1"))
        tenant_row = result.fetchone()

        if not tenant_row:
            print("[ERROR] 테넌트가 없습니다. 먼저 회원가입을 해주세요.")
            return

        tenant_id = tenant_row[0]
        print(f"[OK] 테넌트 ID: {tenant_id}")

        # integrated_records 업데이트
        result = conn.execute(
            text("UPDATE integrated_records SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
            {"tenant_id": tenant_id}
        )
        updated_records = result.rowcount
        print(f"[OK] integrated_records: {updated_records}개 레코드 업데이트")

        # product_margins 업데이트
        result = conn.execute(
            text("UPDATE product_margins SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
            {"tenant_id": tenant_id}
        )
        updated_margins = result.rowcount
        print(f"[OK] product_margins: {updated_margins}개 레코드 업데이트")

        # upload_history 업데이트
        result = conn.execute(
            text("UPDATE upload_history SET tenant_id = :tenant_id WHERE tenant_id IS NULL"),
            {"tenant_id": tenant_id}
        )
        updated_history = result.rowcount
        print(f"[OK] upload_history: {updated_history}개 레코드 업데이트")

        conn.commit()

        print("\n[SUCCESS] 마이그레이션 완료! 이제 기존 데이터를 볼 수 있습니다.")
        print("브라우저를 새로고침하세요.")

if __name__ == "__main__":
    migrate_existing_data()
