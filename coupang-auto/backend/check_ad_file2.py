# -*- coding: utf-8 -*-
import pandas as pd

# Read ad file
ad_file = r"C:\Users\User\Desktop\auto_data2\쿠팡자동\2520251029_A01116666_custom_report (1).xlsx"

print(f"Reading file: {ad_file}\n")
df = pd.read_excel(ad_file)

print(f"=== Column Names ===")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. {col}")

# Find the option ID column
option_col = None
ad_cost_col = None

for col in df.columns:
    if '옵션' in col and 'ID' in col:
        option_col = col
        print(f"\n[Option ID Column]: '{col}'")
    if '광고비' in col:
        ad_cost_col = col
        print(f"[Ad Cost Column]: '{col}'")

if option_col and ad_cost_col:
    # Search for the specific option ID
    option_id = 92582844462

    # Convert option_id column to numeric
    df[option_col] = pd.to_numeric(df[option_col], errors='coerce')

    # Find the row
    matching_rows = df[df[option_col] == option_id]

    print(f"\n=== Searching for Option ID: {option_id} ===")
    print(f"Found {len(matching_rows)} row(s)")

    if len(matching_rows) > 0:
        for idx, row in matching_rows.iterrows():
            print(f"\n--- Row {idx} ---")
            print(f"Option ID: {row[option_col]}")
            print(f"Ad Cost (raw value): {repr(row[ad_cost_col])}")
            print(f"Ad Cost (type): {type(row[ad_cost_col])}")

            # Try to convert to numeric
            try:
                cost_value = pd.to_numeric(row[ad_cost_col], errors='coerce')
                print(f"Ad Cost (converted): {cost_value}")
            except Exception as e:
                print(f"Conversion error: {e}")

            # Show all columns
            print(f"\n=== All Column Values ===")
            for col in df.columns:
                print(f"{col}: {row[col]}")
    else:
        print(f"\nOption ID {option_id} NOT FOUND")
        print(f"\nShowing all option IDs in file:")
        print(df[option_col].dropna().astype('int64').tolist()[:20])
else:
    print("\nCould not identify option_id or ad_cost columns")
