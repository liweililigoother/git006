import akshare as ak
import pandas as pd
import pandas_ta as ta
from datetime import datetime, time, timedelta
import pytz
import os
import time as time_module

# --- 配置 ---
STOCK_CODE = "688027"
TIME_INTERVAL = 120  # 120秒 = 2分钟
RUN_DURATION = 15  # 600秒 = 10分钟
OUTPUT_DIR = "git006/001/output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "NEW.md")

# 量价信号配置
VOLUME_THRESHOLD = 230000000  # 2.3亿
PRICE_FLUCTUATION_THRESHOLD = 3.2

# 技术指标配置
# MACD 参数
MACD_FAST = 5
MACD_SLOW = 20
MACD_SIGNAL = 9
# KDJ 参数
KDJ_N = 9
KDJ_M1 = 3
KDJ_M2 = 3
# KDJ 超买超卖阈值 (根据用户输入 kdj(20.80) 理解)
KDJ_OVERSOLD = 20
KDJ_OVERBOUGHT = 80


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

def print_and_log(message):
    """打印信息到控制台并记录到文件"""
    print(message)
    log_to_file(message)

def is_trading_time():
    """判断当前是否为A股交易时间（北京时间）。
    上午 09:30 - 11:30
    下午 13:00 - 15:00
    """
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    current_time = now.time()

    # 检查是否在交易日（周一到周五）
    # 0=Monday, 5=Saturday, 6=Sunday
    if now.weekday() >= 5:
        return False

    # 上午交易时间
    am_start = datetime.time(9, 30)
    am_end = datetime.time(11, 30)
    # 下午交易时间
    pm_start = datetime.time(13, 0)
    pm_end = datetime.time(15, 0)

    # 检查是否在交易时间段内
    if (current_time >= am_start and current_time < am_end) or \
       (current_time >= pm_start and current_time < pm_end):
        return True
    return False

def check_and_log_signals():
    """主循环，获取数据、检查信号并记录"""
    start_time = time_module.time()
    print_and_log(f"[{get_beijing_time()}] 开始监控股票 {STOCK_CODE}，每 {TIME_INTERVAL} 秒刷新一次。")
    print_and_log(f"此脚本将在 {RUN_DURATION / 60:.0f} 分钟后自动停止。")
    print_and_log("按 Ctrl+C 停止。\n")

    if not os.path.exists(OUTPUT_FILE):
        log_to_file(f"# {STOCK_CODE} 交易信号监控 (混合模式)")
        log_to_file(f"启动时间: {get_beijing_time()}")
        log_to_file("---")

    while True:
        if time_module.time() - start_time > RUN_DURATION:
            print_and_log(f"[{get_beijing_time()}] 运行达到 {RUN_DURATION / 60:.0f} 分钟，脚本自动停止。")
            break
        
        if not is_trading_time():
            message = f"[{get_beijing_time()}] 非交易时间，平安无事。等待交易时间..."
            print_and_log(message)
            
            tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(tz)
            
            next_trading_start = None
            if now.time() < datetime.time(9, 30):
                next_trading_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
            elif now.time() < datetime.time(13, 0):
                next_trading_start = now.replace(hour=13, minute=0, second=0, microsecond=0)
            else:
                days_until_monday = (7 - now.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                next_trading_start = (now + timedelta(days=days_until_monday)).replace(hour=9, minute=30, second=0, microsecond=0)

            sleep_duration = (next_trading_start - now).total_seconds()
            if sleep_duration > 0:
                print_and_log(f"[{get_beijing_time()}] 预计等待 {sleep_duration / 60:.1f} 分钟直到下一个交易时间...")
                time_module.sleep(sleep_duration)
            else:
                time_module.sleep(60)
            continue

        try:
            print_and_log(f"[{get_beijing_time()}] 正在获取 {STOCK_CODE} 的分钟线数据...")
            stock_df_raw = ak.stock_zh_a_minute(symbol=STOCK_CODE, period='1', adjust='qfq')
            
            if stock_df_raw.empty or len(stock_df_raw) < 2:
                print_and_log("未获取到股票数据或数据量不足，可能是股票代码错误或已退市。2分钟后将再次尝试读取。")
                time.sleep(TIME_INTERVAL)
                continue

            signal_found = False

            # --- 1. 量价信号检查 ---
            last_two_minutes = stock_df_raw.iloc[-2:]
            total_amount = last_two_minutes['amount'].sum()
            price_high = last_two_minutes['high'].max()
            price_low = last_two_minutes['low'].min()
            price_fluctuation = price_high - price_low
            price_change = last_two_minutes.iloc[-1]['close'] - last_two_minutes.iloc[0]['open']

            if total_amount >= VOLUME_THRESHOLD and price_fluctuation >= PRICE_FLUCTUATION_THRESHOLD:
                signal = "买入提示" if price_change > 0 else "卖出提示"
                memory_str = f"两分钟交易额: {total_amount/10000:.2f}万元, 价格波动: {price_fluctuation:.2f}元"
                log_message = f"{STOCK_CODE} | {signal} | {get_beijing_time()} | {memory_str}"
                print_and_log(f"检测到量价信号: {log_message}")
                signal_found = True

            # --- 2. 技术指标信号检查 (MACD & KDJ) ---
            stock_df_tech = stock_df_raw.copy()
            stock_df_tech.ta.macd(fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL, append=True)
            stock_df_tech.ta.kdj(n=KDJ_N, m1=KDJ_M1, m2=KDJ_M2, append=True)
            stock_df_tech.dropna(inplace=True)

            if len(stock_df_tech) >= 2:
                latest = stock_df_tech.iloc[-1]
                previous = stock_df_tech.iloc[-2]

                macd_dif_latest = latest[f'MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']
                macd_dea_latest = latest[f'MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']
                macd_dif_previous = previous[f'MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']
                macd_dea_previous = previous[f'MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']

                k_latest = latest[f'K_{KDJ_N}_{KDJ_M1}_{KDJ_M2}']
                d_latest = latest[f'D_{KDJ_N}_{KDJ_M1}_{KDJ_M2}']
                k_previous = previous[f'K_{KDJ_N}_{KDJ_M1}_{KDJ_M2}']
                d_previous = previous[f'D_{KDJ_N}_{KDJ_M1}_{KDJ_M2}']

                macd_buy = macd_dif_previous < macd_dea_previous and macd_dif_latest > macd_dea_latest
                kdj_buy = k_previous < d_previous and k_latest > d_latest and k_latest < KDJ_OVERBOUGHT

                if macd_buy and kdj_buy:
                    log_message = f"{STOCK_CODE} | 买入提示 | {get_beijing_time()} | ma"
                    print_and_log(f"检测到MA信号: {log_message}")
                    signal_found = True

                macd_sell = macd_dif_previous > macd_dea_previous and macd_dif_latest < macd_dea_latest
                kdj_sell = k_previous > d_previous and k_latest < d_latest and k_latest > KDJ_OVERSOLD

                if macd_sell and kdj_sell:
                    log_message = f"{STOCK_CODE} | 卖出提示 | {get_beijing_time()} | ma"
                    print_and_log(f"检测到MA信号: {log_message}")
                    signal_found = True
            
            # --- 3. 无信号则记录平安 ---
            if not signal_found:
                log_message = f"平安无事 | {get_beijing_time()}"
                print_and_log(log_message)

            print_and_log(f"[{get_beijing_time()}] 数据处理完毕，等待下一次轮询...")
            
            elapsed_since_start = time_module.time() - start_time
            remaining_time = RUN_DURATION - elapsed_since_start
            
            if remaining_time < TIME_INTERVAL:
                time.sleep(max(0, remaining_time))
            else:
                time.sleep(TIME_INTERVAL)

        except Exception as e:
            error_message = f"发生错误: {e}"
            print_and_log(error_message)
            print_and_log(f"等待 {TIME_INTERVAL} 秒后重试...")
            time.sleep(TIME_INTERVAL)

if __name__ == "__main__":
    check_and_log_signals()