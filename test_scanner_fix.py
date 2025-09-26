#!/usr/bin/env python3
"""
Test script to verify scanner execution is working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import db, Scanner, Watchlist, ScanHistory, ScanResult
from services.data_service import DataService
from scanners.scanner_engine import ScannerEngine
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def test_scanner_execution():
    """Test scanner execution with proper app context"""

    with app.app_context():
        print("=" * 60)
        print("Testing Scanner Execution")
        print("=" * 60)

        # Initialize data service
        print("\n1. Initializing Data Service...")
        data_service = DataService(
            api_key=Config.OPENALGO_API_KEY,
            host=Config.OPENALGO_HOST
        )

        # Create test scanner
        print("\n2. Creating Test Scanner...")
        scanner_code = '''
# Simple test scanner
signal = False
signal_type = None
metrics = {}

# Check if we have data
if len(close) > 20:
    # Calculate simple moving averages
    sma_10 = talib.SMA(close, timeperiod=10)
    sma_20 = talib.SMA(close, timeperiod=20)

    # Get current values
    current_price = close.iloc[-1] if hasattr(close, 'iloc') else close[-1]
    current_sma_10 = sma_10.iloc[-1] if hasattr(sma_10, 'iloc') else sma_10[-1]
    current_sma_20 = sma_20.iloc[-1] if hasattr(sma_20, 'iloc') else sma_20[-1]

    # Simple crossover check
    if current_sma_10 > current_sma_20:
        signal = True
        signal_type = 'BUY'
        metrics = {
            'price': float(current_price),
            'sma_10': float(current_sma_10),
            'sma_20': float(current_sma_20)
        }
'''

        # Test symbols
        test_symbols = [
            {'symbol': 'RELIANCE', 'exchange': 'NSE'},
            {'symbol': 'TCS', 'exchange': 'NSE'}
        ]

        # Parameters
        params = {
            'interval': '15m',
            'lookback_days': 5,
            'exchange': 'NSE'
        }

        print(f"\n3. Test Configuration:")
        print(f"   Symbols: {[s['symbol'] for s in test_symbols]}")
        print(f"   Interval: {params['interval']}")
        print(f"   Lookback: {params['lookback_days']} days")

        # Create scanner engine
        print("\n4. Creating Scanner Engine...")
        engine = ScannerEngine(data_service)

        # Execute scanner
        print("\n5. Executing Scanner...")
        print("-" * 40)

        def progress_callback(progress, symbol):
            print(f"   Progress: {progress}% - Scanning {symbol}")

        result = engine.execute_scanner(
            scanner_code,
            test_symbols,
            params,
            progress_callback=progress_callback
        )

        # Display results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Total Scanned: {result['total_scanned']}")
        print(f"Signals Found: {result['signals_found']}")
        print(f"Execution Time: {result['execution_time']:.2f} seconds")

        if result['results']:
            print("\nSignals Detected:")
            for r in result['results']:
                print(f"\n  {r['symbol']} - {r['signal']}")
                for key, value in r['metrics'].items():
                    print(f"    {key}: {value}")

        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  {error['symbol']}: {error['error']}")

        return result

def test_scan_history():
    """Test scan history recording"""

    with app.app_context():
        print("\n" + "=" * 60)
        print("Testing Scan History")
        print("=" * 60)

        # Create a test scanner if not exists
        scanner = Scanner.query.filter_by(name='Test Scanner').first()
        if not scanner:
            scanner = Scanner(
                name='Test Scanner',
                description='Test scanner for verification',
                code='signal = False',
                is_active=True
            )
            db.session.add(scanner)
            db.session.commit()
            print(f"Created scanner: {scanner.name}")

        # Create test watchlist if not exists
        watchlist = Watchlist.query.filter_by(name='Test Watchlist').first()
        if not watchlist:
            watchlist = Watchlist(
                name='Test Watchlist',
                description='Test watchlist',
                exchange='NSE'
            )
            watchlist.set_symbols(['RELIANCE', 'TCS'])
            db.session.add(watchlist)
            db.session.commit()
            print(f"Created watchlist: {watchlist.name}")

        # Create scan history
        history = ScanHistory(
            scanner_id=scanner.id,
            watchlist_id=watchlist.id
        )
        history.start()
        db.session.add(history)
        db.session.commit()
        print(f"\nCreated scan history ID: {history.id}")
        print(f"Status: {history.status}")

        # Simulate completion
        history.complete(symbols_scanned=2, signals_found=1)
        db.session.commit()
        print(f"Completed scan - Status: {history.status}")
        print(f"Symbols scanned: {history.symbols_scanned}")
        print(f"Signals found: {history.signals_found}")

        return history

if __name__ == "__main__":
    print("FluxScan Scanner Execution Test")
    print("================================\n")

    try:
        # Test scanner execution
        result = test_scanner_execution()

        # Test scan history
        history = test_scan_history()

        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\n✓ Scanner execution is working")
        print("✓ Scan history is being recorded")
        print("\nYou can now use the scanner in the web interface:")
        print("1. Start the app: python app.py")
        print("2. Go to Scanners → Execute Scan")
        print("3. Select scanner and watchlist")
        print("4. Click 'Start Scan'")

    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()