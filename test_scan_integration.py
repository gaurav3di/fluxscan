#!/usr/bin/env python3
"""
Integration test for scanner execution
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import db, Scanner, Watchlist, ScanHistory, ScanResult
from services.data_service import DataService
from datetime import datetime
import time
import httpx
import json

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def test_via_api():
    """Test scanner execution via API"""

    print("=" * 60)
    print("Testing Scanner via API")
    print("=" * 60)

    base_url = "http://localhost:5001"

    with app.app_context():
        # Ensure we have a scanner
        scanner = Scanner.query.filter_by(name='10/20 EMA Crossover').first()
        if not scanner:
            # Create the scanner
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
            scanner = Scanner(
                name='10/20 EMA Crossover',
                description='Detects EMA crossovers',
                code=scanner_code,
                is_active=True
            )
            scanner.set_parameters({
                'fast_period': 10,
                'slow_period': 20,
                'min_volume': 100000
            })
            db.session.add(scanner)
            db.session.commit()
            print(f"Created scanner: {scanner.name} (ID: {scanner.id})")
        else:
            print(f"Using existing scanner: {scanner.name} (ID: {scanner.id})")

        # Ensure we have a watchlist
        watchlist = Watchlist.query.filter_by(name='Test Stocks').first()
        if not watchlist:
            watchlist = Watchlist(
                name='Test Stocks',
                description='Test watchlist for scanner',
                exchange='NSE'
            )
            # Set symbols with exchange
            watchlist.set_symbols([
                {'symbol': 'RELIANCE', 'exchange': 'NSE'},
                {'symbol': 'TCS', 'exchange': 'NSE'},
                {'symbol': 'INFY', 'exchange': 'NSE'}
            ])
            db.session.add(watchlist)
            db.session.commit()
            print(f"Created watchlist: {watchlist.name} (ID: {watchlist.id})")
        else:
            print(f"Using existing watchlist: {watchlist.name} (ID: {watchlist.id})")

        scanner_id = scanner.id
        watchlist_id = watchlist.id

    # Now test the API
    print("\nTesting Scanner API...")

    with httpx.Client() as client:
        # Execute scan
        payload = {
            'scanner_id': scanner_id,
            'watchlist_id': watchlist_id,
            'parameters': {
                'interval': '15m',
                'lookback_days': 5,
                'exchange': 'NSE',
                'fast_period': 10,
                'slow_period': 20,
                'min_volume': 100000
            }
        }

        print(f"\n1. Starting scan...")
        print(f"   Scanner ID: {scanner_id}")
        print(f"   Watchlist ID: {watchlist_id}")
        print(f"   Parameters: {payload['parameters']}")

        try:
            response = client.post(f"{base_url}/scanners/api/scan", json=payload)
            if response.status_code == 200:
                result = response.json()
                scan_id = result.get('scan_id')
                print(f"   ✓ Scan started: {scan_id}")

                # Poll for status
                print("\n2. Checking scan status...")
                max_polls = 30
                for i in range(max_polls):
                    time.sleep(2)
                    status_response = client.get(f"{base_url}/scanners/api/scan/{scan_id}/status")
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"   Poll {i+1}: Status={status['status']}, Progress={status.get('progress', 0)}%")

                        if status['status'] in ['completed', 'failed', 'cancelled']:
                            print(f"\n3. Scan {status['status']}!")
                            if status['status'] == 'completed':
                                print(f"   Symbols scanned: {status.get('symbols_scanned', 0)}")
                                print(f"   Signals found: {status.get('signals_found', 0)}")

                                if status.get('results'):
                                    print("\n   Signals:")
                                    for r in status['results']:
                                        print(f"   - {r['symbol']}: {r['signal']}")
                            break
                else:
                    print("   ⚠ Scan timed out")
            else:
                print(f"   ✗ Failed to start scan: {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"   ✗ API Error: {e}")

def test_direct_execution():
    """Test scanner execution directly"""

    print("\n" + "=" * 60)
    print("Testing Direct Scanner Execution")
    print("=" * 60)

    with app.app_context():
        # Initialize services
        data_service = DataService(
            api_key=Config.OPENALGO_API_KEY,
            host=Config.OPENALGO_HOST
        )

        from scanners import ScannerEngine
        engine = ScannerEngine(data_service)

        # Simple test scanner
        scanner_code = '''
# Simple test
signal = False
if len(close) > 10:
    current_price = close.iloc[-1]
    sma_10 = talib.SMA(close, timeperiod=10)
    if len(sma_10) > 0:
        signal = True
        signal_type = 'INFO'
        metrics = {
            'price': float(current_price),
            'sma_10': float(sma_10.iloc[-1])
        }
'''

        # Test symbols
        symbols = [
            {'symbol': 'RELIANCE', 'exchange': 'NSE'},
            {'symbol': 'TCS', 'exchange': 'NSE'}
        ]

        params = {
            'interval': '5m',
            'lookback_days': 2
        }

        print("\nExecuting scanner directly...")
        result = engine.execute_scanner(scanner_code, symbols, params)

        print(f"\nResult:")
        print(f"  Status: {result['status']}")
        print(f"  Total scanned: {result['total_scanned']}")
        print(f"  Signals found: {result['signals_found']}")

        if result['results']:
            print("\n  Signals:")
            for r in result['results']:
                print(f"  - {r['symbol']}: {r['signal']}")
                for key, value in r['metrics'].items():
                    print(f"      {key}: {value}")

        if result['errors']:
            print("\n  Errors:")
            for e in result['errors']:
                print(f"  - {e}")

if __name__ == "__main__":
    print("FluxScan Scanner Integration Test")
    print("==================================\n")

    # Test direct execution first
    try:
        test_direct_execution()
    except Exception as e:
        print(f"\n✗ Direct test failed: {e}")
        import traceback
        traceback.print_exc()

    # Then test via API (requires server running)
    print("\n" + "=" * 60)
    print("Note: For API test, ensure server is running on port 5001")
    print("=" * 60)

    try:
        response = httpx.get("http://localhost:5001/")
        if response.status_code == 200:
            test_via_api()
        else:
            print("Server not responding properly")
    except:
        print("Server not running. Start with: python app.py")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)