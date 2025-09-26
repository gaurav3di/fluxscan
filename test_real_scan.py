#!/usr/bin/env python3
"""
Test script to demonstrate real scanning with OpenAlgo SDK
This script shows how FluxScan uses real market data from OpenAlgo
"""

import os
import sys
from datetime import datetime, timedelta
from openalgo import api as openalgo_api
import pandas as pd
import numpy as np
import talib

# Configuration
OPENALGO_API_KEY = os.getenv('OPENALGO_API_KEY', 'your_api_key_here')
OPENALGO_HOST = os.getenv('OPENALGO_HOST', 'http://127.0.0.1:5000')

def initialize_client():
    """Initialize OpenAlgo client"""
    try:
        client = openalgo_api(api_key=OPENALGO_API_KEY, host=OPENALGO_HOST)
        print(f"✓ Connected to OpenAlgo at {OPENALGO_HOST}")
        return client
    except Exception as e:
        print(f"✗ Failed to connect to OpenAlgo: {e}")
        print("  Make sure OpenAlgo is running and API key is correct")
        return None

def get_available_intervals(client):
    """Get supported timeframes from OpenAlgo"""
    try:
        response = client.intervals()
        if response.get('status') == 'success':
            data = response.get('data', {})
            print("\n📊 Available Timeframes from OpenAlgo:")
            print(f"  Minutes: {data.get('minutes', [])}")
            print(f"  Hours: {data.get('hours', [])}")
            print(f"  Days: {data.get('days', [])}")
            return data
        return None
    except Exception as e:
        print(f"✗ Error fetching intervals: {e}")
        return None

def fetch_historical_data(client, symbol='RELIANCE', exchange='NSE', interval='D', days=30):
    """Fetch real historical data from OpenAlgo"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        print(f"\n📈 Fetching {symbol} data...")
        print(f"   Exchange: {exchange}")
        print(f"   Interval: {interval}")
        print(f"   Period: {start_date} to {end_date}")

        response = client.history(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )

        if isinstance(response, pd.DataFrame) and not response.empty:
            print(f"✓ Received {len(response)} data points")
            return response
        else:
            print("✗ No data received")
            return None

    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return None

def run_rsi_scanner(data, oversold=30, overbought=70):
    """Example RSI scanner using real data"""
    try:
        # Ensure columns are lowercase
        if 'Close' in data.columns:
            data.columns = [col.lower() for col in data.columns]

        # Calculate RSI
        rsi = talib.RSI(data['close'].values, timeperiod=14)

        current_rsi = rsi[-1]
        prev_rsi = rsi[-2]

        # Generate signal
        signal = None
        if current_rsi < oversold and prev_rsi >= oversold:
            signal = 'BUY'
        elif current_rsi > overbought and prev_rsi <= overbought:
            signal = 'SELL'

        return {
            'rsi': float(current_rsi),
            'price': float(data['close'].iloc[-1]),
            'signal': signal
        }

    except Exception as e:
        print(f"✗ Scanner error: {e}")
        return None

def run_macd_scanner(data):
    """Example MACD scanner using real data"""
    try:
        # Ensure columns are lowercase
        if 'Close' in data.columns:
            data.columns = [col.lower() for col in data.columns]

        # Calculate MACD
        macd, macd_signal, macd_hist = talib.MACD(
            data['close'].values,
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )

        # Check for crossover
        signal = None
        if len(macd_hist) >= 2:
            if macd_hist[-2] < 0 and macd_hist[-1] > 0:
                signal = 'BUY'
            elif macd_hist[-2] > 0 and macd_hist[-1] < 0:
                signal = 'SELL'

        return {
            'macd': float(macd[-1]) if not np.isnan(macd[-1]) else 0,
            'signal_line': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else 0,
            'histogram': float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else 0,
            'price': float(data['close'].iloc[-1]),
            'signal': signal
        }

    except Exception as e:
        print(f"✗ Scanner error: {e}")
        return None

def scan_multiple_symbols(client, symbols, scanner_func):
    """Scan multiple symbols with given scanner"""
    results = []

    for symbol in symbols:
        data = fetch_historical_data(client, symbol=symbol)
        if data is not None:
            result = scanner_func(data)
            if result:
                result['symbol'] = symbol
                results.append(result)

    return results

def main():
    """Main test function"""
    print("=" * 60)
    print("FluxScan - Real Market Data Scanner Test")
    print("Using OpenAlgo SDK for Live Data")
    print("=" * 60)

    # Initialize client
    client = initialize_client()
    if not client:
        return

    # Get available intervals
    intervals = get_available_intervals(client)

    # Test symbols
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']

    # Test 1: Single symbol with RSI scanner
    print("\n" + "=" * 60)
    print("TEST 1: RSI Scanner on RELIANCE")
    print("=" * 60)

    data = fetch_historical_data(client, 'RELIANCE', 'NSE', '5m', days=1)
    if data is not None:
        result = run_rsi_scanner(data)
        if result:
            print("\n📊 RSI Scanner Result:")
            print(f"   RSI: {result['rsi']:.2f}")
            print(f"   Price: ₹{result['price']:.2f}")
            print(f"   Signal: {result['signal'] or 'HOLD'}")

    # Test 2: Multiple symbols with MACD scanner
    print("\n" + "=" * 60)
    print("TEST 2: MACD Scanner on Multiple Symbols")
    print("=" * 60)

    results = []
    for symbol in test_symbols[:3]:  # Test first 3 symbols
        data = fetch_historical_data(client, symbol, 'NSE', 'D', days=100)
        if data is not None:
            result = run_macd_scanner(data)
            if result:
                result['symbol'] = symbol
                results.append(result)

    if results:
        print("\n📊 MACD Scanner Results:")
        for r in results:
            print(f"\n   {r['symbol']}:")
            print(f"     MACD: {r['macd']:.4f}")
            print(f"     Signal Line: {r['signal_line']:.4f}")
            print(f"     Histogram: {r['histogram']:.4f}")
            print(f"     Price: ₹{r['price']:.2f}")
            print(f"     Signal: {r['signal'] or 'HOLD'}")

    # Test 3: Real-time quote
    print("\n" + "=" * 60)
    print("TEST 3: Real-time Quotes")
    print("=" * 60)

    for symbol in test_symbols[:3]:
        try:
            quote = client.quotes(symbol=symbol, exchange='NSE')
            if quote.get('status') == 'success':
                data = quote.get('data', {})
                print(f"\n   {symbol}:")
                print(f"     LTP: ₹{data.get('ltp', 0):.2f}")
                print(f"     Open: ₹{data.get('open', 0):.2f}")
                print(f"     High: ₹{data.get('high', 0):.2f}")
                print(f"     Low: ₹{data.get('low', 0):.2f}")
                print(f"     Volume: {data.get('volume', 0):,}")
        except Exception as e:
            print(f"✗ Error fetching quote for {symbol}: {e}")

    print("\n" + "=" * 60)
    print("✓ Real data scanning test completed!")
    print("=" * 60)

if __name__ == '__main__':
    main()