import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Fixed Volatility Scanner with proper data handling
scanner_code = """# Short vs Long Term Volatility Analysis
# Fixed to ensure unique data per symbol

# Parameters with safe defaults
ShortATRperiod = int(parameters.get('short_atr_period', 5))
LongATRperiod = int(parameters.get('long_atr_period', 10))

# Ensure we have valid data
if len(close) < max(ShortATRperiod, LongATRperiod, 26) + 1:
    Filter = False
else:
    try:
        # Calculate ATRs - Force recalculation for each symbol
        high_array = np.array(high, dtype=np.float64)
        low_array = np.array(low, dtype=np.float64)
        close_array = np.array(close, dtype=np.float64)

        ATRshort = talib.ATR(high_array, low_array, close_array, timeperiod=ShortATRperiod)
        ATRlong = talib.ATR(high_array, low_array, close_array, timeperiod=LongATRperiod)

        # Get current values - ensure we're getting the right symbol's data
        current_close = float(close_array[-1])
        current_atr_short = float(ATRshort[-1]) if not np.isnan(ATRshort[-1]) else 0
        current_atr_long = float(ATRlong[-1]) if not np.isnan(ATRlong[-1]) else 0

        # Calculate volatility percentages
        VolShortPct = (100 * current_atr_short / current_close) if current_close > 0 else 0
        VolLongPct = (100 * current_atr_long / current_close) if current_close > 0 else 0

        # Calculate ATR ratio
        ATRratio = (current_atr_short / current_atr_long) if current_atr_long != 0 else 0

        # Calculate MACD for filter
        macd_line = talib.MACD(close_array, fastperiod=12, slowperiod=26, signalperiod=9)[0]
        current_macd = float(macd_line[-1]) if not np.isnan(macd_line[-1]) else 0

        # Filter - Show only when MACD > 0
        Filter = current_macd > 0

        # Add columns with actual values for this symbol
        AddColumn('MACD', round(current_macd, 2))
        AddColumn('Close Price', round(current_close, 2))
        AddColumn('Short ATR', round(current_atr_short, 2))
        AddColumn('Long ATR', round(current_atr_long, 2))
        AddColumn('Short ATR % of Price', round(VolShortPct, 2))
        AddColumn('Long ATR % of Price', round(VolLongPct, 2))
        AddColumn('ATR Ratio S/L', round(ATRratio, 2))
        AddColumn('ATR-to-Price (Short %)', round(VolShortPct, 2))
        AddColumn('Volatility Status', 'HIGH' if ATRratio > 1 else 'LOW')
        AddColumn('Trend', 'BULLISH' if current_macd > 0 else 'BEARISH')

    except Exception as e:
        # If any error, skip this symbol
        Filter = False
"""

scanner_params = {
    "short_atr_period": 5,
    "long_atr_period": 10
}

with app.app_context():
    scanner = Scanner.query.filter_by(name='Short vs Long Volatility').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'ATR-based volatility analysis - Fixed for unique data per symbol'
        scanner.category = 'volatility'
        scanner.parameters = json.dumps(scanner_params)
        db.session.commit()
        print("Short vs Long Volatility scanner fixed and updated!")
    else:
        new_scanner = Scanner(
            name='Short vs Long Volatility',
            description='ATR-based volatility analysis - Fixed for unique data per symbol',
            category='volatility',
            code=scanner_code,
            parameters=json.dumps(scanner_params),
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Short vs Long Volatility scanner created!")
        print("Scanner ID:", new_scanner.id)