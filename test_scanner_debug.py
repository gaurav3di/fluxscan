import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Debug version to check data retrieval
scanner_code = """# Debug Volatility Scanner
import pandas as pd

# Debug: Print symbol being processed
print(f"Processing: {symbol}")

# Parameters
ShortATRperiod = 5
LongATRperiod = 10

# Debug: Check data
print(f"Data shape: {data.shape if 'data' in locals() else 'No data'}")
print(f"Close length: {len(close) if 'close' in locals() else 'No close'}")

# Check if we have valid data
if len(close) < 20:
    print(f"WARNING: Not enough data for {symbol}, only {len(close)} bars")
    Filter = False
else:
    # Calculate ATRs
    ATRshort = talib.ATR(high, low, close, timeperiod=ShortATRperiod)
    ATRlong = talib.ATR(high, low, close, timeperiod=LongATRperiod)

    # Get current values
    current_close = float(close.iloc[-1])
    current_atr_short = float(ATRshort.iloc[-1]) if not pd.isna(ATRshort.iloc[-1]) else 0
    current_atr_long = float(ATRlong.iloc[-1]) if not pd.isna(ATRlong.iloc[-1]) else 0

    # Debug: Print values
    print(f"{symbol}: Close={current_close:.2f}, ATR5={current_atr_short:.2f}, ATR10={current_atr_long:.2f}")

    # Calculate volatility percentages
    VolShortPct = (100 * current_atr_short / current_close) if current_close > 0 else 0
    VolLongPct = (100 * current_atr_long / current_close) if current_close > 0 else 0

    # Calculate ATR ratio
    ATRratio = (current_atr_short / current_atr_long) if current_atr_long != 0 else 0

    # Calculate MACD
    macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    current_macd = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0

    # Filter - Show all for debugging
    Filter = True  # Show all to see if data is different

    # Add columns
    AddColumn('Symbol', symbol)  # Add symbol to verify
    AddColumn('MACD', round(current_macd, 2))
    AddColumn('Close Price', round(current_close, 2))
    AddColumn('Short ATR', round(current_atr_short, 2))
    AddColumn('Long ATR', round(current_atr_long, 2))
    AddColumn('Short ATR %', round(VolShortPct, 2))
    AddColumn('Long ATR %', round(VolLongPct, 2))
    AddColumn('ATR Ratio', round(ATRratio, 2))
"""

with app.app_context():
    scanner = Scanner.query.filter_by(name='Debug Volatility').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'Debug scanner to check data issues'
        db.session.commit()
        print("Debug scanner updated!")
    else:
        new_scanner = Scanner(
            name='Debug Volatility',
            description='Debug scanner to check data issues',
            category='debug',
            code=scanner_code,
            parameters='{}',
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Debug scanner created!")
        print("Scanner ID:", new_scanner.id)