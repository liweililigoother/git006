
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import os

def fetch_and_process_stock_data(stock_code="688027", num_trading_days=20):
    """
    Fetches stock data, saves it to a markdown file, and creates a chart.
    """
    try:
        # --- 1. Fetch Data ---
        end_date = datetime.date.today()
        # Fetch data for a longer period to ensure we get enough trading days
        # A buffer of 1.5x to 2x the trading days is usually sufficient
        calendar_days_buffer = num_trading_days * 2
        start_date_hist = end_date - datetime.timedelta(days=calendar_days_buffer)
        
        # Format dates for akshare
        start_date_str = start_date_hist.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')

        # Fetch historical daily data
        hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date_str, end_date=end_date_str, adjust="qfq")
        
        # Ensure we only keep the last 'num_trading_days' trading days
        if not hist_df.empty:
            hist_df = hist_df.tail(num_trading_days)

        # Fetch today's 5-minute data
        try:
            today_df = ak.stock_zh_a_hist_min_em(symbol=stock_code, period='5', adjust='qfq')
            if not today_df.empty:
                # Keep only today's data
                today_df['日期'] = pd.to_datetime(today_df['时间']).dt.date
                today_df = today_df[today_df['日期'] == end_date]
                # Select and rename columns to match historical data
                today_df = today_df[['时间', '开盘', '收盘', '最高', '最低', '成交量']]
                today_df.rename(columns={'时间': '日期'}, inplace=True)
            else:
                today_df = pd.DataFrame() # Ensure it's a dataframe
        except Exception as e:
            print(f"Could not fetch 5-minute data for today (market might be closed): {e}")
            today_df = pd.DataFrame() # Ensure it's a dataframe if call fails

        # --- 2. Prepare Data & Save to Markdown ---
        # Use today's date for filenames
        file_date_str = end_date.strftime('%m%d')
        md_filename = f"b{file_date_str}.md"
        png_filename = f"b{file_date_str}.png"
        
        # Use the directory of the script for output files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        md_filepath = os.path.join(script_dir, md_filename)
        png_filepath = os.path.join(script_dir, png_filename)

        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {stock_code} Stock Data ({end_date_str})\n\n")
            if not hist_df.empty:
                f.write("## Last 20 Days (Daily)\n")
                # Keep only relevant columns for markdown
                hist_display = hist_df[['日期', '开盘', '收盘', '最高', '最低', '成交量']]
                f.write(hist_display.to_markdown(index=False))
                f.write("\n\n")
            else:
                f.write("Could not fetch historical daily data.\n\n")

            if not today_df.empty:
                f.write("## Today's Data (5-Minute Intervals)\n")
                f.write(today_df.to_markdown(index=False))
            else:
                f.write("No 5-minute data available for today.")

        print(f"Data saved to {md_filepath}")

        # --- 3. Generate Chart ---
        if not hist_df.empty:
            # For simplicity, we'll chart the historical daily data
            plot_df = hist_df.copy()
            plot_df['日期'] = pd.to_datetime(plot_df['日期'])
            plot_df.set_index('日期', inplace=True)

            fig, ax1 = plt.subplots(figsize=(12, 7))

            # Plot closing price
            color = 'tab:red'
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Price', color=color)
            ax1.plot(plot_df.index, plot_df['收盘'], color=color, label='Close Price')
            ax1.tick_params(axis='y', labelcolor=color)
            plt.xticks(rotation=45)

            # Create a second y-axis for volume
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('Volume', color=color)
            # Plot volume as a bar chart
            ax2.bar(plot_df.index, plot_df['成交量'], color=color, alpha=0.6, label='Volume')
            ax2.tick_params(axis='y', labelcolor=color)

            fig.suptitle(f'Stock Price and Volume for {stock_code} (Last {num_trading_days} Trading Days)')
            fig.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for title
            
            plt.savefig(png_filepath)
            print(f"Chart saved to {png_filepath}")
        else:
            print("Cannot generate chart because no historical data was fetched.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_and_process_stock_data()
