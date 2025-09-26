#!/usr/bin/env python3
"""
Simple EMA Scanner Test (Windows-safe version)
"""

import sys
import os
import pandas as pd
import talib

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.data_service import DataService
from scanners.scanner_engine import ScannerEngine
from models import db
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
        {'symbol': 'TCS', 'exchange': 'NSE'}
    ]

    # Scanner parameters
    params = {
        'fast_period': 10,
        'slow_period': 20,
        'min_volume': 100000,
        'interval': '15m',
        'lookback_days': 5
    }

    print(f"\n2. Test Configuration:")
    print(f"   - Symbols: {[s['symbol'] for s in test_symbols]}")
    print(f"   - Timeframe: {params['interval']}")
    print(f"   - Lookback: {params['lookback_days']} days")

    # EMA Scanner Code
    scanner_code = '''
# 10/20 EMA Crossover Scanner
fast_period = params.get('fast_period', 10)
slow_period = params.get('slow_period', 20)
min_volume = params.get('min_volume', 100000)

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
            'volume': float(current_volume)
        }
    elif bearish_cross and volume_condition:
        signal = True
        signal_type = 'SELL'
        metrics = {
            'ema_10': float(fast_current),
            'ema_20': float(slow_current),
            'price': float(close.iloc[-1]),
            'volume': float(current_volume)
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

    def progress_callback(progress, symbol):
        print(f"   Progress: {progress}% - Scanning {symbol}")

    result = engine.execute_scanner(
        scanner_code,
        test_symbols,
        params,
        progress_callback=progress_callback
    )

    # Summary
    print("\n" + "=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Symbols Scanned: {result['total_scanned']}")
    print(f"Signals Found: {result['signals_found']}")
    print(f"Execution Time: {result['execution_time']:.2f} seconds")

    if result['results']:
        print("\nSIGNALS DETECTED:")
        for r in result['results']:
            print(f"\n{r['symbol']} - {r['signal']}")
            for key, value in r['metrics'].items():
                print(f"  {key}: {value}")

    if result['errors']:
        print("\nERRORS:")
        for error in result['errors']:
            print(f"  {error}")

    return result

if __name__ == "__main__":
    with app.app_context():
        print("FluxScan - EMA Scanner Test")
        print("============================\n")

        try:
            result = test_ema_scanner()
            print("\n[SUCCESS] Test completed!")
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()