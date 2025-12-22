
import akshare as ak
import pandas as pd
import os
import itertools
from datetime import datetime, timedelta

def get_stock_data(stock_code, days):
    """
    获取指定股票最近N天的历史交易数据。
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days * 1.5) # 获取更长周期以确保足够交易日
    
    end_date_str = end_date.strftime('%Y%m%d')
    start_date_str = start_date.strftime('%Y%m%d')

    try:
        # 使用 akshare 获取数据
        stock_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date_str, end_date=end_date_str, adjust="qfq")
        if stock_df.empty:
            print(f"未能获取到股票 {stock_code} 的数据。")
            return None
        # akshare 返回的数据日期是升序，我们保持这个顺序
        # 截取最近90个交易日
        stock_df = stock_df.tail(days)
        stock_df.reset_index(inplace=True, drop=True)
        return stock_df
    except Exception as e:
        print(f"获取股票 {stock_code} 数据时出错: {e}")
        return None

def analyze_macd_backtest(df, fast_period, slow_period, signal_period):
    """
    对给定的参数组合进行MACD回测，并计算成功率。
    """
    if slow_period <= fast_period:
        return 0, 0, 0, [] # 参数无效

    # 计算 MACD
    df['ema_fast'] = df['收盘'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['收盘'].ewm(span=slow_period, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal']

    # 寻找金叉和死叉信号
    df['prev_macd'] = df['macd'].shift(1)
    df['prev_signal'] = df['signal'].shift(1)

    # 金叉：MACD 从下方上穿信号线
    buy_signals = df[(df['macd'] > df['signal']) & (df['prev_macd'] <= df['prev_signal'])]
    # 死叉：MACD 从上方下穿信号线
    sell_signals = df[(df['macd'] < df['signal']) & (df['prev_macd'] >= df['prev_signal'])]

    # 简单回测
    trades = []
    last_buy_price = None

    for index, row in df.iterrows():
        is_buy_signal = (row['macd'] > row['signal']) and (row['prev_macd'] <= row['prev_signal'])
        is_sell_signal = (row['macd'] < row['signal']) and (row['prev_macd'] >= row['prev_signal'])

        if last_buy_price is None and is_buy_signal:
            last_buy_price = row['收盘']
            trades.append({'buy_date': row['日期'], 'buy_price': last_buy_price})
        elif last_buy_price is not None and is_sell_signal:
            sell_price = row['收盘']
            trade = trades[-1]
            trade['sell_date'] = row['日期']
            trade['sell_price'] = sell_price
            trade['profit'] = sell_price - last_buy_price
            last_buy_price = None

    if not trades:
        return 0, 0, 0, []

    # 最后一个交易如果是未平仓状态，则不计入
    if 'sell_price' not in trades[-1]:
        trades.pop()

    if not trades:
        return 0, 0, 0, []

    successful_trades = sum(1 for trade in trades if trade['profit'] > 0)
    total_trades = len(trades)
    success_rate = (successful_trades / total_trades) if total_trades > 0 else 0
    
    return success_rate, successful_trades, total_trades, trades

def find_best_macd_params(df):
    """
    寻找成功率超过85%的最佳MACD参数组合。
    """
    # 定义参数搜索范围
    fast_periods = range(5, 21, 3) # 5, 8, 11, 14, 17, 20
    slow_periods = range(20, 41, 4) # 20, 24, 28, 32, 36, 40
    signal_periods = range(5, 16, 2) # 5, 7, 9, 11, 13, 15

    best_params = None
    best_rate = 0
    
    param_combinations = list(itertools.product(fast_periods, slow_periods, signal_periods))
    
    print(f"开始搜索MACD参数，共 {len(param_combinations)} 种组合...")

    for fast, slow, signal in param_combinations:
        if slow <= fast:
            continue
            
        rate, _, _, _ = analyze_macd_backtest(df.copy(), fast, slow, signal)
        
        if rate > best_rate:
            best_rate = rate
            best_params = (fast, slow, signal)
            
        if rate >= 0.85:
            print(f"找到成功率 >= 85% 的参数: {best_params}, 成功率: {best_rate:.2%}")
            return best_params, best_rate

    print(f"未找到成功率达到85%的参数，返回找到的最佳组合。")
    return best_params, best_rate


if __name__ == "__main__":
    STOCK_CODE = "688027"
    DATA_DAYS = 90
    OUTPUT_DIR = "out"

    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"创建目录: {OUTPUT_DIR}")

    # 1. 获取数据
    print(f"正在获取股票 {STOCK_CODE} 最近 {DATA_DAYS} 天的交易数据...")
    stock_data = get_stock_data(STOCK_CODE, DATA_DAYS)

    if stock_data is not None:
        # 2. 保存原始数据
        data_path = os.path.join(OUTPUT_DIR, f"{STOCK_CODE}_stock_data.csv")
        stock_data.to_csv(data_path, index=False, encoding='utf-8-sig')
        print(f"原始数据已保存到: {data_path}")

        # 3. 分析并寻找最佳MACD参数
        best_params, best_rate = find_best_macd_params(stock_data.copy())
        
        # 4. 保存分析报告
        report_path = os.path.join(OUTPUT_DIR, "macd_analysis_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"MACD 参数分析报告 - 股票代码: {STOCK_CODE}\n")
            f.write(f"分析周期: 最近 {DATA_DAYS} 个交易日\n")
            f.write("-" * 30 + "\n\n")

            if best_params:
                f.write(f"找到的最佳参数组合 (fast, slow, signal): {best_params}\n")
                f.write(f"在此参数下的回测成功率: {best_rate:.2%}\n\n")
                
                # 使用最佳参数重新获取交易详情并写入报告
                _, successful_trades, total_trades, trades = analyze_macd_backtest(stock_data.copy(), best_params[0], best_params[1], best_params[2])
                
                f.write(f"回测交易详情 (共 {total_trades} 笔交易, 成功 {successful_trades} 笔):\n")
                if trades:
                    for i, trade in enumerate(trades):
                        profit_str = f"{trade['profit']:.2f}"
                        status = "盈利" if trade['profit'] > 0 else "亏损"
                        f.write(f"  交易 {i+1}: \n")
                        f.write(f"    买入: {trade['buy_date']} @ {trade['buy_price']}\n")
                        f.write(f"    卖出: {trade['sell_date']} @ {trade['sell_price']}\n")
                        f.write(f"    盈亏: {profit_str} ({status})\n")
                else:
                    f.write("在回测期间未发现完整的买卖交易。\n")

            else:
                f.write("在指定的参数范围内未能找到任何可以产生交易的MACD组合。\n")

        print(f"分析报告已保存到: {report_path}")

    else:
        print("由于数据获取失败，无法进行分析。")
