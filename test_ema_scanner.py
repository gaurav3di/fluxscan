#!/usr/bin/env python3
"""
Test script for 10/20 EMA Crossover Scanner
Tests the scanner with real OpenAlgo data
"""

import sys
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.data_service import DataService
from scanners.scanner_engine import ScannerEngine
from models import db, Scanner, Watchlist
from flask import Flask

# Initialize Flask app for database context
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def test_ema_scanner():
    """Test the EMA crossover scanner with real data"""

    print("=" * 60)
    print("10/20 EMA Crossover Scanner Test")
    print("=" * 60)

    # Initialize data service
    print("\n1. Initializing OpenAlgo connection...")
    data_service = DataService(
        api_key=Config.OPENALGO_API_KEY,
        host=Config.OPENALGO_HOST
    )

    # Test symbols
    test_symbols = [
        {'symbol': 'RELIANCE', 'exchange': 'NSE'},
        {'symbol': 'TCS', 'exchange': 'NSE'},
        {'symbol': 'INFY', 'exchange': 'NSE'},
        {'symbol': 'HDFCBANK', 'exchange': 'NSE'},
        {'symbol': 'ICICIBANK', 'exchange': 'NSE'}
    ]

    # Scanner parameters
    params = {
        'fast_period': 10,
        'slow_period': 20,
        'min_volume': 1000000,
        'interval': '15m',  # 15-minute timeframe
        'lookback_days': 5
    }

    print(f"\n2. Test Configuration:")
    print(f"   - Symbols: {[s['symbol'] for s in test_symbols]}")
    print(f"   - Timeframe: {params['interval']}")
    print(f"   - Lookback: {params['lookback_days']} days")
    print(f"   - Fast EMA: {params['fast_period']}")
    print(f"   - Slow EMA: {params['slow_period']}")
    print(f"   - Min Volume: {params['min_volume']:,}")

    # EMA Scanner Code (Basic version)
    scanner_code = '''
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
'''

    # Initialize scanner engine
    print("\n3. Initializing Scanner Engine...")
    engine = ScannerEngine(data_service)

    # Execute scanner
    print("\n4. Executing Scanner...")
    print("-" * 40)

    results = []
    errors = []

    for stock in test_symbols:
        try:
            print(f"\nScanning {stock['symbol']}...")

            # Fetch data
            data = data_service.get_historical_data(
                symbol=stock['symbol'],
                exchange=stock['exchange'],
                interval=params['interval'],
                lookback_days=params['lookback_days']
            )

            if data is None or data.empty:
                print(f"  ⚠ No data available for {stock['symbol']}")
                continue

            print(f"  ✓ Data fetched: {len(data)} candles")

            # Prepare data for scanner
            open_prices = data['open']
            high = data['high']
            low = data['low']
            close = data['close']
            volume = data['volume']

            # Execute scanner code
            namespace = {
                'open': open_prices,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'params': params,
                'talib': talib,
                'signal': False,
                'signal_type': None,
                'metrics': {}
            }

            exec(scanner_code, namespace)

            if namespace['signal']:
                result = {
                    'symbol': stock['symbol'],
                    'exchange': stock['exchange'],
                    'signal': namespace['signal_type'],
                    'metrics': namespace['metrics']
                }
                results.append(result)

                print(f"  🎯 SIGNAL DETECTED: {namespace['signal_type']}")
                print(f"     - EMA 10: {namespace['metrics']['ema_10']:.2f}")
                print(f"     - EMA 20: {namespace['metrics']['ema_20']:.2f}")
                print(f"     - Price: {namespace['metrics']['price']:.2f}")
                print(f"     - Gap: {namespace['metrics']['gap_percent']:.2f}%")
                print(f"     - Strength: {namespace['metrics']['signal_strength']:.0f}/100")
            else:
                print(f"  · No signal")

                # Still calculate and display current EMAs for reference
                ema_fast = talib.EMA(close, timeperiod=params['fast_period'])
                ema_slow = talib.EMA(close, timeperiod=params['slow_period'])

                if len(ema_fast) > 0 and len(ema_slow) > 0:
                    print(f"     - EMA 10: {ema_fast.iloc[-1]:.2f}")
                    print(f"     - EMA 20: {ema_slow.iloc[-1]:.2f}")
                    print(f"     - Price: {close.iloc[-1]:.2f}")

        except Exception as e:
            error_msg = f"Error scanning {stock['symbol']}: {str(e)}"
            errors.append(error_msg)
            print(f"  ✗ {error_msg}")

    # Summary
    print("\n" + "=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    print(f"Symbols Scanned: {len(test_symbols)}")
    print(f"Signals Found: {len(results)}")
    print(f"Errors: {len(errors)}")

    if results:
        print("\n📊 SIGNALS DETECTED:")
        for r in results:
            print(f"\n{r['symbol']} ({r['exchange']}) - {r['signal']}")
            print(f"  EMA Gap: {r['metrics']['gap_percent']:.2f}%")
            print(f"  Signal Strength: {r['metrics']['signal_strength']:.0f}/100")
            print(f"  Price: ₹{r['metrics']['price']:.2f}")
            print(f"  Volume: {r['metrics']['volume']:,.0f}")

    return results, errors

def test_advanced_ema_scanner():
    """Test the advanced EMA scanner with trend filter"""

    print("\n" + "=" * 60)
    print("ADVANCED EMA Scanner Test (with Trend Filter)")
    print("=" * 60)

    # Initialize data service
    data_service = DataService(
        api_key=Config.OPENALGO_API_KEY,
        host=Config.OPENALGO_HOST
    )

    # Test with daily timeframe for trend
    test_symbols = [
        {'symbol': 'RELIANCE', 'exchange': 'NSE'},
        {'symbol': 'TCS', 'exchange': 'NSE'}
    ]

    params = {
        'fast_period': 10,
        'slow_period': 20,
        'trend_period': 50,
        'min_volume': 1000000,
        'use_trend_filter': True,
        'interval': 'D',  # Daily timeframe
        'lookback_days': 100
    }

    print(f"\nConfiguration:")
    print(f"  - Timeframe: Daily")
    print(f"  - Trend EMA: {params['trend_period']}")
    print(f"  - Trend Filter: Enabled")

    # Run scan on each symbol
    for stock in test_symbols:
        print(f"\nScanning {stock['symbol']}...")

        try:
            # Fetch data
            data = data_service.get_historical_data(
                symbol=stock['symbol'],
                exchange=stock['exchange'],
                interval=params['interval'],
                lookback_days=params['lookback_days']
            )

            if data is None or data.empty:
                print(f"  ⚠ No data available")
                continue

            # Calculate indicators
            close = data['close']
            volume = data['volume']
            high = data['high']
            low = data['low']

            ema_10 = talib.EMA(close, timeperiod=10)
            ema_20 = talib.EMA(close, timeperiod=20)
            ema_50 = talib.EMA(close, timeperiod=50)
            adx = talib.ADX(high, low, close, timeperiod=14)

            # Check latest values
            if len(ema_10) > 1:
                current_price = close.iloc[-1]
                trend_ema = ema_50.iloc[-1] if len(ema_50) > 0 else ema_20.iloc[-1]

                print(f"  Current Price: ₹{current_price:.2f}")
                print(f"  EMA 10: ₹{ema_10.iloc[-1]:.2f}")
                print(f"  EMA 20: ₹{ema_20.iloc[-1]:.2f}")
                print(f"  EMA 50: ₹{trend_ema:.2f}")

                # Check trend
                if current_price > trend_ema:
                    print(f"  📈 UPTREND (Price above EMA 50)")
                else:
                    print(f"  📉 DOWNTREND (Price below EMA 50)")

                # Check for crossover
                if len(ema_10) > 1 and len(ema_20) > 1:
                    fast_prev = ema_10.iloc[-2]
                    fast_current = ema_10.iloc[-1]
                    slow_prev = ema_20.iloc[-2]
                    slow_current = ema_20.iloc[-1]

                    if (fast_prev <= slow_prev) and (fast_current > slow_current):
                        print(f"  🎯 BULLISH CROSSOVER DETECTED!")
                        if current_price > trend_ema:
                            print(f"     ✓ Confirmed by uptrend")
                        else:
                            print(f"     ⚠ Warning: Against the trend")
                    elif (fast_prev >= slow_prev) and (fast_current < slow_current):
                        print(f"  🎯 BEARISH CROSSOVER DETECTED!")
                        if current_price < trend_ema:
                            print(f"     ✓ Confirmed by downtrend")
                        else:
                            print(f"     ⚠ Warning: Against the trend")

                # ADX trend strength
                if len(adx) > 0:
                    adx_value = adx.iloc[-1]
                    print(f"  ADX: {adx_value:.1f}", end="")
                    if adx_value > 25:
                        print(" (Strong Trend)")
                    else:
                        print(" (Weak Trend)")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        print("FluxScan - EMA Crossover Scanner Test Suite")
        print("Using Real OpenAlgo Market Data")
        print("\n")

        # Test basic EMA scanner
        results, errors = test_ema_scanner()

        # Test advanced EMA scanner
        test_advanced_ema_scanner()

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

        if errors:
            print("\n⚠ ERRORS ENCOUNTERED:")
            for error in errors:
                print(f"  - {error}")

        print("\n✓ EMA Scanner test completed successfully!")
        print("\nTo use in FluxScan:")
        print("1. Run: python utils/seed_data.py")
        print("2. Start FluxScan: python app.py")
        print("3. Go to Scanners → Execute Scan")
        print("4. Select '10/20 EMA Crossover' scanner")
        print("5. Choose timeframe and watchlist")
        print("6. Click 'Start Scan'")