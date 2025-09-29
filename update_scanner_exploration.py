import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Scanner
from app import app

# Amibroker-style Exploration Scanner - Shows ALL crossovers
scanner_code = """# EMA Crossover Exploration - Amibroker Style
# Shows ALL crossovers in the scanning period, not just the latest

import pandas as pd

# Calculate EMAs
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Calculate ATR for risk management
atr = talib.ATR(high, low, close, timeperiod=14)

# MACD for additional confirmation
macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

# Initialize crossover list
crossovers = []

# Scan through all bars to find crossovers
for i in range(2, len(close)):
    # Current and previous EMA values
    curr_ema10 = float(ema10.iloc[i]) if not pd.isna(ema10.iloc[i]) else 0
    curr_ema20 = float(ema20.iloc[i]) if not pd.isna(ema20.iloc[i]) else 0
    prev_ema10 = float(ema10.iloc[i-1]) if not pd.isna(ema10.iloc[i-1]) else 0
    prev_ema20 = float(ema20.iloc[i-1]) if not pd.isna(ema20.iloc[i-1]) else 0

    # Skip if any value is 0
    if curr_ema10 == 0 or curr_ema20 == 0 or prev_ema10 == 0 or prev_ema20 == 0:
        continue

    # Detect crossovers
    bullish_crossover = prev_ema10 <= prev_ema20 and curr_ema10 > curr_ema20
    bearish_crossover = prev_ema10 >= prev_ema20 and curr_ema10 < curr_ema20

    if bullish_crossover or bearish_crossover:
        # Get values at crossover point
        crossover_price = float(close.iloc[i])
        crossover_atr = float(atr.iloc[i]) if not pd.isna(atr.iloc[i]) else 0
        crossover_macd = float(macd.iloc[i]) if not pd.isna(macd.iloc[i]) else 0
        crossover_volume = float(volume.iloc[i]) if 'volume' in locals() and not pd.isna(volume.iloc[i]) else 0

        # Determine signal type
        signal_type = 'BUY' if bullish_crossover else 'SELL'

        # Calculate risk metrics based on ATR
        if signal_type == 'BUY':
            entry_price = crossover_price
            stop_loss = crossover_price - (2 * crossover_atr)
            target_price = crossover_price + (3 * crossover_atr)
            risk_reward = 1.5 if crossover_atr > 0 else 0
        else:  # SELL
            entry_price = crossover_price
            stop_loss = crossover_price + (2 * crossover_atr)
            target_price = crossover_price - (3 * crossover_atr)
            risk_reward = 1.5 if crossover_atr > 0 else 0

        # Calculate ATR percentages
        short_atr_pct = (crossover_atr / crossover_price) * 100 if crossover_price > 0 else 0
        long_atr_pct = short_atr_pct  # Can be different period if needed
        atr_ratio = 1.0  # Ratio between short and long ATR

        # Get timestamp if available
        try:
            timestamp = data.index[i].strftime('%Y-%m-%d %H:%M') if hasattr(data.index[i], 'strftime') else str(i)
        except:
            timestamp = f"Bar {i}"

        # Add to crossovers list
        crossovers.append({
            'bar': i,
            'type': signal_type,
            'date': timestamp,
            'price': round(crossover_price, 2),
            'ema10': round(curr_ema10, 2),
            'ema20': round(curr_ema20, 2),
            'macd': round(crossover_macd, 2),
            'atr': round(crossover_atr, 2),
            'short_atr': round(crossover_atr, 2),
            'long_atr': round(crossover_atr, 2),
            'short_atr_pct': round(short_atr_pct, 2),
            'long_atr_pct': round(long_atr_pct, 2),
            'atr_ratio': round(atr_ratio, 2),
            'atr_to_price': round(short_atr_pct, 2),
            'entry': round(entry_price, 2),
            'target': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'risk_reward': round(risk_reward, 2),
            'volume': int(crossover_volume)
        })

# Get current status
current_price = float(close.iloc[-1])
current_ema10 = float(ema10.iloc[-1]) if not pd.isna(ema10.iloc[-1]) else 0
current_ema20 = float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else 0
current_trend = 'BULLISH' if current_ema10 > current_ema20 else 'BEARISH'

# Determine if we have signals to report
if len(crossovers) > 0:
    signal = True

    # Get the most recent crossover
    most_recent = crossovers[-1]
    signal_type = most_recent['type']

    # Build comprehensive metrics
    metrics = {
        'current_price': round(current_price, 2),
        'current_ema10': round(current_ema10, 2),
        'current_ema20': round(current_ema20, 2),
        'current_trend': current_trend,
        'total_bars': len(close),
        'crossover_count': len(crossovers),
        'crossovers': crossovers,  # All crossovers
        'most_recent': most_recent,
        'summary': f'{symbol}: {len(crossovers)} crossovers found',

        # Latest crossover metrics for display
        'price': most_recent['price'],
        'close_price': most_recent['price'],
        'macd': most_recent['macd'],
        'short_atr': most_recent['short_atr'],
        'long_atr': most_recent['long_atr'],
        'short_atr_pct': most_recent['short_atr_pct'],
        'long_atr_pct': most_recent['long_atr_pct'],
        'atr_ratio': most_recent['atr_ratio'],
        'atr_to_price': most_recent['atr_to_price'],
        'entry': most_recent['entry'],
        'target': most_recent['target'],
        'stop_loss': most_recent['stop_loss'],
        'risk_reward': most_recent['risk_reward'],
        'timestamp': most_recent['date']
    }
else:
    # No crossovers found
    signal = False
    signal_type = None
    metrics = {
        'current_price': round(current_price, 2),
        'current_ema10': round(current_ema10, 2),
        'current_ema20': round(current_ema20, 2),
        'current_trend': current_trend,
        'total_bars': len(close),
        'crossover_count': 0,
        'crossovers': [],
        'summary': f'{symbol}: No crossovers found'
    }
"""

with app.app_context():
    # Find the scanner
    scanner = Scanner.query.filter_by(name='EMA Crossover Final').first()

    if scanner:
        scanner.code = scanner_code
        scanner.description = 'EMA 10/20 crossover exploration - shows ALL crossovers like Amibroker'
        db.session.commit()
        print("Scanner updated to exploration style - will show ALL crossovers!")
    else:
        # Create new scanner
        new_scanner = Scanner(
            name='EMA Crossover Final',
            description='EMA 10/20 crossover exploration - shows ALL crossovers like Amibroker',
            category='exploration',
            code=scanner_code,
            is_active=True
        )
        db.session.add(new_scanner)
        db.session.commit()
        print("Exploration scanner created - will show ALL crossovers!")