import pandas as pd
from datetime import datetime

def load_sales_data(filepath, sheet_name="Sheet1"):
    """
    Loads sales data from an Excel file (XLSX) and parses the 'Date' column.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name, parse_dates=['Date'], engine='openpyxl')
    return df


def append_daily_sales(master_df, new_data_df):
    """
    Appends new sales data to the master DataFrame, removing duplicates.
    """
    combined = pd.concat([master_df, new_data_df], ignore_index=True)

    # Avoid duplication based on Date + Particular + Voucher No.
    combined.drop_duplicates(
        subset=['Date', 'Particular', 'Voucher No.'],
        keep='last',
        inplace=True
    )
    
    return combined

