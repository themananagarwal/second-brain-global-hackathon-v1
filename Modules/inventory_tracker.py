import pandas as pd
import os
import matplotlib.pyplot as plt

def build_inventory_timeline(sales_file, purchase_file, base_inventory_file):
    # Load all datasets
    sales_df = pd.read_excel(sales_file, sheet_name="Sheet1")
    purchase_df = pd.read_excel(purchase_file, sheet_name="Sheet1")
    base_inventory = pd.read_excel(base_inventory_file, sheet_name="Sheet1")

    # Strip column names of leading/trailing spaces
    sales_df.columns = sales_df.columns.str.strip()
    purchase_df.columns = purchase_df.columns.str.strip()
    base_inventory.columns = base_inventory.columns.str.strip()

    # Rename 'Particulars' to 'Particular' if necessary
    if 'Particulars' in sales_df.columns:
        sales_df.rename(columns={'Particulars': 'Particular'}, inplace=True)
    if 'Particulars' in purchase_df.columns:
        purchase_df.rename(columns={'Particulars': 'Particular'}, inplace=True)
    if 'Particulars' in base_inventory.columns:
        base_inventory.rename(columns={'Particulars': 'Particular'}, inplace=True)

    # Ensure dates are in datetime format
    sales_df['Date'] = pd.to_datetime(sales_df['Date'])
    purchase_df['Date'] = pd.to_datetime(purchase_df['Date'])

    # Combine all events (purchases as positive, sales as negative)
    sales_df['Quantity'] = -sales_df['Quantity']  # sales reduce inventory
    combined = pd.concat([
        purchase_df[['Date', 'Particular', 'Quantity']],
        sales_df[['Date', 'Particular', 'Quantity']]
    ])

    # Sort chronologically
    combined.sort_values(by='Date', inplace=True)

    # Get list of all unique dates and SKUs
    all_dates = pd.date_range(start=combined['Date'].min(), end=combined['Date'].max())
    all_skus = combined['Particular'].unique()

    # Create a DataFrame to track inventory
    inventory = pd.DataFrame(index=all_dates, columns=all_skus)
    inventory = inventory.fillna(0).infer_objects(copy=False)

    # Add base inventory on the first day
    for _, row in base_inventory.iterrows():
        sku = row['Particular']
        qty = row['Quantity']
        inventory.loc[all_dates[0], sku] = qty

    # Aggregate all events by day and SKU
    daily_events = combined.groupby(['Date', 'Particular'])['Quantity'].sum().unstack(fill_value=0)

    # Fill in the inventory levels
    for i in range(1, len(inventory)):
        today = inventory.index[i]
        yesterday = inventory.index[i - 1]
        inventory.loc[today] = inventory.loc[yesterday]
        if today in daily_events.index:
            inventory.loc[today] += daily_events.loc[today]

    # Save the latest inventory snapshot
    latest_inventory = inventory.iloc[-1].reset_index()
    latest_inventory.columns = ['Particular', 'Quantity']
    os.makedirs("data", exist_ok=True)
    latest_inventory.to_csv("data/latest_inventory.csv", index=False)

    # Save the full inventory timeline
    inventory.to_csv("data/inventory_timeline.csv")

    # Create folder for plots
    plot_dir = "data/inventory_plots"
    os.makedirs(plot_dir, exist_ok=True)

    # Plot inventory levels for each SKU
    for sku in inventory.columns:
        plt.figure(figsize=(10, 4))
        inventory[sku].plot(title=f"Inventory Level Over Time: {sku}", ylabel="Quantity", xlabel="Date")
        plt.tight_layout()
        plt.savefig(f"{plot_dir}/{sku}.png")
        plt.close()

    return inventory, latest_inventory

# Example usage
if __name__ == "__main__":
    build_inventory_timeline(
        sales_file="data/MDF Sales data.xlsx",
        purchase_file="data/MDF purchase data.xlsx",
        base_inventory_file="data/inventory Base Data.xlsx"
    )
