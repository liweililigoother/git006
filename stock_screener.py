
import pandas as pd
import pandas_ta as ta
import akshare as ak
from tqdm import tqdm
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def screen_stocks():
    """
    Finds the 5 STAR Market stocks with the lowest 20-day average Bollinger Bandwidth
    that are also under 50 RMB, using an iterative "king-of-the-hill" search.
    """
    print("Fetching list of STAR Market (科创板) stocks...")
    try:
        stock_list = ak.stock_kc_a_spot_em()
    except Exception as e:
        print(f"Error fetching stock list: {e}")
        return []

    print(f"Found {len(stock_list)} stocks. Starting iterative screening process...")
    
    leaderboard = [] # This will hold the top 5 stocks
    
    for index, row in tqdm(stock_list.iterrows(), total=stock_list.shape[0], desc="Screening Stocks"):
        code = row['代码']
        name = row['名称']
        
        try:
            hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20240101", adjust="qfq")
            if hist_data.empty or len(hist_data) < 60:
                continue

            # 1. Price check
            latest_price = hist_data['收盘'].iloc[-1]
            if latest_price >= 50:
                continue

            # 2. Bollinger Bands check
            hist_data.ta.bbands(close='收盘', length=20, append=True)
            
            b_upper_col = 'BBU_20_2.0'
            b_lower_col = 'BBL_20_2.0'
            b_middle_col = 'BBM_20_2.0'

            if not all(col in hist_data.columns for col in [b_upper_col, b_lower_col, b_middle_col]):
                continue

            hist_data['bandwidth'] = (hist_data[b_upper_col] - hist_data[b_lower_col]) / hist_data[b_middle_col]

            last_20_days_bandwidth = hist_data['bandwidth'].tail(20)
            if len(last_20_days_bandwidth) < 20:
                continue
            avg_bandwidth_20d = last_20_days_bandwidth.mean()
            
            # 3. "King of the Hill" logic
            if len(leaderboard) < 5:
                leaderboard.append({
                    "code": code,
                    "name": name,
                    "latest_price": latest_price,
                    "avg_bandwidth_20d": avg_bandwidth_20d
                })
                # Sort leaderboard by bandwidth descending to easily find the max
                leaderboard.sort(key=lambda x: x['avg_bandwidth_20d'], reverse=True)
            else:
                # If current stock is better than the worst on the leaderboard
                if avg_bandwidth_20d < leaderboard[0]['avg_bandwidth_20d']:
                    leaderboard[0] = {
                        "code": code,
                        "name": name,
                        "latest_price": latest_price,
                        "avg_bandwidth_20d": avg_bandwidth_20d
                    }
                    leaderboard.sort(key=lambda x: x['avg_bandwidth_20d'], reverse=True)

        except Exception:
            continue
            
    print(f"\nScreening complete. Found {len(leaderboard)} stocks.")
    
    # Final step: add volume data for the winners
    print("Fetching volume data for the final 5 stocks...")
    for stock in tqdm(leaderboard, desc="Fetching Volume"):
        try:
            hist_data = ak.stock_zh_a_hist(symbol=stock['code'], period="daily", start_date="20240101", adjust="qfq")
            stock['avg_volume_20d'] = hist_data['成交量'].tail(20).mean()
        except Exception:
            stock['avg_volume_20d'] = 0

    # Sort final list for display
    leaderboard.sort(key=lambda x: x['avg_bandwidth_20d'])
    
    return leaderboard

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
    df = df[['code', 'name', 'latest_price', 'avg_bandwidth_20d', 'avg_volume_20d']]
    df.rename(columns={
        'code': '股票代码',
        'name': '股票名称',
        'latest_price': '最新价格 (元)',
        'avg_bandwidth_20d': '近20日平均布林带带宽 (%)',
        'avg_volume_20d': '20日平均成交量 (股)'
    }, inplace=True)


    # Format bandwidth to percentage
    df['近20日平均布林带带宽 (%)'] = df['近20日平均布林带带宽 (%)'].apply(lambda x: f"{x:.2%}")
    df['20日平均成交量 (股)'] = df['20日平均成交量 (股)'].apply(lambda x: f"{int(x):,}")


    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 科创板低位低波标的筛选结果\n\n")
        f.write("筛选标准：\n")
        f.write("1. 最新价格 < 50元\n")
        f.write("2. 遍历所有科创板股票，选取“近20日平均布林带带宽”最低的5支\n\n")
        f.write(df.to_markdown(index=False))

    print("Results saved successfully.")
    print("\n--- 筛选结果 ---")
    print(df.to_string(index=False))
    print("--------------------")


if __name__ == "__main__":
    top_stocks = screen_stocks()
    save_results(top_stocks)
