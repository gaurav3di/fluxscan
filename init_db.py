#!/usr/bin/env python
"""
Database initialization script for FluxScan
Creates all tables and loads initial scanner templates
"""

from app import app, db
from models import Scanner, ScannerTemplate, Watchlist, Settings
from scanners.templates.momentum import macd, rsi
import sys

def init_database():
    """Initialize database with tables and default data"""
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully!")

        # Load scanner templates if not exist
        if ScannerTemplate.query.count() == 0:
            print("Loading scanner templates...")

            # MACD Template
            macd_template = ScannerTemplate(
                name="MACD Crossover",
                category="momentum",
                description=macd.description,
                code=macd.template_code
            )
            macd_template.set_parameters(macd.default_parameters)
            db.session.add(macd_template)

            # RSI Template
            rsi_template = ScannerTemplate(
                name="RSI Overbought/Oversold",
                category="momentum",
                description=rsi.description,
                code=rsi.template_code
            )
            rsi_template.set_parameters(rsi.default_parameters)
            db.session.add(rsi_template)

            # Bollinger Bands Template
            bb_template = ScannerTemplate(
                name="Bollinger Band Squeeze",
                category="volatility",
                description="Identifies Bollinger Band squeeze patterns indicating potential breakouts",
                code='''
# Bollinger Band Squeeze Scanner
bb_period = params.get('bb_period', 20)
bb_std = params.get('bb_std', 2)
squeeze_threshold = params.get('squeeze_threshold', 2)

if len(close) < bb_period:
    signal = False
else:
    upper, middle, lower = talib.BBANDS(close, timeperiod=bb_period, nbdevup=bb_std, nbdevdn=bb_std)

    if len(upper) > 0 and len(lower) > 0:
        bandwidth = (upper[-1] - lower[-1]) / middle[-1] * 100

        if bandwidth < squeeze_threshold:
            signal = True
            signal_type = 'WATCH'
            metrics = {
                'bandwidth': float(bandwidth),
                'upper_band': float(upper[-1]),
                'lower_band': float(lower[-1]),
                'middle_band': float(middle[-1]),
                'price': float(close[-1])
            }
        else:
            signal = False
    else:
        signal = False
'''
            )
            bb_template.set_parameters({
                'bb_period': 20,
                'bb_std': 2,
                'squeeze_threshold': 2
            })
            db.session.add(bb_template)

            # Moving Average Crossover Template
            ma_template = ScannerTemplate(
                name="Moving Average Crossover",
                category="trend",
                description="Identifies moving average crossovers for trend following",
                code='''
# Moving Average Crossover Scanner
fast_period = params.get('fast_period', 10)
slow_period = params.get('slow_period', 20)
ma_type = params.get('ma_type', 'SMA')

if len(close) < slow_period:
    signal = False
else:
    if ma_type == 'EMA':
        fast_ma = talib.EMA(close, timeperiod=fast_period)
        slow_ma = talib.EMA(close, timeperiod=slow_period)
    else:
        fast_ma = talib.SMA(close, timeperiod=fast_period)
        slow_ma = talib.SMA(close, timeperiod=slow_period)

    if len(fast_ma) >= 2 and len(slow_ma) >= 2:
        # Bullish crossover
        if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
            signal = True
            signal_type = 'BUY'
            metrics = {
                'fast_ma': float(fast_ma[-1]),
                'slow_ma': float(slow_ma[-1]),
                'price': float(close[-1])
            }
        # Bearish crossover
        elif fast_ma[-1] < slow_ma[-1] and fast_ma[-2] >= slow_ma[-2]:
            signal = True
            signal_type = 'SELL'
            metrics = {
                'fast_ma': float(fast_ma[-1]),
                'slow_ma': float(slow_ma[-1]),
                'price': float(close[-1])
            }
        else:
            signal = False
    else:
        signal = False
'''
            )
            ma_template.set_parameters({
                'fast_period': 10,
                'slow_period': 20,
                'ma_type': 'SMA'
            })
            db.session.add(ma_template)

            # Volume Breakout Template
            vol_template = ScannerTemplate(
                name="Volume Breakout",
                category="volume",
                description="Identifies significant volume spikes with price movement",
                code='''
# Volume Breakout Scanner
volume_multiplier = params.get('volume_multiplier', 2)
price_change_min = params.get('price_change_min', 2)
lookback = params.get('lookback', 20)

if len(close) < lookback or len(volume) < lookback:
    signal = False
else:
    avg_volume = talib.SMA(volume, timeperiod=lookback)
    price_change = ((close[-1] - close[-2]) / close[-2] * 100) if len(close) >= 2 else 0

    if volume[-1] > avg_volume[-1] * volume_multiplier and abs(price_change) > price_change_min:
        signal = True
        signal_type = 'BUY' if price_change > 0 else 'SELL'

        metrics = {
            'volume': float(volume[-1]),
            'avg_volume': float(avg_volume[-1]),
            'volume_ratio': float(volume[-1] / avg_volume[-1]),
            'price_change': float(price_change),
            'price': float(close[-1])
        }
    else:
        signal = False
'''
            )
            vol_template.set_parameters({
                'volume_multiplier': 2,
                'price_change_min': 2,
                'lookback': 20
            })
            db.session.add(vol_template)

            db.session.commit()
            print("Scanner templates loaded successfully!")

        # Create default watchlists if not exist
        if Watchlist.query.count() == 0:
            print("Creating default watchlists...")

            # NIFTY 50 Watchlist
            nifty50 = Watchlist(
                name="NIFTY 50",
                description="Top 50 large-cap Indian stocks",
                exchange="NSE"
            )
            nifty50.set_symbols([
                'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
                'HDFC', 'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK',
                'LT', 'AXISBANK', 'WIPRO', 'ASIANPAINT', 'MARUTI',
                'HCLTECH', 'BAJFINANCE', 'TITAN', 'ULTRACEMCO', 'NESTLEIND'
            ])
            db.session.add(nifty50)

            # High Volume Stocks
            high_volume = Watchlist(
                name="High Volume Stocks",
                description="Stocks with high trading volume",
                exchange="NSE"
            )
            high_volume.set_symbols([
                'SBIN', 'TATASTEEL', 'IDEA', 'YESBANK', 'TATAMOTORS',
                'BANKBARODA', 'PNB', 'VEDL', 'SAIL', 'BHEL'
            ])
            db.session.add(high_volume)

            db.session.commit()
            print("Default watchlists created!")

        # Set default settings
        print("Setting default application settings...")
        Settings.set('market_open_time', '09:15')
        Settings.set('market_close_time', '15:30')
        Settings.set('timezone', 'Asia/Kolkata')
        Settings.set('default_exchange', 'NSE')
        Settings.set('enable_notifications', True)

        print("\nDatabase initialization complete!")
        print("You can now run the application with: python app.py")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)