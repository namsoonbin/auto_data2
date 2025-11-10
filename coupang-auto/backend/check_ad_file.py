# -*- coding: utf-8 -*-
import pandas as pd
import sys

# Read ad file
ad_file = r"C:\Users\User\Desktop\auto_data2\쿠팡자동\2520251029_A01116666_custom_report (1).xlsx"

print(f"Reading file: {ad_file}")
df = pd.read_excel(ad_file)

print(f"\n=== File Info ===")
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")

print(f"\n=== All Column Names ===")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. '{col}'")

# Search for option ID 92582844462
option_id_to_find = 92582844462
print(f"\n=== Searching for Option ID: {option_id_to_find} ===")

# Try to find which column contains option IDs
for col in df.columns:
    if 'option' in col.lower() or '옵션' in col.lower() or 'id' in col.lower():
        print(f"\nChecking column: '{col}'")
        # Convert to numeric and check
        df_temp = pd.to_numeric(df[col], errors='coerce')
        if option_id_to_find in df_temp.values:
            print(f"[FOUND] in column '{col}'!")
            # Show the row
            row = df[df_temp == option_id_to_find]
            print("\n=== Row Data ===")
            for c in df.columns[:15]:  # Show first 15 columns
                print(f"{c}: {row[c].values[0]}")
            break
else:
    print(f"\n[NOT FOUND] Option ID {option_id_to_find} NOT FOUND in any column")
    print("\nShowing first 3 rows of data:")
    print(df.head(3).to_string())
