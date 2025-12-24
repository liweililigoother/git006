import akshare as ak
import pandas as pd
from datetime import datetime
import pytz
import time
import os

# --- 配置 ---
STOCK_CODE = "688027"
TIME_INTERVAL = 120  # 120秒 = 2分钟
RUN_DURATION = 600  # 600秒 = 10分钟
VOLUME_THRESHOLD = 230000000  # 2.3亿
PRICE_FLUCTUATION_THRESHOLD = 3.2
OUTPUT_DIR = "git006/001/output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "NEW.md")

def get_beijing_time():
    """获取当前的北京时间"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

def log_to_file(message):
    """记录信息到Markdown文件"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(message + "\n")

def check_and_log_signals():
    """主循环，获取数据、检查信号并记录"""
    start_time = time.time()
    print(f"[{get_beijing_time()}] 开始监控股票 {STOCK_CODE}，每 {TIME_INTERVAL} 秒刷新一次。")
    print(f"此脚本将在 {RUN_DURATION / 60:.0f} 分钟后自动停止。")
    print(f"触发条件: {TIME_INTERVAL}秒内 交易额 > {VOLUME_THRESHOLD/100000000:.2f}亿 且 价格波动 > {PRICE_FLUCTUATION_THRESHOLD}元")
    print("按 Ctrl+C 停止。")

    # 确保文件存在，如果不存在，创建一个空的
    if not os.path.exists(OUTPUT_FILE):
        log_to_file(f"# {STOCK_CODE} 交易信号监控")
        log_to_file(f"启动时间: {get_beijing_time()}")
        log_to_file("---")

    while True:
        # 检查是否超时
        if time.time() - start_time > RUN_DURATION:
            print(f"[{get_beijing_time()}] 运行达到 {RUN_DURATION / 60:.0f} 分钟，脚本自动停止。")
            break
            
        try:
            print(f"[{get_beijing_time()}] 正在获取 {STOCK_CODE} 的分钟线数据...")
            # 获取最新的1分钟K线数据
            stock_df = ak.stock_zh_a_minute(symbol=STOCK_CODE, period='1', adjust='qfq')
            
            if stock_df.empty or len(stock_df) < 2:
                print("未能获取到足够的数据，等待下一次尝试。")
                # 即便没有数据，也按要求记录
                log_to_file(f"平安无事 | {get_beijing_time()}")
                time.sleep(TIME_INTERVAL)
                continue

            # --- 分析最新的两分钟数据 ---
            last_two_minutes = stock_df.iloc[-2:]
            
            # 计算总交易额 (amount单位是元)
            total_amount = last_two_minutes['amount'].sum()
            
            # 计算价格波动
            price_high = last_two_minutes['high'].max()
            price_low = last_two_minutes['low'].min()
            price_fluctuation = price_high - price_low

            # 价格变化方向 (用最后一分钟的收盘价和第一分钟的开盘价)
            price_change = last_two_minutes.iloc[-1]['close'] - last_two_minutes.iloc[0]['open']

            memory_str = f"两分钟交易额: {total_amount/10000:.2f}万元, 价格波动: {price_fluctuation:.2f}元"

            # --- 信号判断逻辑 ---
            if total_amount >= VOLUME_THRESHOLD and price_fluctuation >= PRICE_FLUCTUATION_THRESHOLD:
                signal = "买入提示" if price_change > 0 else "卖出提示"
                log_message = f"{STOCK_CODE} | {signal} | {get_beijing_time()} | {memory_str}"
                print(f"检测到信号: {log_message}")
                log_to_file(log_message)
            else:
                log_message = f"平安无事 | {get_beijing_time()}"
                print(log_message)
                log_to_file(log_message)

            print(f"[{get_beijing_time()}] 数据处理完毕，等待下一次轮询...")
            
            # 计算下一次运行前需要等待的时间
            elapsed_since_start = time.time() - start_time
            remaining_time = RUN_DURATION - elapsed_since_start
            
            # 如果剩余时间小于一个检查周期，就没必要再等了
            if remaining_time < TIME_INTERVAL:
                time.sleep(max(0, remaining_time)) # 等待剩余时间
            else:
                time.sleep(TIME_INTERVAL)

        except Exception as e:
            error_message = f"发生错误: {e}"
            print(error_message)
            log_to_file(f"错误 | {get_beijing_time()} | {error_message}")
            print(f"等待 {TIME_INTERVAL} 秒后重试...")
            time.sleep(TIME_INTERVAL)


if __name__ == "__main__":
    check_and_log_signals()