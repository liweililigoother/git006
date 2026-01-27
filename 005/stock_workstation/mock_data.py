# stock_workstation/mock_data.py

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def generate_mock_minute_data(start_price: float = 580.0, date: datetime = datetime.now()) -> pd.DataFrame:
    """
    Generates mock minute-level stock data for the 09:15-10:00 period.

    Args:
        start_price (float): The starting price for the simulation.
        date (datetime): The date for which to generate the mock data.

    Returns:
        pd.DataFrame: A DataFrame containing simulated minute-level data with
                      '时间', '开盘', '收盘', '最高', '最低', '成交量', '成交额' columns.
    """
    mock_data = []
    
    # Generate data for 09:15 to 10:00 (inclusive)
    # Total minutes = (10:00 - 09:15) + 1 minute for 10:00 itself = 45 + 1 = 46 minutes
    
    current_price = start_price
    for m_offset in range(46): # 0 to 45 minutes
        minute_time = date.replace(hour=9, minute=15) + timedelta(minutes=m_offset)
        
        # Simulate price movement
        open_price = current_price
        # Small random walk for price
        change = (np.random.rand() - 0.5) * 2 * (start_price * 0.001) # +/- 0.1% of start price
        close_price = open_price + change
        
        high_price = max(open_price, close_price) + np.random.rand() * (start_price * 0.0005)
        low_price = min(open_price, close_price) - np.random.rand() * (start_price * 0.0005)
        
        volume = np.random.randint(500, 3000) # Random volume
        amount = volume * close_price # Simplified amount calculation
        
        mock_data.append({
            '时间': minute_time,
            '开盘': open_price,
            '收盘': close_price,
            '最高': high_price,
            '最低': low_price,
            '成交量': volume,
            '成交额': amount
        })
        current_price = close_price # Next minute's open is current minute's close

    df = pd.DataFrame(mock_data)
    return df

if __name__ == '__main__':
    print("--- Testing Mock Data Generation ---")
    mock_df = generate_mock_minute_data(start_price=575.0, date=datetime(2024, 1, 27))
    print(mock_df.head())
    print(mock_df.tail())
    print(f"Generated {len(mock_df)} minutes of data.")

    # Test with a different start price
    mock_df_2 = generate_mock_minute_data(start_price=600.0)
    print("\n--- Testing with different start price ---")
    print(mock_df_2.head())
