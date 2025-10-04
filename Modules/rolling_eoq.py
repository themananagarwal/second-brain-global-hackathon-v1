import pandas as pd
import numpy as np

def calculate_rolling_eoq(sales_df, sku_weights, lookback_days=365, today=None):
    """
    Calculates EOQ per SKU based on recent sales data.

    Parameters:
        sales_df (pd.DataFrame): Cleaned sales data containing 'Date', 'Particular', and 'Quantity'.
        sku_weights (dict): Mapping of SKU (Particular) to weight per piece in kg.
        lookback_days (int): Number of days to look back for demand estimation.
        today (str or datetime): Override current date for testing. Defaults to today's date.

    Returns:
        pd.DataFrame with EOQ values and supporting metrics per SKU.
    """

    # Use current date or override
    if today is None:
        today = pd.Timestamp.today()
    else:
        today = pd.to_datetime(today)

    # Filter sales to the recent period
    recent_sales = sales_df.copy()
    recent_sales['Date'] = pd.to_datetime(recent_sales['Date'])
    max_date = recent_sales['Date'].max()
    recent_sales = recent_sales[recent_sales['Date'] >= max_date - pd.Timedelta(days=lookback_days)]
    recent_sales.to_csv("data/recent_sales.csv", index=False)

    # Calculate total quantity sold per SKU
    demand_summary = recent_sales.groupby('Particular', as_index=False)['Quantity'].sum()
    demand_summary.rename(columns={'Quantity': 'past_demand'}, inplace=True)
    demand_summary.to_csv("data/demand_summary.csv", index=False)

    # Estimate daily demand (D)
    demand_summary['daily_demand'] = demand_summary['past_demand'] / lookback_days
    demand_summary['annual_demand'] = demand_summary['daily_demand'] * 365

    # Estimate per-piece holding cost dynamically using weight
    def estimate_holding_cost(sku):
        weight = sku_weights.get(sku, 40)  # Default weight = 40kg if unknown
        monthly_cost = 500 + 15000 + 16000 * 2  # Electricity + Rent + Labour
        monthly_cost_per_piece = (monthly_cost / 10000) * (weight / 40)  # Assumes 10,000kg capacity
        return monthly_cost_per_piece * 12  # Annualize

    demand_summary['holding_cost'] = demand_summary['Particular'].apply(estimate_holding_cost)

    # Ordering cost based on unloading (₹170 per ton, assumming for 12 tons every time)
    ORDERING_COST_PER_ORDER = 2000.0  # ₹ per order (unloading event / truck)
    demand_summary['ordering_cost'] = ORDERING_COST_PER_ORDER

    # Ensure numeric inputs
    demand_summary['annual_demand'] = pd.to_numeric(demand_summary['annual_demand'], errors='coerce')
    demand_summary['ordering_cost'] = pd.to_numeric(demand_summary['ordering_cost'], errors='coerce')
    demand_summary['holding_cost'] = pd.to_numeric(demand_summary['holding_cost'], errors='coerce')


    # EOQ formula: sqrt(2DS / H)
    demand_summary['EOQ'] = np.sqrt(
        (2 * demand_summary['annual_demand'] * demand_summary['ordering_cost']) /
        demand_summary['holding_cost']
    ).round().astype(int)

    # Add SKU weight to final result
    demand_summary['unit_weight'] = demand_summary['Particular'].map(sku_weights)

    # Cap EOQ at annual demand
    demand_summary['EOQ'] = demand_summary[['EOQ', 'annual_demand']].min(axis=1).astype(int)

    return demand_summary[['Particular', 'daily_demand', 'annual_demand', 'EOQ', 'unit_weight', 'ordering_cost', 'holding_cost']]



