from pathlib import Path
import pandas as pd
from Modules.data_ingestion import load_sales_data, append_daily_sales
from Modules.trends_analysis import calculate_monthly_mix, plot_monthly_mix_pct
from Modules.rolling_eoq import calculate_rolling_eoq
from Modules.inventory_tracker import build_inventory_timeline

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


# Calculate monthly mix
monthly_mix, monthly_mix_pct = calculate_monthly_mix(sales_df)

# Plot
plot_monthly_mix_pct(monthly_mix_pct)




# Create a dictionary mapping each SKU to its weight per piece
sku_weights = dict(zip(sales_df['Particular'], sales_df['Weight Per Piece']))

# Run EOQ calculation for the last 90 days
eoq_results = calculate_rolling_eoq(sales_df, sku_weights, lookback_days=365)

# Save or inspect the EOQ results
eoq_results.to_csv("outputs/eoq_results.csv", index=False)
print(eoq_results)



_, current_inventory = build_inventory_timeline(
    sales_file="data/MDF Sales data.xlsx",
    purchase_file="data/MDF purchase data.xlsx",
    base_inventory_file="data/Inventory Base Data.xlsx"
)

print(current_inventory.head())  # optional: preview
