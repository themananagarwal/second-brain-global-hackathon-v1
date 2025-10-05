# reorder_evaluator.py

# ------------------------------------------------------------
# Computes Reorder Points (ROP) per SKU using recent demand
# and saves results to CSV + Excel.

# How to run (simple):
# python reorder_evaluator.py

# Tweak parameters in the __main__ block at the bottom.
# ------------------------------------------------------------

import os
import pandas as pd
import numpy as np

# -----------------------------
# Config: service level Z table
# -----------------------------
Z_TABLE = {
    0.90: 1.28,
    0.95: 1.65,
    0.975: 1.96,
    0.99: 2.33,
}


def _nearest_z(service_level: float) -> float:
    """Map service level (probability) to a Z value, picking the nearest known level."""
    if service_level in Z_TABLE:
        return Z_TABLE[service_level]
    k = min(Z_TABLE.keys(), key=lambda x: abs(x - service_level))
    return Z_TABLE[k]


def evaluate_reorder_points(
        sales_file="data/MDF Sales data.xlsx",
        inventory_file="data/latest_inventory.csv",
        eoq_file="outputs/eoq_results.csv",
        sheet_name="Sheet1",
        lookback_days=120,  # recent window for responsiveness (try 90–120)
        default_lead_time_days=7,  # can be overridden per SKU
        default_service_level=0.95,  # can be overridden per SKU (probability, not percent)
        lead_time_map=None,  # dict: { "11MM DWR": 10, ... }
        service_level_map=None,  # dict: { "11MM DWR": 0.99, ... }
        on_order_file=None,  # optional CSV with columns: Particular,on_order
        backorders_file=None,  # optional CSV with columns: Particular,backorders
        # --- Business floors (set to 0 to disable) ---
        min_safety_stock=0,  # e.g., 10 (units)
        min_reorder_point=0  # e.g., 20 (units)
):
    """
    Builds ROP from recent demand statistics and current inventory.
    Returns a DataFrame and writes:
      - data/reorder_evaluation.csv
      - data/reorder_evaluation.xlsx

    Columns:
      Particular, mu_daily, sigma_daily, lead_time_days, service_level, Z,
      safety_stock, lead_time_demand, reorder_point,
      current_inventory, on_order, backorders, inventory_position,
      EOQ, need_reorder, suggested_order_qty, Action
    """
    # -----------------------------
    # Load inputs
    # -----------------------------
    sales_df = pd.read_excel(sales_file, sheet_name=sheet_name)
    inv_df = pd.read_csv(inventory_file)
    eoq_df = pd.read_csv(eoq_file)

    # Normalize columns
    for df in (sales_df, inv_df, eoq_df):
        df.columns = df.columns.str.strip()
    if 'Particulars' in sales_df.columns:
        sales_df = sales_df.rename(columns={'Particulars': 'Particular'})
    sales_df['Date'] = pd.to_datetime(sales_df['Date'])

    # Optional on-order/backorders
    on_order_df = pd.DataFrame(columns=['Particular', 'on_order'])
    if on_order_file and os.path.exists(on_order_file):
        on_order_df = pd.read_csv(on_order_file).rename(columns=str.strip)
    backorders_df = pd.DataFrame(columns=['Particular', 'backorders'])
    if backorders_file and os.path.exists(backorders_file):
        backorders_df = pd.read_csv(backorders_file).rename(columns=str.strip)

    # -----------------------------
    # Recent window daily demand per SKU
    # -----------------------------
    max_date = sales_df['Date'].max()
    start_date = max_date - pd.Timedelta(days=lookback_days - 1)
    recent = sales_df.loc[sales_df['Date'].between(start_date, max_date)].copy()

    # We want positive demand numbers (not negative stock movements)
    # If your sales quantities are negative (for inventory movement), flip:
    # recent['Quantity'] = recent['Quantity'].abs()

    all_days = pd.date_range(start=start_date.normalize(), end=max_date.normalize(), freq='D')

    # Daily demand matrix: rows=SKU, cols=day, values=units (0 on days with no sales)
    daily = (
        recent
        .groupby(['Particular', recent['Date'].dt.normalize()])['Quantity']
        .sum()
        .unstack(fill_value=0)
    ).reindex(columns=all_days, fill_value=0)

    # Stats per SKU
    mu_daily = daily.mean(axis=1)  # average units/day
    sigma_daily = daily.std(axis=1, ddof=1).fillna(0)  # sample std (0 if 1 obs)

    stats = pd.DataFrame({
        'Particular': daily.index,
        'mu_daily': mu_daily.values,
        'sigma_daily': sigma_daily.values
    })

    # -----------------------------
    # Merge inventory / EOQ / orders
    # -----------------------------
    inv_df = inv_df.rename(columns={'Quantity': 'current_inventory'})

    merged = (
        stats
        .merge(inv_df[['Particular', 'current_inventory']], on='Particular', how='left')
        .merge(eoq_df[['Particular', 'EOQ']], on='Particular', how='left')
        .merge(on_order_df, on='Particular', how='left')
        .merge(backorders_df, on='Particular', how='left')
    )

    merged['current_inventory'] = merged['current_inventory'].fillna(0).astype(float)
    merged['EOQ'] = merged['EOQ'].fillna(0).astype(float)
    merged['on_order'] = merged['on_order'].fillna(0).astype(float)
    merged['backorders'] = merged['backorders'].fillna(0).astype(float)

    # -----------------------------
    # Lead time & service level per SKU
    # -----------------------------
    lead_time_map = lead_time_map or {}
    service_level_map = service_level_map or {}

    merged['lead_time_days'] = merged['Particular'].map(lead_time_map).fillna(default_lead_time_days).astype(float)
    merged['service_level'] = merged['Particular'].map(service_level_map).fillna(default_service_level).astype(float)
    merged['Z'] = merged['service_level'].apply(_nearest_z)

    # -----------------------------
    # ROP components
    # -----------------------------
    merged['lead_time_demand'] = (merged['mu_daily'] * merged['lead_time_days']).clip(lower=0)
    merged['safety_stock'] = (merged['Z'] * merged['sigma_daily'] * np.sqrt(merged['lead_time_days'])).clip(lower=0)

    # Apply business floors if desired
    if min_safety_stock and min_safety_stock > 0:
        merged['safety_stock'] = merged['safety_stock'].apply(lambda x: max(x, float(min_safety_stock)))

    merged['reorder_point'] = merged['lead_time_demand'] + merged['safety_stock']

    if min_reorder_point and min_reorder_point > 0:
        merged['reorder_point'] = merged['reorder_point'].apply(lambda x: max(x, float(min_reorder_point)))

    # Round for presentation (keep internal precision above if you want)
    merged['safety_stock'] = merged['safety_stock'].round()
    merged['lead_time_demand'] = merged['lead_time_demand'].round()
    merged['reorder_point'] = merged['reorder_point'].round()

    # Inventory position = on hand + on order - backorders
    merged['inventory_position'] = merged['current_inventory'] + merged['on_order'] - merged['backorders']

    # Reorder flag and suggested qty
    merged['need_reorder'] = merged['inventory_position'] <= merged['reorder_point']
    merged['suggested_order_qty'] = np.where(merged['need_reorder'], merged['EOQ'], 0).astype(int)

    # -----------------------------
    # Action Classification (NEW)
    # -----------------------------
    def determine_action(row):
        """
        Classify inventory action priority for dashboard display.

        Returns:
            str: One of ["REORDER NOW", "REORDER SOON", "ADEQUATE", "OVERSTOCKED"]
        """
        ip = row['inventory_position']
        rop = row['reorder_point']
        eoq = row['EOQ']
        safety_stock = row['safety_stock']

        # Critical: At or below reorder point
        if ip <= rop:
            return "REORDER NOW"

        # Warning: Within safety stock buffer above ROP
        elif ip <= (rop + safety_stock * 0.5):
            return "REORDER SOON"

        # Excess: Significantly overstocked
        elif eoq > 0 and ip > (rop + eoq * 1.5):
            return "OVERSTOCKED"

        # Normal: Healthy inventory level
        else:
            return "ADEQUATE"

    # Apply action classification
    merged['Action'] = merged.apply(determine_action, axis=1)

    # Print action summary for verification
    print("\n📊 Action Summary:")
    print(merged['Action'].value_counts())

    # -----------------------------
    # Save & return
    # -----------------------------
    os.makedirs("data", exist_ok=True)
    merged_sorted = merged.sort_values(['need_reorder', 'Particular'], ascending=[False, True])

    # Save both CSV and Excel
    csv_path = "data/reorder_evaluation.csv"
    xlsx_path = "data/reorder_evaluation.xlsx"

    merged_sorted.to_csv(csv_path, index=False)

    try:
        merged_sorted.to_excel(xlsx_path, index=False)
    except Exception as e:
        # Excel requires openpyxl; we fail gracefully but keep CSV
        print(f"⚠️  Could not write Excel ({xlsx_path}). Install openpyxl? Error: {e}")

    return merged_sorted


# ------------------------------------------------------------
# Run directly: tweak parameters here, then `python reorder_evaluator.py`
# ------------------------------------------------------------
if __name__ == "__main__":
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.width", 180)

    df = evaluate_reorder_points(
        sales_file="data/MDF Sales data.xlsx",
        inventory_file="data/latest_inventory.csv",
        eoq_file="outputs/eoq_results.csv",
        sheet_name="Sheet1",
        lookback_days=120,  # recent window for variability
        default_lead_time_days=7,  # override if needed
        default_service_level=0.95,  # e.g., 0.95 (not 95)
        lead_time_map=None,  # e.g., {"3.30MM DWR": 10}
        service_level_map=None,  # e.g., {"3.30MM DWR": 0.99}
        on_order_file=None,  # e.g., "data/on_order.csv"
        backorders_file=None,  # e.g., "data/backorders.csv"
        min_safety_stock=10,  # ✅ set floors for business realism
        min_reorder_point=20
    )

    cols = [
        "Particular", "mu_daily", "sigma_daily", "lead_time_days", "service_level", "Z",
        "lead_time_demand", "safety_stock", "reorder_point",
        "current_inventory", "on_order", "backorders", "inventory_position",
        "EOQ", "need_reorder", "suggested_order_qty", "Action"
    ]

    print("\nReorder evaluation (showing key columns):")
    print(df[cols].to_string(index=False))
    print("\nSaved -> data/reorder_evaluation.csv and data/reorder_evaluation.xlsx")
