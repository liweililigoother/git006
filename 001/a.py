import akshare as ak
import pandas as pd
import mplfinance as mpf
from datetime import datetime, timedelta
import os
import argparse

def get_stock_data_combined(stock_code="688027", days=200):
    """
    获取最近N个交易日的日线数据，并合并所有这些天的5分钟线数据到一个DataFrame。
    """
    print(f"开始获取股票代码 {stock_code} 的最近 {days} 个交易日数据...")
    
    # 根据股票代码前缀判断是上海还是深圳股票，并添加相应前缀
    if stock_code.startswith('0') or stock_code.startswith('3'):
        prefixed_stock_code = f"sz{stock_code}"
    elif stock_code.startswith('6'):
        prefixed_stock_code = f"sh{stock_code}"
    else:
        prefixed_stock_code = stock_code # 保持不变，可能是其他类型代码或已带前缀
    
    try:
        # 使用 stock_zh_a_minute 获取所有可用的5分钟数据
        all_5min_data_df = ak.stock_zh_a_minute(symbol=prefixed_stock_code, period="5", adjust="qfq")
        
        if all_5min_data_df.empty:
            print("未能获取到任何5分钟数据，请检查股票代码或网络。")
            return None
        
        # 将 'day' 列转换为 datetime 对象
        all_5min_data_df['datetime'] = pd.to_datetime(all_5min_data_df['day'])
        
        # 提取日期部分，并获取唯一的交易日
        all_5min_data_df['date'] = all_5min_data_df['datetime'].dt.date
        unique_trading_dates = sorted(all_5min_data_df['date'].unique(), reverse=True)
        
        if len(unique_trading_dates) < days:
            print(f"警告: 只能获取到 {len(unique_trading_dates)} 个交易日的5分钟数据，少于请求的 {days} 天。")
        
        # 筛选出最近 days 个交易日的数据
        recent_trading_dates = unique_trading_dates[:days]
        combined_df = all_5min_data_df[all_5min_data_df['date'].isin(recent_trading_dates)].copy()
        
        if combined_df.empty:
            print(f"未能从最近 {days} 个交易日中获取到有效数据。")
            return None
            
        # 将列名统一为mplfinance需要的格式
        combined_df.rename(columns={'开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'}, inplace=True)
        
        # 确保数据类型正确
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
        combined_df.dropna(subset=numeric_cols, inplace=True) # 移除转换失败的行
        
        # 移除辅助的 'date' 列
        combined_df.drop(columns=['date'], inplace=True)        
        print(f"成功获取并筛选到 {len(recent_trading_dates)} 个交易日的5分钟数据。")
        return combined_df

    except Exception as e:
        print(f"获取5分钟数据时发生严重错误: {e}")
        return None

def save_data_to_csv(df, file_path):
    """将所有数据保存到单个CSV文件中。"""
    print(f"正在将所有数据保存到: {file_path}")
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print("数据保存完毕。")

def generate_candlestick_charts(df, stock_code, output_dir):
    """为每个交易日生成5分钟K线图。"""
    print(f"开始为每个交易日生成K线图，保存至 '{output_dir}' 目录...")
    if df.empty or 'datetime' not in df.columns:
        print("DataFrame为空或缺少'datetime'列，无法生成图表。")
        return
        
    df_indexed = df.set_index('datetime')
    
    # 按天分组
    daily_groups = df_indexed.groupby(pd.Grouper(freq='D'))
    
    for group_name, group_df in daily_groups:
        if group_df.empty:
            continue
            
        day_str = group_name.strftime('%Y-%m-%d')
        chart_file = os.path.join(output_dir, f"{day_str}.png")
        
        print(f"  - 正在生成 {day_str} 的图表...")
        
        # 使用mplfinance绘制K线图
        mpf.plot(group_df, 
                 type='candle', 
                 style='charles',
                 title=f'{stock_code} 5-Min Data - {day_str}',
                 ylabel='Price',
                 ylabel_lower='Volume',
                 volume=True, 
                 mav=(5, 10), # 5周期和10周期移动平均线
                 savefig=chart_file)
    
    print("所有图表生成完毕。")

def main():
    parser = argparse.ArgumentParser(description="获取股票数据，保存并生成图表。")
    parser.add_argument("--stock_code", type=str, default="688027", help="股票代码")
    # 固定的天数以满足需求，但保留参数以便未来灵活使用
    parser.add_argument("--days", type=int, default=200, help="获取最近的交易天数")
    args = parser.parse_args()

    # 1. 获取最近200个交易日的所有5分钟数据
    combined_data = get_stock_data_combined(args.stock_code, args.days)

    if combined_data is not None and not combined_data.empty:
        # 定义输出路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "output", args.stock_code)
        os.makedirs(output_dir, exist_ok=True)
        
        csv_file_path = os.path.join(output_dir, "all_stock_data.csv")

        # 2. 所有数据存入同一文件
        save_data_to_csv(combined_data, csv_file_path)

        # 3. 生成每个交易日的五分钟柱状图
        generate_candlestick_charts(combined_data, args.stock_code, output_dir)
    else:
        print("未能获取到有效数据，程序退出。")

    print("\n所有任务已完成。")

if __name__ == "__main__":
    main()
