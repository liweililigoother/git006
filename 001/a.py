import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import os

def fetch_and_process_today_stock_data(stock_code="688027"):
    """
    Fetches today's 5-minute stock data, saves it to a markdown file, 
    and creates a price-volume chart. Overwrites existing files.
    """
    try:
        # --- 1. Fetch Data ---
        end_date = datetime.date.today()

        # Fetch today's 5-minute data from East Money
        today_df = ak.stock_zh_a_hist_min_em(symbol=stock_code, period='5', adjust='qfq')

        if today_df.empty:
            print(f"No 5-minute data available for {stock_code} today. The market might be closed.")
            return

        # Filter for today's date just in case the API returns more
        today_df['日期'] = pd.to_datetime(today_df['时间']).dt.date
        today_df = today_df[today_df['日期'] == end_date].copy()
        
        if today_df.empty:
            print(f"No 5-minute data found for {stock_code} specifically for today's date.")
            return

        # --- 2. Prepare Data & Save to Markdown ---
        file_date_str = end_date.strftime('%m%d')
        md_filename = f"a{file_date_str}.md"
        png_filename = f"a{file_date_str}.png"
        
        # Use the directory of the script for output files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        md_filepath = os.path.join(script_dir, md_filename)
        png_filepath = os.path.join(script_dir, png_filename)

        # Select and rename columns for clarity
        display_df = today_df[['时间', '开盘', '收盘', '最高', '最低', '成交量']].copy()

        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {stock_code} Today's Stock Data ({end_date.strftime('%Y-%m-%d')})\n\n")
            f.write("## 5-Minute Intervals\n")
            f.write(display_df.to_markdown(index=False))

        print(f"Data saved to {md_filepath}")

        # --- 3. Generate Chart ---
        plot_df = display_df.copy()
        plot_df['时间'] = pd.to_datetime(plot_df['时间'])
        plot_df.set_index('时间', inplace=True)

        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Plot closing price as a line chart
        color = 'tab:red'
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price', color=color)
        ax1.plot(plot_df.index, plot_df['收盘'], color=color, label='Close Price', marker='o', linestyle='-')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True)

        # Rotate x-axis labels for better readability
        plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

        # Create a second y-axis for volume as a bar chart
        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('Volume', color=color)
        ax2.bar(plot_df.index, plot_df['成交量'], color=color, alpha=0.6, width=0.002, label='Volume')
        ax2.tick_params(axis='y', labelcolor=color)

        fig.suptitle(f'Today\'s 5-Min Price and Volume for {stock_code}', fontsize=16)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        plt.savefig(png_filepath)
        print(f"Chart saved to {png_filepath}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Set matplotlib to use a non-interactive backend to avoid display issues in some environments
    import matplotlib
    matplotlib.use('Agg')
    fetch_and_process_today_stock_data()