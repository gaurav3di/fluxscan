#!/usr/bin/env python3
"""
Test OpenAlgo with the correct API key
"""

from openalgo import api
import pandas as pd
from datetime import datetime, timedelta

# Your correct API key
API_KEY = '517f37716c227360c0526acb18505d6892a3252380d31160dd7603ff6b35626d'
HOST = 'http://127.0.0.1:5000'

print("Testing with correct API key")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...")
print(f"Host: {HOST}")
print()

# Initialize client with correct key
client = api(api_key=API_KEY, host=HOST)

# Test 1: intervals
print("1. Testing intervals()...")
try:
    response = client.intervals()
    if isinstance(response, dict):
        if response.get('status') == 'success':
            print("   [SUCCESS] Got intervals!")
            data = response.get('data', {})
            for key, values in data.items():
                if values:
                    print(f"   {key}: {values}")
        else:
            print(f"   [ERROR] {response.get('message', 'Unknown')}")
    else:
        print(f"   Response: {response}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: history
print("\n2. Testing history()...")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)

    response = client.history(
        symbol="RELIANCE",
        exchange="NSE",
        interval="5m",
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

    if isinstance(response, pd.DataFrame):
        print("   [SUCCESS] Got historical data!")
        print(f"   Shape: {response.shape}")
        print(f"   Columns: {list(response.columns)}")
        if len(response) > 0:
            print(f"   Date range: {response.index[0]} to {response.index[-1]}")
    elif isinstance(response, dict):
        print(f"   [ERROR] {response.get('message', 'Unknown')}")
    else:
        print(f"   Response: {response}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: quotes
print("\n3. Testing quotes()...")
try:
    response = client.quotes(symbol="RELIANCE", exchange="NSE")
    if isinstance(response, dict):
        if response.get('status') == 'success':
            print("   [SUCCESS] Got quote!")
            data = response.get('data', {})
            for key, value in list(data.items())[:3]:
                print(f"   {key}: {value}")
        else:
            print(f"   [ERROR] {response.get('message', 'Unknown')}")
    else:
        print(f"   Response: {response}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "=" * 60)
print("If all tests pass, update your system environment variable:")
print("1. Close all terminals")
print("2. Set OPENALGO_API_KEY system variable to the correct key")
print("3. Or remove the system variable to use .env file")
print("=" * 60)