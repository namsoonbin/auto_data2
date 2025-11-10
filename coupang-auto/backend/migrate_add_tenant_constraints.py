# -*- coding: utf-8 -*-
"""
Migration script to add tenant_id to unique constraints
"""
import sqlite3
import os

# Database path - same as in services/database.py
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)
DB_PATH = os.path.join(data_dir, 'coupang_integrated.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting migration...")

        # 1. Drop old unique constraint on integrated_records
        print("Step 1: Recreating integrated_records table with new constraints...")

        # Create a temporary table with the new structure
        cursor.execute("""
            CREATE TABLE integrated_records_new (
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

        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO integrated_records_new
            SELECT * FROM integrated_records
        """)

        # Drop old table
        cursor.execute("DROP TABLE integrated_records")

        # Rename new table to original name
        cursor.execute("ALTER TABLE integrated_records_new RENAME TO integrated_records")

        # Create indexes
        cursor.execute("CREATE INDEX idx_tenant_option_date ON integrated_records(tenant_id, option_id, date)")
        cursor.execute("CREATE INDEX ix_integrated_records_tenant_id ON integrated_records(tenant_id)")
        cursor.execute("CREATE INDEX ix_integrated_records_option_id ON integrated_records(option_id)")
        cursor.execute("CREATE INDEX ix_integrated_records_product_name ON integrated_records(product_name)")
        cursor.execute("CREATE INDEX ix_integrated_records_date ON integrated_records(date)")

        print("[OK] integrated_records table migrated successfully")

        # 2. Check and migrate upload_history if needed
        print("\nStep 2: Checking upload_history table...")
        cursor.execute("PRAGMA table_info(upload_history)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'tenant_id' in columns:
            print("[OK] upload_history already has tenant_id column")
        else:
            print("Adding tenant_id column to upload_history...")
            cursor.execute("ALTER TABLE upload_history ADD COLUMN tenant_id CHAR(32)")
            cursor.execute("CREATE INDEX ix_upload_history_tenant_id ON upload_history(tenant_id)")
            print("[OK] upload_history migrated successfully")

        # 3. Check and migrate product_margins if needed
        print("\nStep 3: Checking product_margins table...")
        cursor.execute("PRAGMA table_info(product_margins)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'tenant_id' in columns:
            print("[OK] product_margins already has tenant_id column")
        else:
            print("Adding tenant_id column to product_margins...")
            cursor.execute("ALTER TABLE product_margins ADD COLUMN tenant_id CHAR(32)")
            cursor.execute("CREATE INDEX ix_product_margins_tenant_id ON product_margins(tenant_id)")
            print("[OK] product_margins migrated successfully")

        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
