import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Amibroker-style EMA Crossover Scanner with ATR metrics
scanner_code = """# EMA Crossover with ATR Risk Management
# Similar to Amibroker exploration output

# Calculate EMAs
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Calculate ATR for risk management
atr = talib.ATR(high, low, close, timeperiod=14)

# MACD for additional confirmation
macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

# Current values
current_price = float(close.iloc[-1])
current_ema10 = float(ema10.iloc[-1])
current_ema20 = float(ema20.iloc[-1])
current_atr = float(atr.iloc[-1]) if len(atr) > 0 else 0
current_macd = float(macd.iloc[-1]) if len(macd) > 0 else 0

# Previous values for crossover detection
prev_ema10 = float(ema10.iloc[-2])
prev_ema20 = float(ema20.iloc[-2])

# Detect crossovers
bullish_crossover = prev_ema10 <= prev_ema20 and current_ema10 > current_ema20
bearish_crossover = prev_ema10 >= prev_ema20 and current_ema10 < current_ema20

# Generate signals
signal = False
signal_type = None

if bullish_crossover:
    signal = True
    signal_type = 'BUY'

    # Calculate risk metrics
    entry_price = current_price
    stop_loss = current_price - (2 * current_atr)  # 2 ATR stop loss
    target_price = current_price + (3 * current_atr)  # 3 ATR target

elif bearish_crossover:
    signal = True
    signal_type = 'SELL'

    # Calculate risk metrics
    entry_price = current_price
    stop_loss = current_price + (2 * current_atr)  # 2 ATR stop loss
    target_price = current_price - (3 * current_atr)  # 3 ATR target

# Calculate additional metrics if signal found
if signal:
    # ATR-based metrics
    short_atr = current_atr
    long_atr = current_atr  # Can be different period if needed

    # Percentage calculations
    if signal_type == 'BUY':
        short_atr_pct = (short_atr / current_price) * 100
        long_atr_pct = (long_atr / current_price) * 100
        atr_ratio = long_atr / short_atr if short_atr > 0 else 1
        atr_to_price = (short_atr / current_price) * 100
    else:  # SELL
        short_atr_pct = (short_atr / current_price) * 100
        long_atr_pct = (long_atr / current_price) * 100
        atr_ratio = long_atr / short_atr if short_atr > 0 else 1
        atr_to_price = (short_atr / current_price) * 100

    # Build metrics dictionary
    metrics = {
        'price': current_price,
        'close_price': current_price,
        'macd': round(current_macd, 2),
        'short_atr': round(short_atr, 2),
        'long_atr': round(long_atr, 2),
        'short_atr_pct': round(short_atr_pct, 2),
        'long_atr_pct': round(long_atr_pct, 2),
        'atr_ratio': round(atr_ratio, 2),
        'atr_to_price': round(atr_to_price, 2),
        'entry': round(entry_price, 2),
        'target': round(target_price, 2),
        'stop_loss': round(stop_loss, 2),
        'risk_reward': round((target_price - entry_price) / (entry_price - stop_loss), 2) if signal_type == 'BUY' else round((entry_price - target_price) / (stop_loss - entry_price), 2),
        'ema10': round(current_ema10, 2),
        'ema20': round(current_ema20, 2)
    }
"""

with app.app_context():
    # Find the scanner
    scanner = Scanner.query.filter_by(name='EMA Crossover Final').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'EMA 10/20 crossover with ATR-based risk management metrics'
        db.session.commit()
        print("Scanner updated successfully with Amibroker-style metrics!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='EMA Crossover Final',
            description='EMA 10/20 crossover with ATR-based risk management metrics',
            category='trend',
            code=scanner_code,
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Scanner created successfully with Amibroker-style metrics!")