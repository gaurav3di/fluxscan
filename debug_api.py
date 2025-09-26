#!/usr/bin/env python3
"""
Debug OpenAlgo API connection
"""

import os
import sys
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openalgo_connection():
    """Test OpenAlgo API directly"""

    print("=" * 60)
    print("OpenAlgo API Debug Test")
    print("=" * 60)

    # Get credentials from environment
    api_key = os.getenv('OPENALGO_API_KEY', '')
    host = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')

    print(f"\n1. Environment Variables:")
    print(f"   API Key: {api_key[:20]}..." if len(api_key) > 20 else f"   API Key: {api_key}")
    print(f"   API Key Length: {len(api_key)} characters")
    print(f"   Host: {host}")

    # Check for common issues
    print(f"\n2. Checking for Common Issues:")
    if not api_key:
        print("   [ERROR] API key is empty!")
        return

    if api_key.startswith(' ') or api_key.endswith(' '):
        print("   [WARNING] API key has leading/trailing spaces")
        api_key = api_key.strip()
        print(f"   Trimmed API key: {api_key}")

    if 'your_api_key_here' in api_key:
        print("   [ERROR] API key is still the placeholder value!")
        return

    print("   [OK] API key format looks OK")

    # Test direct HTTP connection
    print(f"\n3. Testing Direct HTTP Connection:")

    # First test if server is reachable
    try:
        with httpx.Client() as client:
            print(f"   Testing server at {host}...")
            response = client.get(f"{host}/")
            print(f"   Server response: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Cannot reach server: {e}")
        print(f"   Make sure OpenAlgo is running at {host}")
        return

    # Test with intervals endpoint (doesn't require auth on some versions)
    try:
        with httpx.Client() as client:
            print(f"\n4. Testing /intervals endpoint:")
            headers = {
                'Content-Type': 'application/json',
                'X-API-KEY': api_key  # Some versions use header
            }

            # Try with API key in header
            response = client.get(f"{host}/api/v1/intervals", headers=headers)
            print(f"   Response (with header): {response.status_code}")
            if response.status_code == 200:
                print(f"   Data: {response.json()}")
            else:
                print(f"   Error: {response.text[:200]}")

            # Try with API key as parameter
            print(f"\n5. Testing with API key as parameter:")
            response = client.get(f"{host}/api/v1/intervals", params={'apikey': api_key})
            print(f"   Response (with param): {response.status_code}")
            if response.status_code == 200:
                print(f"   Data: {response.json()}")
            else:
                print(f"   Error: {response.text[:200]}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test OpenAlgo Python SDK directly
    print(f"\n6. Testing OpenAlgo Python SDK:")
    try:
        from openalgo import api as openalgo_api

        # Try initializing the client
        client = openalgo_api(api_key=api_key, host=host)
        print(f"   Client initialized successfully")

        # Try getting intervals
        print(f"\n   Testing intervals() method:")
        result = client.intervals()
        print(f"   Result: {result}")

        # If intervals worked, try a simple quote
        if isinstance(result, dict) and result.get('status') != 'error':
            print(f"\n   Testing quotes() method:")
            quote_result = client.quotes(symbol='RELIANCE', exchange='NSE')
            print(f"   Quote result: {quote_result}")

    except Exception as e:
        print(f"   SDK Error: {e}")
        import traceback
        traceback.print_exc()

    # Check OpenAlgo SDK version
    print(f"\n7. Checking OpenAlgo SDK Version:")
    try:
        import openalgo
        if hasattr(openalgo, '__version__'):
            print(f"   OpenAlgo version: {openalgo.__version__}")
        else:
            print(f"   OpenAlgo version: Unknown (check if latest)")
    except:
        print(f"   Could not determine version")

    # Test alternative authentication methods
    print(f"\n8. Testing Alternative Auth Methods:")

    test_urls = [
        f"{host}/api/v1/intervals",
        f"{host}/api/intervals",
        f"{host}/intervals",
    ]

    auth_methods = [
        {'headers': {'apikey': api_key}},
        {'headers': {'x-api-key': api_key}},
        {'headers': {'X-API-KEY': api_key}},
        {'headers': {'Authorization': f'Bearer {api_key}'}},
        {'params': {'apikey': api_key}},
        {'params': {'api_key': api_key}},
    ]

    with httpx.Client() as client:
        for url in test_urls:
            for i, auth in enumerate(auth_methods):
                try:
                    if 'headers' in auth:
                        response = client.get(url, headers=auth['headers'])
                    else:
                        response = client.get(url, params=auth['params'])

                    if response.status_code == 200:
                        print(f"   [SUCCESS] Found working auth with URL: {url}")
                        print(f"     Auth method: {list(auth.keys())[0]} = {list(auth.values())[0]}")
                        print(f"     Response: {response.text[:100]}")
                        return
                except:
                    pass

    print(f"\n   [FAILED] None of the auth methods worked")
    print(f"\nPossible Issues:")
    print(f"1. API key format might be different than expected")
    print(f"2. OpenAlgo server version might require different auth")
    print(f"3. Check OpenAlgo server logs for more details")

if __name__ == "__main__":
    test_openalgo_connection()

    print(f"\n" + "=" * 60)
    print("Debug Complete")
    print("=" * 60)
    print("\nIf API key is correct but still failing:")
    print("1. Check OpenAlgo server logs for the exact error")
    print("2. Verify the API key format (some versions use different formats)")
    print("3. Make sure the OpenAlgo server is properly configured")
    print("4. Try regenerating the API key in OpenAlgo")