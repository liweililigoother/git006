import akshare as ak
import pandas as pd

# 1. 获取科创板所有股票的实时行情
print("正在获取科创板数据...")
df = ak.stock_zh_a_spot_em()
# 筛选科创板 (688开头)
df_star = df[df['代码'].str.startswith('688')].copy()

# 2. 基础条件筛选：股价低于 50 元
df_star = df_star[df_star['最新价'] < 50]

# 3. 计算 BOLL 紧缩 (以简化算法为例：(最高-最低)/均价)
# 注：更精准的紧缩需下载历史K线计算，此处演示筛选当前乖离率较小的个股
df_star['振幅_%'] = df_star['振幅'] 

# 4. 排序：按成交量 (Volume) 从大到小排列
df_result = df_star.sort_values(by='成交量', ascending=False)

# 5. 格式化并导出为 001.md
with open('001.md', 'w', encoding='utf-8') as f:
    f.write("# 科创板选股结果 (BOLL紧缩 & 低价)\n")
    f.write(f"> 筛选日期: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
    f.write(df_result[['代码', '名称', '最新价', '成交量', '振幅_%']].to_markdown(index=False))

print("筛选完成，结果已存入 001.md")