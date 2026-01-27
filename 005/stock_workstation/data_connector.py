# stock_workstation/data_connector.py

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_minute_data(symbol: str, start_date: str, end_date: str, period: str = "1", adjust: str = "") -> pd.DataFrame:
    """
    Fetches minute-level historical data for a given stock symbol.
    Note: akshare.stock_zh_a_hist_min provides basic minute data (open, high, low, close, volume, amount).
    L2/time-series data (more detailed tick or order book info) might require other akshare interfaces
    or alternative data sources not directly covered by this function.

    Args:
        symbol (str): Stock symbol, e.g., "688027".
        start_date (str): Start date in "YYYYMMDD" format.
        end_date (str): End date in "YYYYMMDD" format.
        period (str): K-line period, e.g., "1", "5", "15", "30", "60". Default is "1" (minute).
        adjust (str): Adjustment type, e.g., "qfq" (前复权), "hfq" (后复权), "". Default is no adjustment.

    Returns:
        pd.DataFrame: DataFrame containing minute-level data.
    """
    try:
        # For A-share minute data, adjust stock symbol with exchange suffix if not already present
        if not (symbol.endswith('.SH') or symbol.endswith('.SZ')):
            # Assume 688xxx are Shanghai stocks, others might be Shenzhen.
            # This is a simplification; a more robust solution would determine exchange based on symbol prefix.
            if symbol.startswith('6'): # Shanghai stock
                symbol_with_suffix = f"{symbol}.SH"
            else: # Shenzhen stock (e.g., 00xxxx, 30xxxx)
                symbol_with_suffix = f"{symbol}.SZ"
        else:
            symbol_with_suffix = symbol

        df = ak.stock_zh_a_hist_min(symbol=symbol_with_suffix, period=period,
                                   start_date=start_date, end_date=end_date, adjust=adjust)

        # Filter for 09:15-10:00. akshare returns datetime objects for '时间' column.
        if '时间' in df.columns:
            df['时间'] = pd.to_datetime(df['时间'])
            df_filtered = df[(df['时间'].dt.time >= pd.to_datetime('09:15:00').time()) &
                             (df['时间'].dt.time <= pd.to_datetime('10:00:00').time())].copy()
            return df_filtered
        else:
            print("Warning: '时间' column not found in the data.")
            return pd.DataFrame()

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def get_past_n_trading_days_data(symbol: str, n_days: int = 40) -> dict:
    """
    Fetches minute-level data for the past N trading days (09:15-10:00 range).

    Args:
        symbol (str): Stock symbol, e.g., "688027".
        n_days (int): Number of past trading days to retrieve data for.

    Returns:
        dict: A dictionary where keys are dates (YYYY-MM-DD) and values are DataFrames
              containing minute-level data for that day, filtered from 09:15 to 10:00.
    """
    all_data = {}
    today = datetime.now()
    # To get N *trading* days, we might need to fetch a broader range and then filter.
    # A simpler approach for now is to get a wider date range and then filter by actual trading days.
    # akshare.tool_trade_date_hist_sina() can give trade dates.
    trade_dates_df = ak.tool_trade_date_hist_sina()
    trade_dates = [pd.to_datetime(d).strftime('%Y%m%d') for d in trade_dates_df['trade_date'].iloc[::-1]] # get recent dates
    
    # Filter to ensure we have dates within the last N trading days
    recent_trade_dates = []
    for date_str in trade_dates:
        if pd.to_datetime(date_str) <= today:
            recent_trade_dates.append(date_str)
        if len(recent_trade_dates) >= n_days + 5: # Fetch a few extra days to be safe
            break
            
    recent_trade_dates = recent_trade_dates[-n_days:] # Take the last N trading days

    for date_str in recent_trade_dates:
        # Akshare's stock_zh_a_hist_min usually takes a date range, not single day.
        # So we'll fetch for each day individually for simplicity of filtering by day.
        # This might be inefficient for many days; a batch fetch and then splitting would be better.
        # For the purpose of getting 09:15-10:00 data, this is acceptable.
        
        # Ensure start_date and end_date are the same for single-day fetching
        day_data = get_minute_data(symbol, date_str, date_str)
        if not day_data.empty:
            # Store data keyed by date, e.g., '2023-01-27'
            all_data[pd.to_datetime(date_str).strftime('%Y-%m-%d')] = day_data
    return all_data

if __name__ == '__main__':
    # Example usage:
    stock_symbol = "688027"
    past_40_days_data = get_past_n_trading_days_data(stock_symbol, n_days=3) # Reduced to 3 for quick testing

    if past_40_days_data:
        print(f"Fetched data for {stock_symbol} for {len(past_40_days_data)} trading days:")
        for date, df in past_40_days_data.items():
            print(f"\n--- Data for {date} (09:15 - 10:00) ---")
            print(df.head())
            print(df.tail())
            print(f"Number of rows: {len(df)}")
    else:
        print("No data fetched.")

    # Test a single day fetch
    print("\n--- Testing single day fetch (20240126) ---")
    single_day_data = get_minute_data("688027", "20240126", "20240126")
    if not single_day_data.empty:
        print(single_day_data.head())
    else:
        print("No data for single day 20240126")
