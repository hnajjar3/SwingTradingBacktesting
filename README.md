# SwingTradingBacktesting

## Overview
This is a multi-indicator strategy created to test any ticker symbol available on Yahoo Finance. It differs from other strategies in that it utilizes multiple indicators and optimized entry and exits. 

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/SwingTradingStrategy.git
   cd SwingTradingStrategy
   
2.	Set up a virtual environment (optional but recommended):

python -m venv trading_env
source trading_env/bin/activate  # On Windows use `trading_env\Scripts\activate`
3.	Install the required packages:
pip install -r requirements.txt

Ensure requirements.txt includes:
yfinance
pandas
pandas_ta
backtesting
scikit-learn
numpy
argparse
matplotlib

Running the Strategy
You can run the strategy using a stock ticker or a CSV file with historical data.

Example Usage with a Ticker:
python strategy.py -t AAPL -d 2014-01-01:2024-08-27

With a CSV file:
python strategy.py -i data.csv -r W-FRI

Strategy Details

	•	Indicators Used:
	•	RSI: Identifies oversold conditions.
	•	MACD: Confirms trend direction and momentum.
	•	CCI: Detects cyclical trends and potential reversals.
    •	Optimal Entry and Exit delays


