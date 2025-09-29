import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Fixed Short vs Long Term Volatility Scanner
scanner_code = """# Short vs Long Term Volatility Analysis
# Amibroker-style exploration with ATR analysis

# Parameters - Handle both direct values and nested definitions
def get_param(param_name, default_value):
    param = parameters.get(param_name, default_value)
    # If it's a dict with 'default' key, use that
    if isinstance(param, dict) and 'default' in param:
        return param['default']
    return param

ShortATRperiod = get_param('short_atr_period', 5)
LongATRperiod = get_param('long_atr_period', 10)

# Calculate ATRs
ATRshort = talib.ATR(high, low, close, timeperiod=int(ShortATRperiod))
ATRlong = talib.ATR(high, low, close, timeperiod=int(LongATRperiod))

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

# Store parameters as simple key-value pairs for default values
# The UI can use a more complex structure if needed
scanner_params = {
    "short_atr_period": 5,
    "long_atr_period": 10
}

with app.app_context():
    # Check if scanner exists
    scanner = Scanner.query.filter_by(name='Short vs Long Volatility').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'ATR-based volatility analysis - Short vs Long term'
        scanner.category = 'volatility'
        scanner.parameters = json.dumps(scanner_params)
        db.session.commit()
        print("Short vs Long Volatility scanner updated with fixed parameters!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='Short vs Long Volatility',
            description='ATR-based volatility analysis - Short vs Long term',
            category='volatility',
            code=scanner_code,
            parameters=json.dumps(scanner_params),
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Short vs Long Volatility scanner created with fixed parameters!")
        print("Scanner ID:", new_scanner.id)