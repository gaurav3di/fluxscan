from models import db, Scanner, Watchlist, ScannerTemplate
from datetime import datetime

def seed_database():
    # Create default scanner templates
    templates = [
        {
            'name': '10/20 EMA Crossover',
            'description': 'Detects when 10 EMA crosses above or below 20 EMA',
            'code': '''
# 10/20 EMA Crossover Scanner
# Generates BUY/SELL signals on EMA crossovers

# Get parameters
fast_period = params.get('fast_period', 10)
slow_period = params.get('slow_period', 20)
min_volume = params.get('min_volume', 1000000)

# Calculate EMAs
ema_fast = talib.EMA(close, timeperiod=fast_period)
ema_slow = talib.EMA(close, timeperiod=slow_period)

# Check if we have enough data
if len(ema_fast) < 2 or len(ema_slow) < 2:
    signal = False
else:
    # Current and previous values
    fast_current = ema_fast.iloc[-1]
    fast_prev = ema_fast.iloc[-2]
    slow_current = ema_slow.iloc[-1]
    slow_prev = ema_slow.iloc[-2]

    # Volume filter
    current_volume = volume.iloc[-1]
    volume_condition = current_volume >= min_volume

    # Detect crossover
    bullish_cross = (fast_prev <= slow_prev) and (fast_current > slow_current)
    bearish_cross = (fast_prev >= slow_prev) and (fast_current < slow_current)

    if bullish_cross and volume_condition:
        signal = True
        signal_type = 'BUY'
        metrics = {
            'ema_10': float(fast_current),
            'ema_20': float(slow_current),
            'price': float(close.iloc[-1]),
            'volume': float(current_volume),
            'gap_percent': float((fast_current - slow_current) / slow_current * 100),
            'signal_strength': min(100, abs(float((fast_current - slow_current) / slow_current * 100)) * 20)
        }
    elif bearish_cross and volume_condition:
        signal = True
        signal_type = 'SELL'
        metrics = {
            'ema_10': float(fast_current),
            'ema_20': float(slow_current),
            'price': float(close.iloc[-1]),
            'volume': float(current_volume),
            'gap_percent': float((fast_current - slow_current) / slow_current * 100),
            'signal_strength': min(100, abs(float((fast_current - slow_current) / slow_current * 100)) * 20)
        }
    else:
        signal = False
''',
            'default_params': {'fast_period': 10, 'slow_period': 20, 'min_volume': 1000000}
        },
        {
            'name': 'RSI Oversold',
            'description': 'Scan for stocks with RSI below 30',
            'code': '''
# RSI Oversold Scanner
def scan(data, params):
    rsi_period = params.get('rsi_period', 14)
    threshold = params.get('threshold', 30)

    # Calculate RSI
    rsi = talib.RSI(data['close'], timeperiod=rsi_period)

    # Check if current RSI is below threshold
    if rsi.iloc[-1] < threshold:
        return {
            'signal': 'BUY',
            'metrics': {
                'rsi': float(rsi.iloc[-1]),
                'price': float(data['close'].iloc[-1])
            }
        }

    return None
''',
            'default_params': {'rsi_period': 14, 'threshold': 30}
        },
        {
            'name': 'MACD Crossover',
            'description': 'Detect MACD signal line crossovers',
            'code': '''
# MACD Crossover Scanner
def scan(data, params):
    fast = params.get('fast_period', 12)
    slow = params.get('slow_period', 26)
    signal = params.get('signal_period', 9)

    # Calculate MACD
    macd, macd_signal, macd_hist = talib.MACD(
        data['close'],
        fastperiod=fast,
        slowperiod=slow,
        signalperiod=signal
    )

    # Check for bullish crossover
    if len(macd_hist) >= 2:
        if macd_hist.iloc[-2] < 0 and macd_hist.iloc[-1] > 0:
            return {
                'signal': 'BUY',
                'metrics': {
                    'macd': float(macd.iloc[-1]),
                    'signal': float(macd_signal.iloc[-1]),
                    'histogram': float(macd_hist.iloc[-1]),
                    'price': float(data['close'].iloc[-1])
                }
            }

    return None
''',
            'default_params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        },
        {
            'name': 'Volume Breakout',
            'description': 'Identify stocks with volume breakouts',
            'code': '''
# Volume Breakout Scanner
def scan(data, params):
    volume_multiplier = params.get('volume_multiplier', 2.0)
    price_change = params.get('price_change', 0.02)

    # Calculate average volume
    avg_volume = data['volume'].rolling(window=20).mean()

    # Check for volume breakout with price increase
    current_volume = data['volume'].iloc[-1]
    current_price = data['close'].iloc[-1]
    prev_price = data['close'].iloc[-2]

    if current_volume > avg_volume.iloc[-1] * volume_multiplier:
        price_pct_change = (current_price - prev_price) / prev_price
        if price_pct_change > price_change:
            return {
                'signal': 'BUY',
                'metrics': {
                    'volume': float(current_volume),
                    'avg_volume': float(avg_volume.iloc[-1]),
                    'volume_ratio': float(current_volume / avg_volume.iloc[-1]),
                    'price_change': float(price_pct_change * 100),
                    'price': float(current_price)
                }
            }

    return None
''',
            'default_params': {'volume_multiplier': 2.0, 'price_change': 0.02}
        }
    ]

    for template_data in templates:
        if not ScannerTemplate.query.filter_by(name=template_data['name']).first():
            template = ScannerTemplate(**template_data)
            db.session.add(template)

    # Create sample watchlists
    watchlists = [
        {
            'name': 'NIFTY 50',
            'description': 'Top 50 stocks from NSE',
            'exchange': 'NSE',
            'symbols': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK']
        },
        {
            'name': 'Banking Sector',
            'description': 'Major banking stocks',
            'exchange': 'NSE',
            'symbols': ['HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN', 'INDUSINDBK', 'BANDHANBNK', 'FEDERALBNK', 'IDFCFIRSTB', 'PNB']
        },
        {
            'name': 'IT Sector',
            'description': 'Information Technology stocks',
            'exchange': 'NSE',
            'symbols': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTI', 'MINDTREE', 'MPHASIS', 'COFORGE', 'PERSISTENT']
        }
    ]

    for wl_data in watchlists:
        if not Watchlist.query.filter_by(name=wl_data['name']).first():
            watchlist = Watchlist(
                name=wl_data['name'],
                description=wl_data['description'],
                exchange=wl_data['exchange']
            )
            watchlist.set_symbols(wl_data['symbols'])
            db.session.add(watchlist)

    # Create sample scanners
    scanners = [
        {
            'name': '10/20 EMA Crossover',
            'description': 'Detects when 10 EMA crosses above or below 20 EMA',
            'scanner_type': 'custom',
            'is_active': True,
            'timeframe': '15m',
            'code': templates[0]['code'],
            'params': templates[0]['default_params']
        },
        {
            'name': 'RSI Oversold Scanner',
            'description': 'Find stocks with RSI below 30',
            'scanner_type': 'custom',
            'is_active': True,
            'timeframe': '1h',
            'code': templates[1]['code'],
            'params': templates[1]['default_params']
        },
        {
            'name': 'MACD Bullish',
            'description': 'Detect bullish MACD crossovers',
            'scanner_type': 'custom',
            'is_active': True,
            'timeframe': 'D',
            'code': templates[2]['code'],
            'params': templates[2]['default_params']
        },
        {
            'name': 'Volume Breakout',
            'description': 'Identify stocks with volume breakouts',
            'scanner_type': 'custom',
            'is_active': True,
            'timeframe': '5m',
            'code': templates[3]['code'],
            'params': templates[3]['default_params']
        }
    ]

    for scanner_data in scanners:
        if not Scanner.query.filter_by(name=scanner_data['name']).first():
            params = scanner_data.pop('params', {})
            scanner = Scanner(**scanner_data)
            scanner.set_parameters(params)
            db.session.add(scanner)

    db.session.commit()
    print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()