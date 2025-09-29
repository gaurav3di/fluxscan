import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Basic Exploration Scanner - Shows LTP, EMA10, EMA20 for ALL stocks
scanner_code = """# Basic Exploration - Show Latest Price and EMAs
# Similar to Amibroker: Filter = 1 (shows all stocks)

# Calculate EMAs
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Get latest values (last bar)
latest_close = float(close.iloc[-1]) if len(close) > 0 else 0
latest_ema10 = float(ema10.iloc[-1]) if not pd.isna(ema10.iloc[-1]) else 0
latest_ema20 = float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else 0

# Get timestamp
try:
    latest_time = data.index[-1].strftime('%Y-%m-%d %H:%M') if hasattr(data.index[-1], 'strftime') else str(data.index[-1])
except:
    latest_time = "Latest"

# Calculate trend
trend = "NEUTRAL"
if latest_ema10 > 0 and latest_ema20 > 0:
    if latest_ema10 > latest_ema20:
        trend = "BULLISH"
    elif latest_ema10 < latest_ema20:
        trend = "BEARISH"

# Calculate EMA difference
ema_diff = latest_ema10 - latest_ema20
ema_diff_pct = (ema_diff / latest_ema20 * 100) if latest_ema20 > 0 else 0

# Get volume if available
latest_volume = float(volume.iloc[-1]) if 'volume' in locals() and len(volume) > 0 and not pd.isna(volume.iloc[-1]) else 0

# ALWAYS return a signal (Filter = 1 in Amibroker means show ALL)
signal = True
signal_type = 'EXPLORE'  # Special type for exploration

# Build metrics
metrics = {
    'ltp': round(latest_close, 2),
    'close_price': round(latest_close, 2),
    'ema10': round(latest_ema10, 2),
    'ema20': round(latest_ema20, 2),
    'trend': trend,
    'ema_diff': round(ema_diff, 2),
    'ema_diff_pct': round(ema_diff_pct, 2),
    'volume': int(latest_volume),
    'timestamp': latest_time,

    # Additional calculated metrics
    'above_ema10': "YES" if latest_close > latest_ema10 else "NO",
    'above_ema20': "YES" if latest_close > latest_ema20 else "NO",
    'ema10_above_ema20': "YES" if latest_ema10 > latest_ema20 else "NO",

    # Price distance from EMAs
    'dist_from_ema10': round((latest_close - latest_ema10), 2),
    'dist_from_ema10_pct': round((latest_close - latest_ema10) / latest_ema10 * 100, 2) if latest_ema10 > 0 else 0,
    'dist_from_ema20': round((latest_close - latest_ema20), 2),
    'dist_from_ema20_pct': round((latest_close - latest_ema20) / latest_ema20 * 100, 2) if latest_ema20 > 0 else 0,
}
"""

with app.app_context():
    # Check if scanner exists
    scanner = Scanner.query.filter_by(name='Basic Exploration').first()

    if scanner:
        # Update existing scanner
        scanner.code = scanner_code
        scanner.description = 'Shows LTP, EMA10, EMA20 for all stocks - No filtering (Filter=1)'
        scanner.category = 'exploration'
        scanner.is_active = True
        db.session.commit()
        print("Basic Exploration scanner updated successfully!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='Basic Exploration',
            description='Shows LTP, EMA10, EMA20 for all stocks - No filtering (Filter=1)',
            category='exploration',
            code=scanner_code,
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Basic Exploration scanner created successfully!")
        print("Scanner ID:", new_scanner.id)