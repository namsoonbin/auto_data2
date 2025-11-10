# -*- coding: utf-8 -*-
"""
Reset database and recreate with proper multi-tenancy constraints
"""
import sqlite3
import os

# Database path - same as in services/database.py
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)
DB_PATH = os.path.join(data_dir, 'coupang_integrated.db')

def reset_database():
    print(f"Resetting database at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Step 1: Dropping integrated_records table...")
        cursor.execute("DROP TABLE IF EXISTS integrated_records")

        print("Step 2: Creating integrated_records table with correct constraints...")
        cursor.execute("""
            CREATE TABLE integrated_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id CHAR(32),
                option_id BIGINT NOT NULL,
                option_name VARCHAR,
                product_name VARCHAR NOT NULL,
                date DATE,
                sales_amount FLOAT DEFAULT 0.0,
                sales_quantity INTEGER DEFAULT 0,
                order_count INTEGER DEFAULT 0,
                total_sales FLOAT DEFAULT 0.0,
                total_sales_quantity INTEGER DEFAULT 0,
                ad_cost FLOAT DEFAULT 0.0,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                ad_sales_quantity INTEGER DEFAULT 0,
                conversion_sales FLOAT DEFAULT 0.0,
                cost_price FLOAT DEFAULT 0.0,
                selling_price FLOAT DEFAULT 0.0,
                margin_amount FLOAT DEFAULT 0.0,
                margin_rate FLOAT DEFAULT 0.0,
                fee_rate FLOAT DEFAULT 0.0,
                fee_amount FLOAT DEFAULT 0.0,
                vat FLOAT DEFAULT 0.0,
                total_cost FLOAT DEFAULT 0.0,
                net_profit FLOAT DEFAULT 0.0,
                actual_margin_rate FLOAT DEFAULT 0.0,
                cost_rate FLOAT DEFAULT 0.0,
                ad_cost_rate FLOAT DEFAULT 0.0,
                roas FLOAT DEFAULT 0.0,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(tenant_id) REFERENCES tenants(id),
                UNIQUE(tenant_id, option_id, date)
            )
        """)

        print("Step 3: Creating indexes...")
        cursor.execute("CREATE INDEX idx_tenant_option_date ON integrated_records(tenant_id, option_id, date)")
        cursor.execute("CREATE INDEX ix_integrated_records_tenant_id ON integrated_records(tenant_id)")
        cursor.execute("CREATE INDEX ix_integrated_records_option_id ON integrated_records(option_id)")
        cursor.execute("CREATE INDEX ix_integrated_records_product_name ON integrated_records(product_name)")
        cursor.execute("CREATE INDEX ix_integrated_records_date ON integrated_records(date)")

        conn.commit()
        print("\n[SUCCESS] Database reset successfully!")
        print("integrated_records table recreated with proper multi-tenancy constraints.")
        print("You can now upload new data.")

    except Exception as e:
        print(f"\n[ERROR] Failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    reset_database()
