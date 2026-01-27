# stock_workstation/app.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px # For heatmap

# Import functions from data_connector, feature_engineering, similarity_analysis, and mock_data
from data_connector import get_past_n_trading_days_data, get_minute_data
from feature_engineering import calculate_bidding_strength, calculate_efficiency_before_10am, detect_moat_support
from similarity_analysis import find_historical_twin_days
from mock_data import generate_mock_minute_data

st.set_page_config(layout="wide")
st.title("A股688027定制化特征点监控与回测工作站")

# Sidebar for user input
st.sidebar.header("参数设置")
stock_symbol = st.sidebar.text_input("股票代码", "688027")
n_historical_days = st.sidebar.number_input("历史数据天数 (用于竞价强弱度、DTW)", 1, 40, 5) # Increased to 5 for better DTW

use_mock_data = st.sidebar.checkbox("使用模拟数据 (用于演示)", value=False)

# Define constants from the problem description
PULLBACK_TARGET = 592.00
COST_PRICE = 579.00
GOLDEN_PIT_RANGE = (578, 580)


# Main application logic
st.header(f"股票: {stock_symbol}")

# --- Data Acquisition ---
st.subheader("1. 环境与数据接入")

if use_mock_data:
    st.info("已启用模拟数据。")
    # For mock data, let's generate some for 'today' and some 'historical'
    today_date = datetime.now()
    current_day_data_for_features = generate_mock_minute_data(start_price=579.5, date=today_date)
    
    historical_data = {}
    for i in range(n_historical_days):
        hist_date = today_date - timedelta(days=i+1)
        historical_data[hist_date.strftime('%Y-%m-%d')] = generate_mock_minute_data(start_price=580 + (i%3)*2 - 1, date=hist_date)
    st.success(f"生成了 {len(historical_data)} 个历史模拟数据和今日模拟数据。")
    st.dataframe(current_day_data_for_features.head())

else:
    @st.cache_data(ttl=3600) # Cache for 1 hour
    def fetch_data(symbol, days):
        with st.spinner(f"正在获取 {symbol} 过去 {days} 个交易日的分钟级数据..."):
            return get_past_n_trading_days_data(symbol, days)

    historical_data_raw = fetch_data(stock_symbol, n_historical_days + 1) # +1 to ensure current_day_data_for_features can be derived

    if historical_data_raw:
        st.success(f"成功获取 {len(historical_data_raw)} 个交易日的数据。")
        
        # Split into current day's data and historical data for DTW
        sorted_dates = sorted(historical_data_raw.keys())
        last_trading_day_str = sorted_dates[-1]
        
        current_day_data_for_features = historical_data_raw[last_trading_day_str]
        historical_data = {date: df for date, df in historical_data_raw.items() if date != last_trading_day_str}

        st.write(f"用于特征计算的当前日数据（取自最新交易日 {last_trading_day_str}）:")
        st.dataframe(current_day_data_for_features.head())
        st.write("已获取的历史数据日期:", list(historical_data.keys()))

    else:
        st.warning("未能获取历史数据，请检查股票代码或网络连接。请尝试使用模拟数据。")
        current_day_data_for_features = pd.DataFrame() # Ensure it's empty if no data
        historical_data = {}


# --- Feature Engineering ---
st.subheader("2. 核心特征算法")
if not current_day_data_for_features.empty and historical_data:
    bidding_strength = calculate_bidding_strength(current_day_data_for_features, historical_data)
    efficiency_before_10am = calculate_efficiency_before_10am(current_day_data_for_features)
    moat_support_detected = detect_moat_support(current_day_data_for_features, golden_pit_range=GOLDEN_PIT_RANGE)

    st.metric("竞价强弱度", f"{bidding_strength:.2f}")
    st.metric("10点前效率", f"{efficiency_before_10am:.4f}")
    st.metric("护城河支撑检测", "检测到" if moat_support_detected else "未检测到")
else:
    st.info("数据不足，无法计算特征指标。")

# --- Real-time Graphical Dashboard ---
st.subheader("3. 实时图形化仪表盘")

pullback_probability = st.slider("模拟回抽概率 (%)", 0, 100, 75) / 100.0 # User can adjust for demo

col1, col2 = st.columns(2)

with col1:
    st.write("#### 今日回抽目标位预测")
    fig_indicator = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = pullback_probability * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"目标 {PULLBACK_TARGET:.2f} 概率"},
        gauge = {'axis': {'range': [None, 100]},
                 'steps' : [
                     {'range': [0, 50], 'color': "lightgray"},
                     {'range': [50, 80], 'color': "gray"}],
                 'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 80}}))
    st.plotly_chart(fig_indicator, use_container_width=True)

with col2:
    st.write("#### 动态压力带")
    if not current_day_data_for_features.empty:
        latest_price = current_day_data_for_features['收盘'].iloc[-1]
        is_above_cost = latest_price > COST_PRICE
        
        strong_buying_pressure = detect_moat_support(current_day_data_for_features, golden_pit_range=GOLDEN_PIT_RANGE, high_volume_threshold=0.8)
        
        pressure_band_color = "red"
        status_message = f"当前价格: {latest_price:.2f}"
        
        if is_above_cost and strong_buying_pressure:
            pressure_band_color = "green"
            status_message += " (绿色护城河: 价格在成本之上且买盘强劲)"
        elif is_above_cost:
            pressure_band_color = "orange"
            status_message += " (价格在成本之上，但买盘强度未知)"
        else:
            pressure_band_color = "red"
            status_message += f" (红色警告: 价格跌破成本 {COST_PRICE:.2f})"


        st.markdown(f"""
        <div style="background-color:{pressure_band_color}; padding: 10px; border-radius: 5px; color: white;">
            <p style="font-size: 20px; font-weight: bold;">成本价压力带: {COST_PRICE:.2f}</p>
            <p style="font-size: 18px;">{status_message}</p>
        </div>
        """, unsafe_allow_html=True)

        fig_price_chart = go.Figure()
        fig_price_chart.add_trace(go.Scatter(x=current_day_data_for_features['时间'], 
                                             y=current_day_data_for_features['收盘'],
                                             mode='lines', name='收盘价'))
        fig_price_chart.add_hline(y=COST_PRICE, line_dash="dot", line_color="red", annotation_text=f"成本价: {COST_PRICE:.2f}")
        
        fig_price_chart.add_hrect(y0=GOLDEN_PIT_RANGE[0], y1=GOLDEN_PIT_RANGE[1], 
                                  line_width=0, fillcolor="gold", opacity=0.2,
                                  annotation_text="黄金坑", annotation_position="top left")

        fig_price_chart.update_layout(title="分钟价格走势与压力带", xaxis_title="时间", yaxis_title="价格")
        st.plotly_chart(fig_price_chart, use_container_width=True)


    else:
        st.info("没有当前日数据来绘制动态压力带。")


# --- Advanced Similarity Analysis ---
st.subheader("4. 高级相似度分析")
if not current_day_data_for_features.empty and historical_data:
    current_day_series = current_day_data_for_features['收盘']
    twin_days = find_historical_twin_days(current_day_series, historical_data, top_n=3)

    if twin_days:
        st.write("#### 识别到的历史“孪生日”走势:")
        # Prepare data for heatmap
        heatmap_data = []
        for date, df in twin_days.items():
            # Assume '后续走势' implies the full historical minute data (09:15-10:00)
            # For a true "heatmap of subsequent trends," we'd need data *after* 10:00,
            # which we haven't fetched explicitly. For now, we'll plot the 09:15-10:00.
            # A more complete solution would fetch a wider range for historical days.
            
            # Pad or truncate historical series to match current day series length for heatmap alignment
            # This is a simplification; a better approach for DTW visualization might be different
            
            # For simplicity, just show the similar 09:15-10:00 segment for now
            # and potentially the next X minutes if available (but not currently fetched by data_connector)
            df_plot = df.set_index('时间')['收盘'].resample('1T').mean().dropna().reset_index()
            df_plot['时间'] = df_plot['时间'].dt.time.astype(str) # Convert time to string for x-axis
            df_plot['日期'] = date
            heatmap_data.append(df_plot)
        
        if heatmap_data:
            combined_df = pd.concat(heatmap_data)
            
            # Pivot the table for heatmap
            pivot_df = combined_df.pivot_table(index='日期', columns='时间', values='收盘')

            fig_heatmap = px.imshow(pivot_df, 
                                    x=pivot_df.columns, 
                                    y=pivot_df.index, 
                                    color_continuous_scale='Viridis',
                                    title="历史“孪生日”09:15-10:00价格走势 (热力图)")
            st.plotly_chart(fig_heatmap, use_container_width=True)

            # Display individual charts for twin days for more detail
            for date, df in twin_days.items():
                st.write(f"##### {date} 走势:")
                fig_twin = go.Figure()
                fig_twin.add_trace(go.Scatter(x=df['时间'], y=df['收盘'], mode='lines', name=f'{date} 收盘价'))
                fig_twin.update_layout(title=f"{date} 09:15-10:00 价格走势", xaxis_title="时间", yaxis_title="价格")
                st.plotly_chart(fig_twin, use_container_width=True)

    else:
        st.info("未找到历史“孪生日”。")
else:
    st.info("数据不足，无法进行高级相似度分析。")


# --- Simulation Test ---
st.subheader("5. 仿真测试")
st.write("通过调整模拟数据参数，观察仪表盘和特征指标的动态变化。")

# User input for mock data simulation
simulation_start_price = st.slider("模拟起始价格", 500.0, 700.0, 585.0, 0.1)
simulate_button = st.button("生成并显示模拟数据走势")

if simulate_button:
    simulated_data = generate_mock_minute_data(start_price=simulation_start_price, date=datetime.now())
    st.write("#### 模拟数据走势图:")
    fig_simulated = go.Figure()
    fig_simulated.add_trace(go.Scatter(x=simulated_data['时间'], y=simulated_data['收盘'], mode='lines', name='模拟收盘价'))
    fig_simulated.update_layout(title="模拟 09:15-10:00 价格走势", xaxis_title="时间", yaxis_title="价格")
    st.plotly_chart(fig_simulated, use_container_width=True)
    
    st.write("#### 模拟数据特征计算:")
    # Calculate features for simulated data
    sim_bidding_strength = calculate_bidding_strength(simulated_data, historical_data) # Use actual historical data for comparison
    sim_efficiency_before_10am = calculate_efficiency_before_10am(simulated_data)
    sim_moat_support_detected = detect_moat_support(simulated_data, golden_pit_range=GOLDEN_PIT_RANGE)

    st.metric("模拟竞价强弱度", f"{sim_bidding_strength:.2f}")
    st.metric("模拟10点前效率", f"{sim_efficiency_before_10am:.4f}")
    st.metric("模拟护城河支撑检测", "检测到" if sim_moat_support_detected else "未检测到")


# Instructions to run the app
st.sidebar.markdown("""
---
**如何运行:**
1. 确保已安装依赖: `pip install -r requirements.txt`
2. 在终端中运行: `streamlit run app.py`
""")
