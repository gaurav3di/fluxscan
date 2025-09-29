import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Simple Exploration Scanner - Exact replica of Amibroker Filter = 1
scanner_code = """# Simple Exploration - LTP, EMA10, EMA20
# Amibroker equivalent: Filter = 1;

# Calculate EMAs
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Get latest values
ltp = float(close.iloc[-1])
ema10_value = float(ema10.iloc[-1])
ema20_value = float(ema20.iloc[-1])

# Filter = 1 means show ALL stocks
signal = True
signal_type = 'DATA'

# Simple metrics - just the 3 values
metrics = {
    'ltp': round(ltp, 2),
    'ema10': round(ema10_value, 2),
    'ema20': round(ema20_value, 2)
}
"""

with app.app_context():
    # Check if scanner exists
    scanner = Scanner.query.filter_by(name='Simple LTP EMA').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'Simple exploration - LTP, EMA10, EMA20'
        db.session.commit()
        print("Simple LTP EMA scanner updated successfully!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='Simple LTP EMA',
            description='Simple exploration - LTP, EMA10, EMA20',
            category='exploration',
            code=scanner_code,
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Simple LTP EMA scanner created successfully!")
        print("Scanner ID:", new_scanner.id)