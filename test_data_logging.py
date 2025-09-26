#!/usr/bin/env python3
"""
Test data download with logging to see head of historical data
"""

import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console output
    ]
)

from config import Config
from services.data_service import DataService
from datetime import datetime

def test_data_download_with_logging():
    """Test data download and see the head of data"""

    print("=" * 60)
    print("Testing Data Download with Logging")
    print("=" * 60)
    print()

    # Initialize data service
    data_service = DataService(
        api_key=Config.OPENALGO_API_KEY,
        host=Config.OPENALGO_HOST
    )

    # Test different symbols and timeframes
    test_cases = [
        {'symbol': 'RELIANCE', 'exchange': 'NSE', 'interval': '5m', 'lookback_days': 2},
        {'symbol': 'TCS', 'exchange': 'NSE', 'interval': '15m', 'lookback_days': 3},
        {'symbol': 'INFY', 'exchange': 'NSE', 'interval': 'D', 'lookback_days': 10}
    ]

    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Fetching: {test['symbol']} ({test['exchange']})")
        print(f"Interval: {test['interval']}, Lookback: {test['lookback_days']} days")
        print(f"{'='*60}")

        # Fetch data - this will trigger logging
        data = data_service.get_historical_data(
            symbol=test['symbol'],
            exchange=test['exchange'],
            interval=test['interval'],
            lookback_days=test['lookback_days']
        )

        if data is not None and not data.empty:
            print(f"\n[SUCCESS] Data fetched successfully")

            # Additional analysis
            print(f"\nQuick Statistics:")
            print(f"  Close price range: {data['close'].min():.2f} - {data['close'].max():.2f}")
            print(f"  Average volume: {data['volume'].mean():,.0f}")
            print(f"  Total rows: {len(data)}")
        else:
            print(f"\n[FAILED] No data received")

        print()

if __name__ == "__main__":
    print("FluxScan - Data Download Test with Logging")
    print("=" * 60)
    print("This will show the head of historical data for each request")
    print()

    test_data_download_with_logging()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nThe logging shows:")
    print("- Data shape and columns")
    print("- Date range of data")
    print("- First 5 rows of each dataset")
    print("\nCheck 'fluxscan.log' file for persistent logs")