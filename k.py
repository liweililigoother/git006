import akshare as ak
import pandas as pd
import pandas_ta as ta

# Function to calculate Bollinger Band widening
def calculate_bollinger_widening(stock_code, period=20, lookback=10):
    try:
        # 获取股票历史K线数据
        # akshare 的 stock_zh_a_hist 默认返回的列名是中文，需要调整
        df_hist = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date="20000101", end_date=pd.Timestamp.now().strftime("%Y%m%d"))
        if df_hist.empty or len(df_hist) < period + lookback:
            return None, None

        # 重命名列以符合 pandas_ta 预期
        df_hist.rename(columns={
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        }, inplace=True)

        # 计算布林带
        df_hist.ta.bbands(close='close', length=period, append=True)

        # 检查布林带相关列是否存在
        if f'BBL_{period}' not in df_hist.columns or f'BBU_{period}' not in df_hist.columns:
            return None, None

        # 计算布林带宽
        df_hist['BB_Bandwidth'] = df_hist[f'BBU_{period}'] - df_hist[f'BBL_{period}']

        # 计算最近lookback天的带宽平均值和前lookback天的带宽平均值
        if len(df_hist) < lookback * 2: # 需要至少2倍的lookback期来做比较
            return None, None
            
        recent_bandwidth_avg = df_hist['BB_Bandwidth'].tail(lookback).mean()
        previous_bandwidth_avg = df_hist['BB_Bandwidth'].iloc[-(lookback*2):-lookback].mean()

        if previous_bandwidth_avg == 0: # 避免除零
            return None, None
            
        # 简单判断是否“明显放大”：近期平均带宽是否大于前期平均带宽的某个百分比
        # 这里的判断可以根据实际需求调整
        widening_ratio = (recent_bandwidth_avg - previous_bandwidth_avg) / previous_bandwidth_avg
        
        # 返回最近的带宽和放大比例，用于排序
        return df_hist['BB_Bandwidth'].iloc[-1], widening_ratio

    except Exception as e:
        print(f"处理股票 {stock_code} 时发生错误: {e}")
        return None, None

# 1. 获取科创板所有股票的实时行情
print("正在获取科创板数据...")
df = ak.stock_zh_a_spot_em()
# 筛选科创板 (688开头)
df_star = df[df['代码'].str.startswith('688')].copy()

# 2. 基础条件筛选：股价低于 50 元
df_star = df_star[df_star['最新价'] < 50]

# 3. 计算 BOLL 紧缩 (以简化算法为例：(最高-最低)/均价)
# 注：更精准的紧缩需下载历史K线计算，此处演示筛选当前乖离率较小的个股
# 这里可以继续使用振幅_% 或者更新为基于布林带的紧缩指标
df_star['振幅_%'] = df_star['振幅']

# 准备存储布林带信息的新列
df_star['BB_Current_Bandwidth'] = None
df_star['BB_Widening_Ratio'] = None

print("正在计算布林带开口放大情况，这可能需要一些时间...")
for index, row in df_star.iterrows():
    stock_code = row['代码']
    current_bandwidth, widening_ratio = calculate_bollinger_widening(stock_code)
    df_star.loc[index, 'BB_Current_Bandwidth'] = current_bandwidth
    df_star.loc[index, 'BB_Widening_Ratio'] = widening_ratio

# 过滤掉无法计算布林带的股票
df_star.dropna(subset=['BB_Current_Bandwidth', 'BB_Widening_Ratio'], inplace=True)

# 4. 排序：按布林开口放大比例从大到小排列，其次按当前带宽从小到大 (更紧缩)
# 可以根据需求调整排序优先级
df_result = df_star.sort_values(by=['BB_Widening_Ratio', 'BB_Current_Bandwidth'], ascending=[False, True])

# 5. 格式化并导出为 001.md
with open('001.md', 'w', encoding='utf-8') as f:
    f.write("# 科创板选股结果 (BOLL开口放大 & 低价)\n")
    f.write(f"> 筛选日期: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
    f.write(df_result[['代码', '名称', '最新价', '成交量', '振幅_%', 'BB_Current_Bandwidth', 'BB_Widening_Ratio']].to_markdown(index=False))

print("筛选完成，结果已存入 001.md")
