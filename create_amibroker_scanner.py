import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Amibroker-style exploration scanner
scanner_code = """# Amibroker Style Exploration
# Equivalent to:
# Filter = 1;
# AddColumn(Close,"LTP",1.2);
# AddColumn(EMA(Close,10),"EMA10",1.2);
# AddColumn(EMA(Close,20),"EMA20",1.2);

# Calculate indicators
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Filter - Show all stocks (Filter = 1 in Amibroker)
Filter = 1  # or True

# Add columns to display
AddColumn('LTP', round(float(close.iloc[-1]), 2))
AddColumn('EMA10', round(float(ema10.iloc[-1]), 2))
AddColumn('EMA20', round(float(ema20.iloc[-1]), 2))
"""

with app.app_context():
    # Check if scanner exists
    scanner = Scanner.query.filter_by(name='Amibroker Style').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'Amibroker-style exploration - Filter and AddColumn'
        db.session.commit()
        print("Amibroker Style scanner updated successfully!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='Amibroker Style',
            description='Amibroker-style exploration - Filter and AddColumn',
            category='exploration',
            code=scanner_code,
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Amibroker Style scanner created successfully!")
        print("Scanner ID:", new_scanner.id)