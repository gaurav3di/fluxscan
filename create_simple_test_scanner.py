import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Simple test scanner to verify unique data per symbol
scanner_code = """# Simple Test - Verify unique data per symbol

# Always show all stocks
Filter = True

# Get basic values for this symbol
current_close = float(close.iloc[-1]) if len(close) > 0 else 0
max_close = float(close.max()) if len(close) > 0 else 0
min_close = float(close.min()) if len(close) > 0 else 0
avg_close = float(close.mean()) if len(close) > 0 else 0

# Calculate simple metrics
ema5 = talib.EMA(close, timeperiod=5)
ema10 = talib.EMA(close, timeperiod=10)

current_ema5 = float(ema5.iloc[-1]) if len(ema5) > 0 and not pd.isna(ema5.iloc[-1]) else 0
current_ema10 = float(ema10.iloc[-1]) if len(ema10) > 0 and not pd.isna(ema10.iloc[-1]) else 0

# Add columns
AddColumn('Symbol Check', symbol)  # Verify we have the right symbol
AddColumn('Close', round(current_close, 2))
AddColumn('Max', round(max_close, 2))
AddColumn('Min', round(min_close, 2))
AddColumn('Avg', round(avg_close, 2))
AddColumn('EMA5', round(current_ema5, 2))
AddColumn('EMA10', round(current_ema10, 2))
AddColumn('Data Points', len(close))
"""

with app.app_context():
    scanner = Scanner.query.filter_by(name='Data Test').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'Simple test to verify unique data per symbol'
        db.session.commit()
        print("Data Test scanner updated!")
    else:
        new_scanner = Scanner(
            name='Data Test',
            description='Simple test to verify unique data per symbol',
            category='test',
            code=scanner_code,
            parameters='{}',
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Data Test scanner created!")
        print("Scanner ID:", new_scanner.id)