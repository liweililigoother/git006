#!/usr/bin/env python3
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime, timedelta
import pandas as pd

# --- Configuration ---
TICKER = "688027.SS"  # Assuming Shanghai Stock Exchange
DAYS_OF_DATA = 30
# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
MD_FILE = os.path.join(SCRIPT_DIR, "6880271231.md")

def fetch_and_process_data(ticker, days):
    """
    Fetches intraday data by looping through each of the last N days,
    then generates charts and returns a daily summary.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    stock = yf.Ticker(ticker)
    
    # Fetch daily history for the summary markdown file first
    daily_summary = stock.history(period=f"{days}d")
    
    print(f"Fetching intraday data for the last {days} days (one day at a time)...")
    
    all_intraday_data = []
    
    # Loop from today backwards for the number of days specified
    for i in range(days):
        day = datetime.now() - timedelta(days=i)
        # yfinance `history` start/end are exclusive of the end date, so we need to add a day
        start_date = day.strftime('%Y-%m-%d')
        end_date = (day + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"  Fetching for: {start_date}")
        
        intraday_day = stock.history(start=start_date, end=end_date, interval="1m")
        
        if not intraday_day.empty:
            all_intraday_data.append(intraday_day)

    if not all_intraday_data:
        print("No intraday data found for the specified period.")
        return daily_summary

    # Combine all the dataframes
    intraday_data = pd.concat(all_intraday_data)

    # Group data by date and generate a chart for each day
    for date, day_data in intraday_data.groupby(intraday_data.index.date):
        generate_intraday_chart(day_data, date)
        
    return daily_summary

def save_summary_to_md(data, filename):
    """Saves the daily summary data to a Markdown file."""
    with open(filename, "w") as f:
        f.write(f"# Daily Stock Summary for {TICKER}\n\n")
        f.write("*Note: Charts are generated from more detailed 1-minute intraday data.*\n\n")
        f.write(data.to_markdown())
    print(f"Daily summary saved to {filename}")

def generate_intraday_chart(day_data, date):
    """Generates a PNG chart from a single day's intraday data."""
    date_str = date.strftime('%Y-%m-%d')
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot the price curve (using 'Close' price from 1m intervals)
    ax.plot(day_data.index, day_data['Close'], label='Price', color='blue')

    # Calculate total volume for the day
    total_volume = day_data['Volume'].sum()
    
    # Add High and Low price markers
    high_price = day_data['High'].max()
    low_price = day_data['Low'].min()
    high_time = day_data['High'].idxmax()
    low_time = day_data['Low'].idxmin()
    ax.plot(high_time, high_price, 'g^', markersize=8, label=f'High: {high_price:.2f}')
    ax.plot(low_time, low_price, 'rv', markersize=8, label=f'Low: {low_price:.2f}')

    # Add Volume as text on the chart
    ax.text(0.05, 0.95, f'Total Volume: {int(total_volume)}', transform=ax.transAxes, ha='left', va='top', fontsize=12, bbox=dict(boxstyle='round,pad=0.5', fc='lightblue', alpha=0.5))

    # Formatting the chart
    ax.set_title(f'Intraday Price Movement for {TICKER} on {date_str}')
    ax.set_ylabel('Price (CNY)')
    ax.set_xlabel('Time of Day')
    
    # Format the x-axis to show time
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    fig.autofmt_xdate()
    ax.grid(True)
    
    # Adjust layout and save the figure
    plt.legend()
    fig.tight_layout()
    chart_filename = os.path.join(OUTPUT_DIR, f'{date_str}.png')
    plt.savefig(chart_filename)
    plt.close(fig)
    print(f"Generated chart: {chart_filename}")

def main():
    """Main function to orchestrate the script."""
    try:
        # 1. Fetch data, process, and generate charts
        daily_summary_data = fetch_and_process_data(TICKER, DAYS_OF_DATA)

        if daily_summary_data.empty:
            print(f"No summary data found for ticker {TICKER}. Exiting.")
            return

        # 2. Save daily summary to Markdown
        save_summary_to_md(daily_summary_data, MD_FILE)
        
        print("\nAll tasks completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
