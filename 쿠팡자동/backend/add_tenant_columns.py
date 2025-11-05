"""
수동으로 tenant_id 컬럼을 추가하는 스크립트
"""
import sqlite3
import os

DB_PATH = os.path.join("data", "coupang_integrated.db")

def add_tenant_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # integrated_records에 tenant_id 컬럼 추가
        print("[1/3] integrated_records 테이블에 tenant_id 컬럼 추가...")
        cursor.execute("""
            ALTER TABLE integrated_records
            ADD COLUMN tenant_id VARCHAR(32)
        """)
        print("    [OK]")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("    [SKIP] 이미 존재함")
        else:
            print(f"    [ERROR] {e}")

    try:
        # product_margins에 tenant_id 컬럼 추가
        print("[2/3] product_margins 테이블에 tenant_id 컬럼 추가...")
        cursor.execute("""
            ALTER TABLE product_margins
            ADD COLUMN tenant_id VARCHAR(32)
        """)
        print("    [OK]")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("    [SKIP] 이미 존재함")
        else:
            print(f"    [ERROR] {e}")

    try:
        # upload_history에 tenant_id 컬럼 추가
        print("[3/3] upload_history 테이블에 tenant_id 컬럼 추가...")
        cursor.execute("""
            ALTER TABLE upload_history
            ADD COLUMN tenant_id VARCHAR(32)
        """)
        print("    [OK]")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("    [SKIP] 이미 존재함")
        else:
            print(f"    [ERROR] {e}")

    conn.commit()
    conn.close()

    print("\n[SUCCESS] 컬럼 추가 완료!")
    print("이제 migrate_existing_data.py를 실행하세요.")

if __name__ == "__main__":
    add_tenant_columns()
