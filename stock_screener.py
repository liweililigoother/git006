
import pandas as pd
import pandas_ta as ta
import akshare as ak
from tqdm import tqdm
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def screen_stocks():
    """
    Screens STAR Market (科创板) stocks based on a set of criteria:
    - Price < 50
    - Bollinger Bandwidth < 10% for the last 10 days
    - High liquidity (trading volume) 
    
    The top 5 stocks by average 20-day volume are selected.
    """
    print("Fetching list of STAR Market (科创板) stocks...")
    try:
        # Get all STAR Market stocks
        stock_list = ak.stock_kc_a_spot_em()
    except Exception as e:
        print(f"Error fetching stock list: {e}")
        return []

    print(f"Found {len(stock_list)} stocks. Starting screening process...")
    
    eligible_stocks = []
    
    # Use tqdm for a progress bar
    for index, row in tqdm(stock_list.iterrows(), total=stock_list.shape[0], desc="Screening Stocks"):
        code = row['代码']
        name = row['名称']
        
        try:
            # Fetch historical data for the last 100 days
            hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20240101", adjust="qfq")
            if hist_data.empty or len(hist_data) < 60:
                continue

            # 1. Price check
            latest_price = hist_data['收盘'].iloc[-1]
            if latest_price >= 50:
                continue

            # 2. Bollinger Bands check
            # Calculate Bollinger Bands using pandas_ta
            hist_data.ta.bbands(close='收盘', length=20, append=True)
            
            # Check if required columns exist
            b_upper_col = 'BBU_20_2.0'
            b_lower_col = 'BBL_20_2.0'
            b_middle_col = 'BBM_20_2.0'

            if not all(col in hist_data.columns for col in [b_upper_col, b_lower_col, b_middle_col]):
                continue

            # Calculate Bandwidth
            hist_data['bandwidth'] = (hist_data[b_upper_col] - hist_data[b_lower_col]) / hist_data[b_middle_col]

            # Check if the bands have not been opening for the last 3 days (i.e., bandwidth is not expanding)
            last_4_days_bandwidth = hist_data['bandwidth'].tail(4)
            if len(last_4_days_bandwidth) < 4:
                continue
            
            # Check if bandwidth is decreasing or staying the same
            is_not_opening = all(last_4_days_bandwidth.iloc[i] <= last_4_days_bandwidth.iloc[i-1] for i in range(1, 4))
            
            if not is_not_opening:
                continue
                
            # 3. Liquidity (Average Volume)
            avg_volume_20d = hist_data['成交量'].tail(20).mean()

            eligible_stocks.append({
                "code": code,
                "name": name,
                "latest_price": latest_price,
                "avg_volume_20d": avg_volume_20d,
                "latest_bandwidth": hist_data['bandwidth'].iloc[-1]
            })

        except Exception:
            # Silently ignore errors for individual stocks
            continue
            
    print(f"\nFound {len(eligible_stocks)} stocks meeting the criteria.")
    
    # Sort by average volume to find the most liquid ones
    sorted_stocks = sorted(eligible_stocks, key=lambda x: x['avg_volume_20d'], reverse=True)
    
    # Select top 5
    top_5_stocks = sorted_stocks[:5]
    
    return top_5_stocks

def save_results(stocks):
    """Saves the list of stocks to 002.md in a formatted table."""
    output_path = 'git006/002.md'
    print(f"Saving results to {output_path}...")
    
    if not stocks:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 科创板低位低波标的筛选结果\n\n")
            f.write("根据筛选标准，未找到符合条件的股票。\n")
        print("No eligible stocks found.")
        return

    # Create a pandas DataFrame for pretty formatting
    df = pd.DataFrame(stocks)
    df = df[['code', 'name', 'latest_price', 'latest_bandwidth', 'avg_volume_20d']]
    df.rename(columns={
        'code': '股票代码',
        'name': '股票名称',
        'latest_price': '最新价格 (元)',
        'latest_bandwidth': '最新布林带带宽 (%)',
        'avg_volume_20d': '20日平均成交量 (股)'
    }, inplace=True)

    # Format bandwidth to percentage
    df['最新布林带带宽 (%)'] = df['最新布林带带宽 (%)'].apply(lambda x: f"{x:.2%}")
    df['20日平均成交量 (股)'] = df['20日平均成交量 (股)'].apply(lambda x: f"{int(x):,}")


    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 科创板低位低波标的筛选结果\n\n")
        f.write("筛选标准：\n")
        f.write("1. 最新价格 < 50元\n")
        f.write("2. 近3个交易日布林带未开口 (带宽未扩大)\n")
        f.write("3. 按20日平均成交量降序排列\n\n")
        f.write(df.to_markdown(index=False))

    print("Results saved successfully.")
    print("\n--- 筛选结果 ---")
    print(df.to_string(index=False))
    print("--------------------")


if __name__ == "__main__":
    top_stocks = screen_stocks()
    save_results(top_stocks)
