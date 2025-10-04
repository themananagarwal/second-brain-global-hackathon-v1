from pathlib import Path
import os
import pandas as pd
from Modules.data_ingestion import load_sales_data, append_daily_sales

# Resolve project root as the parent of the Modules folder containing this file
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# --- Step 1: Load your existing sales data file ---
sales_file = PROJECT_ROOT / "data" / "MDF Sales data.xlsx"
#sales_file = "data/MDF Sales data.xlsx"

sales_df = load_sales_data(str(sales_file), sheet_name="Sheet1")

# Ensure Date column is in datetime format
sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

print(" Loaded master sales data:")
print(sales_df.head())

# --- Optional: Step 2 — Append a new daily sales file ---
# new_sales_file = "data/new_sales_today.csv"
# new_sales_df = load_sales_data(new_sales_file)

# sales_df = append_daily_sales(sales_df, new_sales_df)
# print("✅ After appending new sales data:")
# print(sales_df.tail())

# --- Optional: Step 3 — Save the updated master file ---
# sales_df.to_csv(sales_file, index=False)

# Save it as a CSV file under project_root/data
out_csv = PROJECT_ROOT / "data" / "sales_data.csv"
out_csv.parent.mkdir(parents=True, exist_ok=True)  # ensure data/ exists
sales_df.to_csv(out_csv, index=False)

#sales_df.to_csv("data/sales_data.csv", index=False)
print(f"📁 Saved sales data to '{out_csv}'")