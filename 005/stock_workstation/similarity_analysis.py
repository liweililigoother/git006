# stock_workstation/similarity_analysis.py

import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw # requires pip install fastdtw, which includes scipy

def dtw_similarity(series1: pd.Series, series2: pd.Series) -> float:
    """
    Calculates the Dynamic Time Warping (DTW) distance between two time series.
    Assumes series are aligned by time or represent comparable intervals.
    
    Args:
        series1 (pd.Series): First time series (e.g., '收盘' prices).
        series2 (pd.Series): Second time series.
        
    Returns:
        float: DTW distance between the two series. Lower values indicate higher similarity.
    """
    # Ensure series are of numeric type
    s1 = series1.astype(float).values
    s2 = series2.astype(float).values
    
    distance, path = fastdtw(s1, s2, dist=euclidean)
    return distance

def find_historical_twin_days(current_day_series: pd.Series, historical_data: dict, top_n: int = 3) -> dict:
    """
    Finds historical 'twin days' whose 09:15-10:00 price patterns are most similar
    to the current day's pattern using DTW.

    Args:
        current_day_series (pd.Series): Current day's price series (e.g., '收盘' prices from 09:15-10:00).
        historical_data (dict): Dictionary of minute-level historical DataFrames.
                                Keys are dates (YYYY-MM-DD).
        top_n (int): Number of top most similar historical days to return.

    Returns:
        dict: A dictionary of the top_n most similar historical days.
              Keys are dates (YYYY-MM-DD), values are their full minute-level DataFrames.
    """
    similarities = {}
    
    if current_day_series.empty:
        return {}

    for date, df in historical_data.items():
        if not df.empty:
            # We are comparing only the 09:15-10:00 segment
            historical_series = df['收盘'] # Assuming '收盘' is the price we compare
            
            # Ensure both series have the same length for direct comparison, or handle variable lengths with DTW
            # If lengths differ significantly, DTW is robust. If minor differences, it's fine.
            if len(historical_series) > 1 and len(current_day_series) > 1: # Minimum 2 points for DTW
                 dtw_dist = dtw_similarity(current_day_series, historical_series)
                 similarities[date] = dtw_dist
            else:
                continue # Skip if insufficient data points

    # Sort by DTW distance (ascending) to get most similar
    sorted_similarities = sorted(similarities.items(), key=lambda item: item[1])
    
    twin_days = {}
    for i in range(min(top_n, len(sorted_similarities))):
        date, _ = sorted_similarities[i]
        twin_days[date] = historical_data[date] # Return the full DataFrame for the twin day
        
    return twin_days

if __name__ == '__main__':
    # Example usage with dummy data
    print("--- Testing DTW Similarity Analysis Functions ---")
    from datetime import datetime, timedelta

    # Dummy historical data (e.g., 5 days)
    historical_data_for_dtw = {}
    base_date = datetime(2024, 1, 15)
    for i in range(5):
        current_date = base_date + timedelta(days=i)
        minutes = []
        for h in range(9, 10):
            for m in range(15, 61): # 09:15-10:00
                dt = datetime(current_date.year, current_date.month, current_date.day, h, m)
                price = 580 + np.sin(m/10 + h) * 5 + np.random.rand() * 2
                minutes.append({
                    '时间': dt, '开盘': price-0.5, '收盘': price, '最高': price+0.5,
                    '最低': price-1, '成交量': 1000, '成交额': 1000*price
                })
        historical_data_for_dtw[current_date.strftime('%Y-%m-%d')] = pd.DataFrame(minutes)

    # Dummy current day series - make it similar to one of the historical days
    current_day = datetime(2024, 1, 20)
    current_day_minutes = []
    # Make it similar to 2024-01-16 (i=1) for testing
    for h in range(9, 10):
        for m in range(15, 61): # 09:15-10:00
            dt = datetime(current_day.year, current_day.month, current_day.day, h, m)
            price = 580 + np.sin(m/10 + h) * 5 + np.random.rand() * 1.5 # Slightly noisy
            current_day_minutes.append({
                '时间': dt, '开盘': price-0.5, '收盘': price, '最高': price+0.5,
                '最低': price-1, '成交量': 1000, '成交额': 1000*price
            })
    current_day_df = pd.DataFrame(current_day_minutes)
    current_day_series = current_day_df['收盘']

    print(f"\nCurrent Day Series (first 5 prices):\n{current_day_series.head()}")
    
    twin_days = find_historical_twin_days(current_day_series, historical_data_for_dtw, top_n=2)

    if twin_days:
        print(f"\nFound {len(twin_days)} historical twin days:")
        for date, df in twin_days.items():
            print(f"- {date}: First 5 prices:\n{df['收盘'].head()}")
    else:
        print("No twin days found.")
