# -*- coding: utf-8 -*-
"""
Database migration script to add conversion_sales column
"""
import sqlite3
import os
import sys

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "coupang_integrated.db")

def migrate():
    """Add conversion_sales column to tables"""

    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return False

    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists in integrated_records
        cursor.execute("PRAGMA table_info(integrated_records)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'conversion_sales' not in columns:
            print("Adding conversion_sales column to integrated_records table...")
            cursor.execute("""
                ALTER TABLE integrated_records
                ADD COLUMN conversion_sales REAL DEFAULT 0.0
            """)
            print("[OK] Successfully added conversion_sales to integrated_records")
        else:
            print("[OK] conversion_sales column already exists in integrated_records")

        # Check if column already exists in ad_records_legacy
        cursor.execute("PRAGMA table_info(ad_records_legacy)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'conversion_sales' not in columns:
            print("Adding conversion_sales column to ad_records_legacy table...")
            cursor.execute("""
                ALTER TABLE ad_records_legacy
                ADD COLUMN conversion_sales REAL DEFAULT 0.0
            """)
            print("[OK] Successfully added conversion_sales to ad_records_legacy")
        else:
            print("[OK] conversion_sales column already exists in ad_records_legacy")

        # Commit changes
        conn.commit()
        print("\n[OK] Migration completed successfully!")

        # Verify the changes
        print("\nVerifying migration...")
        cursor.execute("PRAGMA table_info(integrated_records)")
        integrated_columns = [col[1] for col in cursor.fetchall()]
        print(f"integrated_records columns: {', '.join(integrated_columns)}")

        cursor.execute("PRAGMA table_info(ad_records_legacy)")
        ad_columns = [col[1] for col in cursor.fetchall()]
        print(f"ad_records_legacy columns: {', '.join(ad_columns)}")

        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add conversion_sales column")
    print("=" * 60)
    print()

    success = migrate()

    if success:
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("You can now restart the backend server.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("Migration failed. Please check the errors above.")
        print("=" * 60)
        sys.exit(1)
