import pandas as pd
import matplotlib.pyplot as plt

def extract_product_type(particular_column):
    """
    Extracts product type (DWR, DIR, HDHMR) from 'Particular' column.
    Assumes product type is one of these three in the string.
    """
    def extract(row):
        for product_type in ['DWR', 'DIR', 'HDHMR']:
            if product_type in row:
                return product_type
        return 'OTHER'

    return particular_column.apply(extract)


def calculate_monthly_mix(df):
    """
    Calculates monthly total weight per product type and percentage mix.
    Assumes 'Date', 'Particular', and 'Weight' columns exist.
    """
    df['Product_Type'] = extract_product_type(df['Particular'])

    df['YearMonth'] = df['Date'].dt.to_period('M')

    monthly_mix = df.groupby(['YearMonth', 'Product_Type'])['Weight'].sum().unstack(fill_value=0)

    # Add percentage columns
    monthly_mix_pct = monthly_mix.div(monthly_mix.sum(axis=1), axis=0) * 100

    return monthly_mix, monthly_mix_pct


def plot_monthly_mix_pct(monthly_mix_pct):
    """
    Plots the percentage mix of product types per month as a stacked area chart.
    """
    monthly_mix_pct.plot.area(figsize=(12, 6))
    plt.title('Monthly Product Mix (%)')
    plt.ylabel('Percentage')
    plt.xlabel('Month')
    plt.legend(title='Product Type')
    plt.tight_layout()
    plt.show()

