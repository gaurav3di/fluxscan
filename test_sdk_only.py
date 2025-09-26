#!/usr/bin/env python3
"""
Test OpenAlgo SDK connection using only SDK methods as per documentation
"""

import os
from dotenv import load_dotenv
from openalgo import api
import openalgo
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

def test_openalgo_sdk():
    """Test OpenAlgo using SDK methods only"""

    print("=" * 60)
    print("OpenAlgo SDK Test (Using SDK Methods Only)")
    print("=" * 60)

    # Get credentials
    api_key = os.getenv('OPENALGO_API_KEY', '')
    host = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')

    print(f"\n1. Configuration:")
    print(f"   API Key: {api_key[:20]}..." if len(api_key) > 20 else f"   API Key: {api_key}")
    print(f"   Host: {host}")
    print(f"   OpenAlgo Version: {openalgo.__version__ if hasattr(openalgo, '__version__') else 'Unknown'}")

    # Initialize client as per documentation
    print(f"\n2. Initializing Client (as per SDK docs)...")
    try:
        client = api(api_key=api_key, host=host)
        print("   [OK] Client initialized")
    except Exception as e:
        print(f"   [ERROR] Failed to initialize: {e}")
        return

    # Test 1: intervals() - Should return available intervals
    print(f"\n3. Testing intervals() method...")
    try:
        response = client.intervals()
        print(f"   Response type: {type(response)}")
        if isinstance(response, dict):
            print(f"   Status: {response.get('status', 'Unknown')}")
            if response.get('status') == 'success':
                data = response.get('data', {})
                print(f"   Available intervals:")
                for key, values in data.items():
                    if values:
                        print(f"      {key}: {values}")
            else:
                print(f"   Error: {response.get('message', 'Unknown error')}")
        else:
            print(f"   Response: {response}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # Test 2: quotes() - Get quote for a symbol
    print(f"\n4. Testing quotes() method...")
    try:
        response = client.quotes(symbol="RELIANCE", exchange="NSE")
        print(f"   Response type: {type(response)}")
        if isinstance(response, dict):
            print(f"   Status: {response.get('status', 'Unknown')}")
            if response.get('status') == 'success':
                data = response.get('data', {})
                print(f"   Quote data (first 3 fields):")
                for key, value in list(data.items())[:3]:
                    print(f"      {key}: {value}")
            else:
                print(f"   Error: {response.get('message', 'Unknown error')}")
        else:
            print(f"   Response: {response}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # Test 3: history() - Get historical data
    print(f"\n5. Testing history() method...")
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

        print(f"   Response type: {type(response)}")

        # According to docs, history returns a DataFrame
        import pandas as pd
        if isinstance(response, pd.DataFrame):
            print(f"   [SUCCESS] Received DataFrame")
            print(f"   Shape: {response.shape}")
            print(f"   Columns: {list(response.columns)}")
            print(f"   Date range: {response.index[0]} to {response.index[-1]}" if len(response) > 0 else "Empty")
            if len(response) > 0:
                print(f"\n   Last 2 rows:")
                print(response.tail(2).to_string())
        elif isinstance(response, dict):
            print(f"   Status: {response.get('status', 'Unknown')}")
            print(f"   Message: {response.get('message', 'No message')}")
            if response.get('code'):
                print(f"   Code: {response.get('code')}")
        else:
            print(f"   Unexpected response: {response}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # Test 4: symbol() - Get symbol info
    print(f"\n6. Testing symbol() method...")
    try:
        response = client.symbol(symbol="RELIANCE", exchange="NSE")
        print(f"   Response type: {type(response)}")
        if isinstance(response, dict):
            print(f"   Status: {response.get('status', 'Unknown')}")
            if response.get('status') == 'success':
                data = response.get('data', {})
                print(f"   Symbol info (first 3 fields):")
                for key, value in list(data.items())[:3]:
                    print(f"      {key}: {value}")
            else:
                print(f"   Error: {response.get('message', 'Unknown error')}")
        else:
            print(f"   Response: {response}")
    except Exception as e:
        print(f"   [ERROR] {e}")

    # Test 5: search() - Search for symbols
    print(f"\n7. Testing search() method...")
    try:
        response = client.search(query="RELIANCE", exchange="NSE")
        print(f"   Response type: {type(response)}")
        if isinstance(response, dict):
            print(f"   Status: {response.get('status', 'Unknown')}")
            if response.get('status') == 'success':
                data = response.get('data', [])
                print(f"   Found {len(data)} results")
                if data and len(data) > 0:
                    print(f"   First result: {data[0].get('symbol', 'Unknown')}")
            else:
                print(f"   Error: {response.get('message', 'Unknown error')}")
        else:
            print(f"   Response: {response}")
    except Exception as e:
        print(f"   [ERROR] {e}")

def diagnose_issue():
    """Diagnose the connection issue"""

    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)

    api_key = os.getenv('OPENALGO_API_KEY', '')
    host = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')

    issues = []

    # Check API key
    if not api_key:
        issues.append("API key is empty in .env file")
    elif api_key == 'your_api_key_here':
        issues.append("API key is still the placeholder value")
    elif len(api_key) != 64:
        issues.append(f"API key length is {len(api_key)}, expected 64 characters")

    # Check host
    if not host:
        issues.append("Host is not set")

    # Try to connect to host
    import httpx
    try:
        with httpx.Client() as client:
            response = client.get(host, timeout=5)
            if response.status_code == 200:
                print(f"[OK] Server is reachable at {host}")
            else:
                issues.append(f"Server returned status {response.status_code}")
    except Exception as e:
        issues.append(f"Cannot reach server at {host}: {e}")

    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nNo obvious issues found.")
        print("The API key might be:")
        print("  1. Invalid or expired")
        print("  2. For a different OpenAlgo instance")
        print("  3. Not properly configured in OpenAlgo server")

    print("\nRecommended steps:")
    print("1. Login to OpenAlgo web interface")
    print("2. Go to API settings or Profile")
    print("3. Generate a new API key")
    print("4. Update the .env file with the new key")
    print("5. Restart FluxScan")

if __name__ == "__main__":
    test_openalgo_sdk()
    diagnose_issue()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)