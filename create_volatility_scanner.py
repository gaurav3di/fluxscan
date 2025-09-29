import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Short vs Long Term Volatility Scanner (Amibroker style)
scanner_code = """# Short vs Long Term Volatility Analysis
# Amibroker-style exploration with ATR analysis

# Parameters (can be adjusted in scanner parameters)
ShortATRperiod = parameters.get('short_atr_period', 5)
LongATRperiod = parameters.get('long_atr_period', 10)

# Calculate ATRs
ATRshort = talib.ATR(high, low, close, timeperiod=ShortATRperiod)
ATRlong = talib.ATR(high, low, close, timeperiod=LongATRperiod)

# Get current values
current_close = float(close.iloc[-1])
current_atr_short = float(ATRshort.iloc[-1]) if not pd.isna(ATRshort.iloc[-1]) else 0
current_atr_long = float(ATRlong.iloc[-1]) if not pd.isna(ATRlong.iloc[-1]) else 0

# Calculate volatility percentages
VolShortPct = (100 * current_atr_short / current_close) if current_close > 0 else 0
VolLongPct = (100 * current_atr_long / current_close) if current_close > 0 else 0

# Calculate ATR ratio
ATRratio = (current_atr_short / current_atr_long) if current_atr_long != 0 else 0

# Calculate MACD for filter
macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
current_macd = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0

# Filter - Show only when MACD > 0 (as in Amibroker code)
Filter = current_macd > 0

# Add columns in same order as Amibroker
AddColumn('MACD', round(current_macd, 2))
AddColumn('Close Price', round(current_close, 2))
AddColumn('Short ATR', round(current_atr_short, 2))
AddColumn('Long ATR', round(current_atr_long, 2))
AddColumn('Short ATR % of Price', round(VolShortPct, 2))
AddColumn('Long ATR % of Price', round(VolLongPct, 2))
AddColumn('ATR Ratio S/L', round(ATRratio, 2))
AddColumn('ATR-to-Price (Short %)', round(VolShortPct, 2))

# Additional useful metrics
AddColumn('Volatility Status', 'HIGH' if ATRratio > 1 else 'LOW')
AddColumn('Trend', 'BULLISH' if current_macd > 0 else 'BEARISH')
"""

# Scanner parameters configuration
scanner_params = {
    "short_atr_period": {
        "type": "int",
        "default": 5,
        "min": 2,
        "max": 50,
        "description": "Short ATR Period"
    },
    "long_atr_period": {
        "type": "int",
        "default": 10,
        "min": 5,
        "max": 100,
        "description": "Long ATR Period"
    }
}

with app.app_context():
    # Check if scanner exists
    scanner = Scanner.query.filter_by(name='Short vs Long Volatility').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'ATR-based volatility analysis - Short vs Long term'
        scanner.category = 'volatility'
        scanner.parameters = json.dumps(scanner_params)  # Convert to JSON string
        db.session.commit()
        print("Short vs Long Volatility scanner updated successfully!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='Short vs Long Volatility',
            description='ATR-based volatility analysis - Short vs Long term',
            category='volatility',
            code=scanner_code,
            parameters=json.dumps(scanner_params),  # Convert to JSON string
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Short vs Long Volatility scanner created successfully!")
        print("Scanner ID:", new_scanner.id)