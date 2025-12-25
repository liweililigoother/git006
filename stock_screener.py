
import pandas as pd
import pandas_ta as ta
import akshare as ak
from tqdm import tqdm
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def screen_stocks():
    """
    Finds the first 5 STAR Market stocks with a price under 50.
    Fetches average volume for display purposes only.
    """
    print("Fetching list of all STAR Market (科创板) stocks with current prices...")
    try:
        # Get all STAR Market stocks with spot data (much faster)
        spot_data = ak.stock_kc_a_spot_em()
        # Rename columns to be consistent
        spot_data.rename(columns={'最新价': 'price', '代码': 'code', '名称': 'name'}, inplace=True)
    except Exception as e:
        print(f"Error fetching stock list: {e}")
        return []

    # Filter by price
    under_50 = spot_data[spot_data['price'] < 50]
    
    print(f"Found {len(under_50)} stocks under 50 RMB. Taking the first 5.")
    
    # Take the first 5 stocks
    top_5_raw = under_50.head(5)
    
    if top_5_raw.empty:
        return []
        
    eligible_stocks = []
    print("Fetching historical data for the top 5 to get average volume...")
    
    for index, row in tqdm(top_5_raw.iterrows(), total=top_5_raw.shape[0], desc="Fetching Volume"):
        code = row['code']
        name = row['name']
        latest_price = row['price']
        
        try:
            # Fetch historical data ONLY for these 5 stocks
            hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20240101", adjust="qfq")
            if hist_data.empty or len(hist_data) < 20:
                avg_volume_20d = 0
            else:
                avg_volume_20d = hist_data['成交量'].tail(20).mean()
        except Exception:
            avg_volume_20d = 0 # Default to 0 if history fetch fails

        eligible_stocks.append({
            "code": code,
            "name": name,
            "latest_price": latest_price,
            "avg_volume_20d": avg_volume_20d
        })
            
    return eligible_stocks

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
    df = df[['code', 'name', 'latest_price', 'avg_volume_20d']]
    df.rename(columns={
        'code': '股票代码',
        'name': '股票名称',
        'latest_price': '最新价格 (元)',
        'avg_volume_20d': '20日平均成交量 (股)'
    }, inplace=True)


    df['20日平均成交量 (股)'] = df['20日平均成交量 (股)'].apply(lambda x: f"{int(x):,}")


    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 科创板低位低波标的筛选结果\n\n")
        f.write("筛选标准：\n")
        f.write("1. 最新价格 < 50元\n")
        f.write("2. 选取符合条件的前5支股票 (不进行成交量比较)\n\n")
        f.write(df.to_markdown(index=False))

    print("Results saved successfully.")
    print("\n--- 筛选结果 ---")
    print(df.to_string(index=False))
    print("--------------------")


if __name__ == "__main__":
    top_stocks = screen_stocks()
    save_results(top_stocks)
