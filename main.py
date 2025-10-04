import pandas as pd
from Modules.data_ingestion import load_sales_data, append_daily_sales

# --- Step 1: Load your existing sales data file ---
sales_file = "data/MDF Sales data.xlsx"
sales_df = load_sales_data(sales_file, sheet_name="Sheet1")

# Ensure Date column is in datetime format
sales_df['Date'] = pd.to_datetime(sales_df['Date'])


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

# Save it as a CSV file
sales_df.to_csv("data/sales_data.csv", index=False)
print("📁 Saved sales data to 'data/sales_data.csv'")

