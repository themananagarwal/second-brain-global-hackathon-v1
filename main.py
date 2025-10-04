from pathlib import Path
import pandas as pd
from Modules.data_ingestion import load_sales_data, append_daily_sales

# main.py is now at the repo root
PROJECT_ROOT = Path.cwd()

# --- Step 1: Load your existing sales data file ---
sales_file = PROJECT_ROOT / "data" / "MDF Sales data.xlsx"
sales_df = load_sales_data(str(sales_file), sheet_name="Sheet1")

# Ensure Date column is in datetime format
sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

print(" Loaded master sales data:")
print(sales_df.head())

# --- Optional: Step 2 — Append a new daily sales file ---
# new_sales_file = PROJECT_ROOT / "data" / "new_sales_today.csv"
# new_sales_df = load_sales_data(str(new_sales_file))
# sales_df = append_daily_sales(sales_df, new_sales_df)
# print("✅ After appending new sales data:")
# print(sales_df.tail())

# --- Optional: Step 3 — Save the updated master file ---
# sales_df.to_csv(sales_file, index=False)

# Save it as a CSV file under project_root/data
out_csv = PROJECT_ROOT / "data" / "sales_data.csv"
out_csv.parent.mkdir(parents=True, exist_ok=True)
sales_df.to_csv(out_csv, index=False)
print(f"📁 Saved sales data to '{out_csv}'")