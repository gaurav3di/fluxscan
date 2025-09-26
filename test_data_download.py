#!/usr/bin/env python3
"""
Test script to verify OpenAlgo data download
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.data_service import DataService
from datetime import datetime, timedelta
import pandas as pd

def test_data_download():
    """Test if historical data is being downloaded from OpenAlgo"""

    print("=" * 60)
    print("Testing OpenAlgo Data Download")
    print("=" * 60)

    # Initialize data service
    print("\n1. Initializing Data Service...")
    print(f"   API Key: {Config.OPENALGO_API_KEY[:10]}..." if Config.OPENALGO_API_KEY else "   API Key: NOT SET")
    print(f"   Host: {Config.OPENALGO_HOST}")

    data_service = DataService(
        api_key=Config.OPENALGO_API_KEY,
        host=Config.OPENALGO_HOST
    )

    # Test connection
    print("\n2. Testing Connection...")
    if data_service.test_connection():
        print("   [OK] Connection successful")
    else:
        print("   [ERROR] Connection failed - check API key and host")

    # Test intervals
    print("\n3. Getting Available Intervals...")
    intervals = data_service.get_available_intervals()
    print(f"   Available intervals: {intervals}")

    # Test historical data download
    test_configs = [
        {'symbol': 'RELIANCE', 'exchange': 'NSE', 'interval': '5m', 'lookback_days': 2},
        {'symbol': 'TCS', 'exchange': 'NSE', 'interval': '15m', 'lookback_days': 5},
        {'symbol': 'INFY', 'exchange': 'NSE', 'interval': 'D', 'lookback_days': 30}
    ]

    print("\n4. Testing Historical Data Download...")
    print("-" * 40)

    for config in test_configs:
        print(f"\nTesting: {config['symbol']} ({config['exchange']})")
        print(f"  Interval: {config['interval']}")
        print(f"  Lookback: {config['lookback_days']} days")

        try:
            # Get historical data
            data = data_service.get_historical_data(
                symbol=config['symbol'],
                exchange=config['exchange'],
                interval=config['interval'],
                lookback_days=config['lookback_days']
            )

            if data is not None and not data.empty:
                print(f"  [OK] Data downloaded successfully")
                print(f"       - Rows: {len(data)}")
                print(f"       - Columns: {list(data.columns)}")
                print(f"       - Date range: {data.index[0]} to {data.index[-1]}")

                # Show sample data
                print(f"\n  Sample data (last 3 rows):")
                print(data.tail(3).to_string(max_cols=6))

                # Check data quality
                print(f"\n  Data quality check:")
                print(f"       - Has nulls: {data.isnull().any().any()}")
                print(f"       - Volume > 0: {(data['volume'] > 0).all() if 'volume' in data else 'N/A'}")
                print(f"       - Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}" if 'close' in data else "N/A")
            else:
                print(f"  [WARNING] No data received")
                print(f"            Check if symbol exists and market data is available")

        except Exception as e:
            print(f"  [ERROR] Failed to download data: {str(e)}")

    # Test real-time quote
    print("\n\n5. Testing Real-time Quote...")
    print("-" * 40)

    test_symbols = ['RELIANCE', 'TCS']
    for symbol in test_symbols:
        print(f"\nGetting quote for {symbol}...")
        try:
            quote = data_service.get_quote(symbol, 'NSE')
            if quote:
                print(f"  [OK] Quote received")
                for key, value in list(quote.items())[:5]:  # Show first 5 fields
                    print(f"       {key}: {value}")
            else:
                print(f"  [WARNING] No quote data")
        except Exception as e:
            print(f"  [ERROR] {str(e)}")

    # Check if falling back to dummy data
    print("\n\n6. Checking Data Source...")
    print("-" * 40)

    # Try to get data and check if it's real or dummy
    test_data = data_service.get_historical_data('RELIANCE', 'NSE', '5m', 2)
    if test_data is not None and not test_data.empty:
        # Check for patterns that indicate dummy data
        close_prices = test_data['close'].values
        is_random = len(set(close_prices)) == len(close_prices)  # All unique values suggest random data

        if is_random and all(100 <= p <= 200 for p in close_prices[:10]):
            print("  [WARNING] Data appears to be DUMMY/RANDOM data")
            print("            OpenAlgo API may not be properly connected")
            print("\n  Troubleshooting:")
            print("  1. Check if OpenAlgo server is running")
            print("  2. Verify API key is correct in .env file")
            print("  3. Ensure OpenAlgo host URL is correct")
            print("  4. Check if broker is connected in OpenAlgo")
        else:
            print("  [OK] Data appears to be REAL market data")

def check_openalgo_direct():
    """Directly test OpenAlgo API"""
    print("\n\n" + "=" * 60)
    print("Direct OpenAlgo API Test")
    print("=" * 60)

    try:
        from openalgo import api as openalgo_api

        client = openalgo_api(
            api_key=Config.OPENALGO_API_KEY,
            host=Config.OPENALGO_HOST
        )

        # Test intervals endpoint
        print("\n1. Testing intervals endpoint...")
        response = client.intervals()
        print(f"   Response: {response}")

        # Test history endpoint
        print("\n2. Testing history endpoint...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)

        response = client.history(
            symbol='RELIANCE',
            exchange='NSE',
            interval='5m',
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        if isinstance(response, pd.DataFrame):
            print(f"   [OK] Received DataFrame with {len(response)} rows")
        else:
            print(f"   Response type: {type(response)}")
            print(f"   Response: {response}")

    except Exception as e:
        print(f"   [ERROR] Direct API test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("FluxScan - Data Download Test")
    print("==============================\n")

    try:
        # Run data download tests
        test_data_download()

        # Run direct API test
        check_openalgo_direct()

        print("\n\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print("\nIf you're seeing dummy data instead of real data:")
        print("1. Make sure OpenAlgo server is running")
        print("2. Check your .env file has correct OPENALGO_API_KEY")
        print("3. Verify OPENALGO_HOST is set correctly (e.g., http://127.0.0.1:5000)")
        print("4. Ensure your broker is connected in OpenAlgo")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()