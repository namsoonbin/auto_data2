# -*- coding: utf-8 -*-
"""
Migration script to fix product_margins unique constraint
Changes from UNIQUE(option_id) to UNIQUE(tenant_id, option_id)
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
        print("Starting product_margins table migration...")

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_margins'")
        if not cursor.fetchone():
            print("[INFO] product_margins table does not exist yet - skipping migration")
            return

        # Create a new table with the correct structure
        print("Step 1: Creating new product_margins table with correct constraints...")
        cursor.execute("""
            CREATE TABLE product_margins_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id CHAR(32),
                option_id BIGINT NOT NULL,
                product_name VARCHAR NOT NULL,
                option_name VARCHAR,
                cost_price FLOAT DEFAULT 0.0,
                selling_price FLOAT DEFAULT 0.0,
                margin_amount FLOAT DEFAULT 0.0,
                margin_rate FLOAT DEFAULT 0.0,
                fee_rate FLOAT DEFAULT 0.0,
                fee_amount FLOAT DEFAULT 0.0,
                vat FLOAT DEFAULT 0.0,
                created_at DATETIME,
                updated_at DATETIME,
                notes VARCHAR,
                FOREIGN KEY(tenant_id) REFERENCES tenants(id),
                UNIQUE(tenant_id, option_id)
            )
        """)

        # Copy data from old table to new table
        print("Step 2: Copying data from old table...")
        cursor.execute("""
            INSERT INTO product_margins_new
            SELECT * FROM product_margins
        """)

        # Drop old table
        print("Step 3: Dropping old table...")
        cursor.execute("DROP TABLE product_margins")

        # Rename new table to original name
        print("Step 4: Renaming new table...")
        cursor.execute("ALTER TABLE product_margins_new RENAME TO product_margins")

        # Create indexes
        print("Step 5: Creating indexes...")
        cursor.execute("CREATE INDEX ix_product_margins_tenant_id ON product_margins(tenant_id)")
        cursor.execute("CREATE INDEX ix_product_margins_option_id ON product_margins(option_id)")
        cursor.execute("CREATE INDEX ix_product_margins_product_name ON product_margins(product_name)")

        conn.commit()
        print("\n[SUCCESS] product_margins table migration completed successfully!")
        print("The table now has UNIQUE(tenant_id, option_id) constraint.")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
