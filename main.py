import yfinance as yf
import pandas as pd
import pandas_ta as ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from sklearn.linear_model import LinearRegression
import numpy as np
import argparse
import datetime

# Function to fetch and preprocess data
def fetch_technical_data(ticker, start, end, interval=None, logarithmic=False):
    # Download historical stock data from Yahoo Finance
    data = yf.download(ticker, start=start, end=end)

    # Forward fill missing data points
    data = data.ffill()

    # Convert index to datetime format
    data.index = pd.to_datetime(data.index)

    # Resample data if interval is specified (e.g., weekly, monthly)
    if interval:
        data = data.resample(interval).last()

    # Apply logarithmic transformation if specified
    if logarithmic:
        data = np.log(data)

    # Calculate technical indicators using pandas_ta
    data['RSI'] = ta.rsi(data['Close'], length=14)
    macd = ta.macd(data['Close'])
    data['MACD'] = macd['MACD_12_26_9']
    data['MACD_Signal'] = macd['MACDs_12_26_9']
    data['MACD_Hist'] = macd['MACDh_12_26_9']
    data['CCI'] = ta.cci(data['High'], data['Low'], data['Close'], length=20)

    return data

def fetch_data_from_file(file_path, interval=None):
    # Load historical data from a CSV file
    data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')

    # Forward fill missing data points
    data.index = pd.to_datetime(data.index)
    data = data.ffill()

    # Add missing columns if they are not present in the file
    data['Open'] = data['Close']
    data['High'] = data['Close']
    data['Low'] = data['Close']
    data['Volume'] = 0  # If volume data is missing, fill with 0

    # Resample data if interval is specified
    if interval:
        data = data.resample(interval).last()

    # Drop any rows with NaNs after calculations
    data = data.dropna()

    # Calculate technical indicators using pandas_ta
    data['RSI'] = ta.rsi(data['Close'], length=14)
    macd = ta.macd(data['Close'])
    data['MACD'] = macd['MACD_12_26_9']
    data['MACD_Signal'] = macd['MACDs_12_26_9']
    data['MACD_Hist'] = macd['MACDh_12_26_9']
    data['CCI'] = ta.cci(data['High'], data['Low'], data['Close'], length=20)

    # Ensure no NaN values remain
    data = data.dropna()

    return data

# Define the trading strategy
class SwingTradingStrategy(Strategy):
    # Default parameters (these will be optimized)
    hold_period = 16
    RSI_thresh = 30
    CCI_thresh = -100
    macd_hist_thresh = 0
    tp_percent = 0.30
    entry_delay = 5

    def init(self):
        # Initialize indicators
        self.rsi = self.I(lambda x: x, self.data.RSI)
        self.macd = self.I(lambda x: x, self.data.MACD)
        self.macd_signal = self.I(lambda x: x, self.data.MACD_Signal)
        self.macd_hist = self.I(lambda x: x, self.data.MACD_Hist)
        self.cci = self.I(lambda x: x, self.data.CCI)

        # Initialize variables to track entry signals
        self.entry_day = None
        self.buy_signal_day = None

    def next(self):
        # Entry logic
        if not self.position:
            # Check if RSI and CCI conditions are met
            if self.rsi[-1] < self.RSI_thresh and self.cci[-1] < self.CCI_thresh:
                if self.buy_signal_day is None:
                    self.buy_signal_day = len(self.data)

            # Wait for a delay period before entering the trade
            if self.buy_signal_day is not None and (len(self.data) - self.buy_signal_day >= self.entry_delay):
                current_price = self.data.Close[-1]
                stop_loss = current_price * 0.9
                take_profit = current_price * (self.tp_percent + 1)

                # Check if current price is within stop-loss and take-profit range
                if stop_loss < current_price < take_profit:
                    self.buy(sl=stop_loss, tp=take_profit)
                    self.entry_day = len(self.data)
                    self.buy_signal_day = None
        else:
            # Exit logic based on hold period or MACD histogram condition
            if (len(self.data) - self.entry_day >= self.hold_period) or (self.macd_hist < self.macd_hist_thresh):
                self.position.close()

def main():
    # Argument parser to handle command-line input
    parser = argparse.ArgumentParser(description='Run Swing Trading Backtest')
    parser.add_argument('-t', '--ticker', help='Stock ticker symbol')
    parser.add_argument('-d', '--date_range', help='Date range in format YYYY-MM-DD:YYYY-MM-DD')
    parser.add_argument('-i', '--input', help='Input file with historical data')
    parser.add_argument('-r', '--resample_interval', help='Resampling interval (e.g., W-FRI for weekly, M for monthly)')
    args = parser.parse_args()

    # Parse date range
    if args.date_range:
        start_date, end_date = args.date_range.split(':')
        if not end_date:
            end_date = datetime.datetime.today().strftime('%Y-%m-%d')
    else:
        start_date = '2000-01-01'
        end_date = datetime.datetime.today().strftime('%Y-%m-%d')

    # Fetch data based on input
    if args.ticker:
        ticker = args.ticker
        technical_data = fetch_technical_data(ticker, start_date, end_date, args.resample_interval, logarithmic=False)
    elif args.input:
        technical_data = fetch_data_from_file(args.input, args.resample_interval)
        technical_data = technical_data[start_date:end_date]
    else:
        raise ValueError("You must provide either a ticker symbol or an input file.")

    print(technical_data.head())

    # Backtest the strategy and optimize parameters
    bt = Backtest(technical_data, SwingTradingStrategy, cash=10000, commission=.002)
    stats = bt.optimize(hold_period=range(10, 100, 5),
                        RSI_thresh=range(10, 50, 2),
                        CCI_thresh=range(-300, -100, 20),
                        macd_hist_thresh=[n/10 for n in range(-400, 400, 25)],
                        tp_percent=[n/100 for n in range(50, 5000, 100)],
                        entry_delay=range(0, 30, 2),
                        maximize='Return [%]',
                        max_tries=10000)

    # Output the optimal parameters and strategy performance
    print("Optimal hold_period:", stats._strategy._params['hold_period'])
    print(stats)
    bt.plot()

if __name__ == '__main__':
    main()
