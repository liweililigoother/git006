# a.py
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import random

def get_stock_data_simulated(stock_code):
    """
    Simulates 5-minute interval stock data for a given stock code for the current day.
    """
    now = datetime.datetime.now()
    today_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
    today_end = now.replace(hour=15, minute=0, second=0, microsecond=0) # Assuming market closes at 3 PM

    time_intervals = []
    current_time = today_start
    while current_time <= today_end:
        time_intervals.append(current_time)
        current_time += datetime.timedelta(minutes=5)

    data = []
    initial_price = random.uniform(50.0, 150.0)
    current_price = initial_price

    for t in time_intervals:
        open_price = current_price
        close_price = open_price + random.uniform(-2.0, 2.0)
        high_price = max(open_price, close_price) + random.uniform(0.0, 1.0)
        low_price = min(open_price, close_price) - random.uniform(0.0, 1.0)
        volume = random.randint(10000, 500000)
        turnover = volume * (open_price + close_price) / 2
        change_percent = ((close_price - open_price) / open_price) * 100

        data.append({
            'time': t.strftime('%H:%M'),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume,
            'turnover': round(turnover, 2),
            'change_percent': round(change_percent, 2)
        })
        current_price = close_price # Next interval starts from current close

    return pd.DataFrame(data)

def generate_markdown_report(df, stock_code, output_file):
    """Generates a markdown report from the stock data."""
    report = f"# Stock Data Report for {stock_code}\n\n"
    report += f"**Date**: {datetime.date.today().strftime('%Y-%m-%d')}\n\n"
    report += df.to_markdown(index=False)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

def generate_chart(df, stock_code, output_file):
    """Generates a bar chart for 5-minute trading price and volume."""
    fig, ax1 = plt.subplots(figsize=(15, 7))

    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price', color='tab:blue')
    ax1.plot(df['time'], df['close'], color='tab:blue', label='Close Price')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.set_title(f'{stock_code} 5-Minute Trading Data - {datetime.date.today().strftime("%Y-%m-%d")}')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Add a second y-axis for volume
    ax2 = ax1.twinx()
    ax2.set_ylabel('Volume', color='tab:red')
    ax2.bar(df['time'], df['volume'], color='tab:red', alpha=0.3, label='Volume')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Format x-axis labels to show less frequently for readability
    if len(df) > 30: # Adjust threshold as needed
        n = len(df) // 15 # Show about 15 labels
        ax1.set_xticks(df['time'][::n])
        ax1.set_xticklabels(df['time'][::n], rotation=45, ha='right')
    else:
        ax1.set_xticklabels(df['time'], rotation=45, ha='right')


    fig.tight_layout() # otherwise the right y-label is slightly clipped
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.savefig(output_file)
    plt.close(fig)

if __name__ == "__main__":
    STOCK_CODE = "688027"
    today_str = datetime.date.today().strftime("%m%d")
    MD_FILE = f"{today_str}.md"
    PNG_FILE = f"{today_str}.png"

    print(f"Collecting (simulated) stock data for {STOCK_CODE}...")
    stock_data_df = get_stock_data_simulated(STOCK_CODE)
    print("Data collected.")

    print(f"Generating Markdown report to {MD_FILE}...")
    generate_markdown_report(stock_data_df, STOCK_CODE, MD_FILE)
    print("Markdown report generated.")

    print(f"Generating chart to {PNG_FILE}...")
    generate_chart(stock_data_df, STOCK_CODE, PNG_FILE)
    print("Chart generated.")
