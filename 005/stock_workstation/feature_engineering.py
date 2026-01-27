# stock_workstation/feature_engineering.py

import pandas as pd
from datetime import time

def calculate_bidding_strength(current_day_data: pd.DataFrame, historical_data: dict) -> float:
    """
    Calculates the Bidding Strength.
    Definition: (Current day's turnover at 09:25 / Average turnover at 09:25 for the past 40 days).
    Assumption: Turnover at 09:25 is the cumulative trading amount up to 09:25.
    
    Args:
        current_day_data (pd.DataFrame): Minute-level data for the current day.
        historical_data (dict): Dictionary of minute-level historical data for past days.
        
    Returns:
        float: The calculated bidding strength. Returns 0 if denominator is zero or data is insufficient.
    """
    current_day_turnover_at_0925 = 0
    # Find the cumulative turnover at or just after 09:25 for the current day
    if not current_day_data.empty:
        time_0925 = time(9, 25)
        # Assuming '时间' is a datetime object and '成交额' is turnover
        current_day_data['时间_time'] = current_day_data['时间'].dt.time
        df_0925 = current_day_data[current_day_data['时间_time'] <= time_0925]
        if not df_0925.empty:
            current_day_turnover_at_0925 = df_0925['成交额'].sum()

    historical_turnovers_at_0925 = []
    for date, df in historical_data.items():
        if not df.empty:
            time_0925 = time(9, 25)
            df['时间_time'] = df['时间'].dt.time
            df_0925 = df[df['时间_time'] <= time_0925]
            if not df_0925.empty:
                historical_turnovers_at_0925.append(df_0925['成交额'].sum())
    
    if historical_turnovers_at_0925:
        avg_historical_turnover_at_0925 = sum(historical_turnovers_at_0925) / len(historical_turnovers_at_0925)
    else:
        avg_historical_turnover_at_0925 = 0

    if avg_historical_turnover_at_0925 > 0:
        return current_day_turnover_at_0925 / avg_historical_turnover_at_0925
    return 0

def calculate_efficiency_before_10am(current_day_data: pd.DataFrame) -> float:
    """
    Calculates the Efficiency before 10 AM.
    Definition: (Price change at 10:00 relative to opening price / Cumulative trading volume before 10:00).
    Assumption: 10:00 price is '收盘' at 10:00. Opening price is '开盘' at 09:15.
                Cumulative volume is sum of '成交量' from 09:15 to 10:00.
                
    Args:
        current_day_data (pd.DataFrame): Minute-level data for the current day.
        
    Returns:
        float: The calculated efficiency before 10 AM. Returns 0 if denominator is zero or data is insufficient.
    """
    if current_day_data.empty:
        return 0

    # Ensure '时间' is datetime and filter 09:15-10:00
    current_day_data['时间_time'] = current_day_data['时间'].dt.time
    
    open_price_0915 = 0
    # The '开盘' of the first minute (09:15)
    first_minute_data = current_day_data[current_day_data['时间_time'] == time(9, 15)]
    if not first_minute_data.empty:
        open_price_0915 = first_minute_data.iloc[0]['开盘']
    
    close_price_1000 = 0
    # The '收盘' of the minute ending at 10:00
    last_minute_data = current_day_data[current_day_data['时间_time'] == time(10, 0)]
    if not last_minute_data.empty:
        close_price_1000 = last_minute_data.iloc[0]['收盘']

    cumulative_volume_before_1000 = 0
    df_before_1000 = current_day_data[current_day_data['时间_time'] <= time(10, 0)]
    if not df_before_1000.empty:
        cumulative_volume_before_1000 = df_before_1000['成交量'].sum()

    if cumulative_volume_before_1000 > 0:
        price_change = close_price_1000 - open_price_0915
        return price_change / cumulative_volume_before_1000
    return 0

def detect_moat_support(current_day_data: pd.DataFrame, golden_pit_range: tuple = (578, 580), high_volume_threshold: float = 0.5) -> bool:
    """
    Detects "Moat Support" (护城河支撑检测) and "Characteristic Inflection Points".
    Simplified heuristic due to lack of direct L2 order book data from akshare.
    
    A "characteristic inflection point" is identified if:
    1. Price is within the golden pit range.
    2. Trading volume is high (e.g., above a certain percentile or threshold for the day).
    3. Price is not falling significantly (e.g., current minute's close >= current minute's open).

    Args:
        current_day_data (pd.DataFrame): Minute-level data for the current day (09:15-10:00).
        golden_pit_range (tuple): (lower_bound, upper_bound) for the "golden pit".
        high_volume_threshold (float): Threshold for high volume (e.g., 0.5 means above 50th percentile of daily volume).

    Returns:
        bool: True if a "characteristic inflection point" is detected, False otherwise.
    """
    if current_day_data.empty:
        return False

    # Calculate a dynamic high volume threshold based on the day's volume
    if not current_day_data['成交量'].empty:
        volume_threshold = current_day_data['成交量'].quantile(high_volume_threshold)
    else:
        volume_threshold = 0

    for index, row in current_day_data.iterrows():
        close_price = row['收盘']
        open_price = row['开盘']
        volume = row['成交量']

        # Check if price is within golden pit
        if golden_pit_range[0] <= close_price <= golden_pit_range[1]:
            # Check for high volume (放量)
            if volume > volume_threshold:
                # Check for not falling (不跌的瞬间) - simplified as close >= open for the minute
                if close_price >= open_price:
                    # Characteristic inflection point detected
                    return True
    return False

if __name__ == '__main__':
    # Placeholder for testing. In a real scenario, you'd use data from data_connector.py
    # For demonstration, creating dummy data.
    from datetime import datetime, timedelta
    import numpy as np

    print("--- Testing Feature Engineering Functions ---")

    # Dummy historical data (e.g., 3 days)
    historical_dfs = {}
    base_date = datetime(2024, 1, 20)
    for i in range(3):
        current_date = base_date + timedelta(days=i)
        minutes = []
        for h in range(9, 10):
            for m in range(0, 60):
                if h == 9 and m < 15: # Skip before 09:15
                    continue
                dt = datetime(current_date.year, current_date.month, current_date.day, h, m)
                # Simulate some data
                open_p = 580 + np.random.rand() * 5
                close_p = open_p + (np.random.rand() - 0.5) * 2
                high_p = max(open_p, close_p) + np.random.rand()
                low_p = min(open_p, close_p) - np.random.rand()
                volume = 1000 + np.random.rand() * 500
                amount = volume * (open_p + close_p) / 2
                minutes.append({
                    '时间': dt, '开盘': open_p, '收盘': close_p, '最高': high_p,
                    '最低': low_p, '成交量': volume, '成交额': amount
                })
        historical_dfs[current_date.strftime('%Y-%m-%d')] = pd.DataFrame(minutes)

    # Dummy current day data
    current_day = datetime(2024, 1, 23) # A different day
    current_day_minutes = []
    for h in range(9, 10):
        for m in range(0, 60):
            if h == 9 and m < 15: # Skip before 09:15
                continue
            dt = datetime(current_day.year, current_day.month, current_day.day, h, m)
            open_p = 580 + np.random.rand() * 5
            close_p = open_p + (np.random.rand() - 0.5) * 2
            high_p = max(open_p, close_p) + np.random.rand()
            low_p = min(open_p, close_p) - np.random.rand()
            volume = 1200 + np.random.rand() * 600
            amount = volume * (open_p + close_p) / 2
            current_day_minutes.append({
                '时间': dt, '开盘': open_p, '收盘': close_p, '最高': high_p,
                '最低': low_p, '成交量': volume, '成交额': amount
            })
    current_day_df = pd.DataFrame(current_day_minutes)

    # Simulate a "golden pit" entry with high volume
    # Find a minute around 09:40-09:50
    for idx, row in current_day_df.iterrows():
        if row['时间'].time() == time(9, 45):
            current_day_df.loc[idx, '收盘'] = 579.5 # Within golden pit
            current_day_df.loc[idx, '开盘'] = 579.0 # Price not falling
            current_day_df.loc[idx, '成交量'] = current_day_df['成交量'].max() * 0.9 # High volume
            current_day_df.loc[idx, '成交额'] = current_day_df.loc[idx, '成交量'] * (current_day_df.loc[idx, '收盘'] + current_day_df.loc[idx, '开盘']) / 2
            break

    # Calculate features
    bidding_strength = calculate_bidding_strength(current_day_df, historical_dfs)
    print(f"Bidding Strength: {bidding_strength:.2f}")

    efficiency_before_10am = calculate_efficiency_before_10am(current_day_df)
    print(f"Efficiency Before 10 AM: {efficiency_before_10am:.4f}")

    moat_support_detected = detect_moat_support(current_day_df)
    print(f"Moat Support Detected: {moat_support_detected}")