#!/usr/bin/env python3
"""
Test OpenAlgo authentication methods
"""

import httpx
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

api_key = os.getenv('OPENALGO_API_KEY')
host = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')

print("Testing OpenAlgo Authentication")
print("=" * 60)
print(f"Host: {host}")
print(f"API Key: {api_key[:20]}..." if api_key else "No API key")
print()

# Test different endpoints and auth methods
test_cases = [
    {
        'name': 'Intervals with apikey header',
        'url': f'`{host}/api/intervals',
        'headers': {'apikey': api_key},
        'method': 'GET'`
    },
    {
        'name': 'Intervals with Authorization Bearer',
        'url': f'{host}/api/intervals',
        'headers': {'Authorization': f'Bearer {api_key}'},
        'method': 'GET'
    },
    {
        'name': 'Intervals with query param',
        'url': f'{host}/api/intervals?apikey={api_key}',
        'headers': {},
        'method': 'GET'
    },
    {
        'name': 'History endpoint POST with apikey in body',
        'url': f'{host}/api/history',
        'headers': {'Content-Type': 'application/json'},
        'method': 'POST',
        'json': {
            'apikey': api_key,
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'interval': '5m',
            'start_date': '2025-09-25',
            'end_date': '2025-09-26'
        }
    },
    {
        'name': 'Data endpoint with apikey header',
        'url': f'{host}/api/data',
        'headers': {'apikey': api_key, 'Content-Type': 'application/json'},
        'method': 'POST',
        'json': {
            'symbol': 'RELIANCE',
            'exchange': 'NSE',
            'interval': '5m'
        }
    }
]

with httpx.Client(timeout=10) as client:
    for test in test_cases:
        print(f"Testing: {test['name']}")
        print(f"  URL: {test['url']}")

        try:
            if test['method'] == 'GET':
                response = client.get(test['url'], headers=test.get('headers', {}))
            else:
                response = client.post(
                    test['url'],
                    headers=test.get('headers', {}),
                    json=test.get('json', {})
                )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                print(f"  [SUCCESS] This auth method works!")
                try:
                    data = response.json()
                    print(f"  Response preview: {str(data)[:100]}...")
                except:
                    print(f"  Response: {response.text[:100]}...")
            elif response.status_code == 403:
                print(f"  [AUTH FAILED] {response.text[:100]}...")
            elif response.status_code == 404:
                print(f"  [NOT FOUND] Endpoint doesn't exist")
            else:
                print(f"  Response: {response.text[:100]}...")

        except Exception as e:
            print(f"  [ERROR] {str(e)}")

        print()

# Also try to find what endpoints are available
print("\nTrying to discover available endpoints...")
print("-" * 40)

common_endpoints = [
    '/api', '/api/v1', '/api/v2',
    '/intervals', '/api/intervals', '/api/v1/intervals',
    '/history', '/api/history', '/api/v1/history',
    '/data', '/api/data', '/api/v1/data',
    '/quotes', '/api/quotes', '/api/v1/quotes',
    '/healthcheck', '/status', '/ping'
]

with httpx.Client(timeout=5) as client:
    for endpoint in common_endpoints:
        try:
            url = f"{host}{endpoint}"
            response = client.get(url)
            if response.status_code != 404:
                print(f"  {endpoint}: {response.status_code}")
        except:
            pass

print("\n" + "=" * 60)
print("Recommendations:")
print("-" * 40)
print("1. Check OpenAlgo server documentation for correct API endpoints")
print("2. Verify the API key format matches what OpenAlgo expects")
print("3. Look at OpenAlgo server logs to see the actual auth error")
print("4. The server is running but may be a different version than expected")