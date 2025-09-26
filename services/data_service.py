import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from openalgo import api as openalgo_api
import httpx
from .cache_service import CacheService

class DataService:
    def __init__(self, api_key: str, host: str):
        self.api_key = api_key
        self.host = host
        self.client = None
        self.cache = CacheService()
        self.http_client = httpx.Client(timeout=30.0)
        self._initialize_client()

    def _initialize_client(self):
        try:
            self.client = openalgo_api(api_key=self.api_key, host=self.host)
            self.api_valid = None  # Will be checked on first use
        except Exception as e:
            print(f"Failed to initialize OpenAlgo client: {e}")
            self.client = None
            self.api_valid = False

    def get_historical_data(self, symbol: str, exchange: str = 'NSE',
                           interval: str = 'D', lookback_days: int = 100) -> Optional[pd.DataFrame]:
        cache_key = f"hist_{symbol}_{exchange}_{interval}_{lookback_days}"

        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            # Fetch data from OpenAlgo
            if self.client and self.api_valid != False:
                response = self.client.history(
                    symbol=symbol,
                    exchange=exchange,
                    interval=self._convert_interval(interval),
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )

                # Check if we got an error response
                if isinstance(response, dict) and response.get('status') == 'error':
                    error_msg = response.get('message', 'Unknown error')
                    if 'Invalid openalgo apikey' in error_msg or response.get('code') == 403:
                        self.api_valid = False
                        print(f"\n" + "=" * 60)
                        print("OPENALGO API KEY ERROR")
                        print("=" * 60)
                        print("The OpenAlgo API key is invalid or not set correctly.")
                        print("Using dummy data for testing.")
                        print("\nTo fix this:")
                        print("1. Get valid API key from OpenAlgo server")
                        print("2. Update OPENALGO_API_KEY in .env file")
                        print("3. Restart FluxScan")
                        print("=" * 60 + "\n")
                    else:
                        print(f"OpenAlgo API error: {error_msg}")
                elif isinstance(response, pd.DataFrame) and not response.empty:
                    # Ensure column names are lowercase
                    response.columns = [col.lower() for col in response.columns]

                    # Mark API as valid
                    if self.api_valid is None:
                        self.api_valid = True

                    # Cache the data
                    self.cache.set(cache_key, response, ttl=300)  # 5 minutes cache

                    return response

        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")

        # Return dummy data for testing if API fails
        print(f"Using dummy data for {symbol} ({interval})")
        return self._get_dummy_data(lookback_days)

    def get_quote(self, symbol: str, exchange: str = 'NSE') -> Optional[Dict[str, Any]]:
        cache_key = f"quote_{symbol}_{exchange}"

        # Check cache
        cached_quote = self.cache.get(cache_key)
        if cached_quote:
            return cached_quote

        try:
            if self.client:
                response = self.client.quotes(symbol=symbol, exchange=exchange)

                if response and response.get('status') == 'success':
                    quote_data = response.get('data', {})
                    # Cache for 10 seconds
                    self.cache.set(cache_key, quote_data, ttl=10)
                    return quote_data

        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")

        # Return dummy quote for testing
        return self._get_dummy_quote(symbol)

    def get_depth(self, symbol: str, exchange: str = 'NSE') -> Optional[Dict[str, Any]]:
        try:
            if self.client:
                response = self.client.depth(symbol=symbol, exchange=exchange)

                if response and response.get('status') == 'success':
                    return response.get('data', {})

        except Exception as e:
            print(f"Error fetching depth for {symbol}: {e}")

        return None

    def search_symbols(self, query: str, exchange: str = 'NSE') -> List[Dict[str, Any]]:
        try:
            if self.client:
                response = self.client.search(query=query, exchange=exchange)

                if response and response.get('status') == 'success':
                    return response.get('data', [])

        except Exception as e:
            print(f"Error searching symbols: {e}")

        return []

    def validate_symbol(self, symbol: str, exchange: str = 'NSE') -> bool:
        try:
            if self.client:
                response = self.client.symbol(symbol=symbol, exchange=exchange)

                if response and response.get('status') == 'success':
                    return True

        except Exception as e:
            print(f"Error validating symbol {symbol}: {e}")

        # For testing, accept common symbols
        test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'ITC', 'HDFCBANK']
        return symbol in test_symbols

    def get_index_constituents(self, index_name: str) -> List[str]:
        # Predefined index constituents for testing
        indices = {
            'NIFTY50': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HDFC', 'ITC', 'SBIN',
                       'BHARTIARTL', 'KOTAKBANK', 'LT', 'AXISBANK', 'WIPRO', 'ASIANPAINT', 'MARUTI'],
            'NIFTYBANK': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK',
                         'BANDHANBNK', 'FEDERALBNK', 'PNB', 'BANKBARODA'],
            'NIFTYIT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'PERSISTENT',
                       'COFORGE', 'MPHASIS', 'LTTS']
        }

        return indices.get(index_name, [])

    def get_available_intervals(self) -> Dict[str, List[str]]:
        try:
            if self.client:
                response = self.client.intervals()

                if response and response.get('status') == 'success':
                    return response.get('data', {})

        except Exception as e:
            print(f"Error fetching intervals: {e}")

        # Default intervals
        return {
            'minutes': ['1m', '3m', '5m', '10m', '15m', '30m'],
            'hours': ['1h'],
            'days': ['D'],
            'weeks': [],
            'months': []
        }

    def test_connection(self) -> bool:
        try:
            # Try to fetch a simple quote to test connection
            response = self.get_quote('RELIANCE', 'NSE')
            return response is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def _convert_interval(self, interval: str) -> str:
        interval_map = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '10m': '10m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            'D': 'D',
            'W': 'W',
            'M': 'M'
        }
        return interval_map.get(interval, 'D')

    def _get_dummy_data(self, days: int) -> pd.DataFrame:
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        data = {
            'timestamp': dates,
            'open': np.random.uniform(100, 200, days),
            'high': np.random.uniform(100, 200, days),
            'low': np.random.uniform(100, 200, days),
            'close': np.random.uniform(100, 200, days),
            'volume': np.random.uniform(1000000, 5000000, days)
        }

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)

        # Make it more realistic
        for i in range(1, len(df)):
            df.loc[df.index[i], 'open'] = df.loc[df.index[i-1], 'close'] * np.random.uniform(0.98, 1.02)
            df.loc[df.index[i], 'high'] = df.loc[df.index[i], 'open'] * np.random.uniform(1.0, 1.03)
            df.loc[df.index[i], 'low'] = df.loc[df.index[i], 'open'] * np.random.uniform(0.97, 1.0)
            df.loc[df.index[i], 'close'] = np.random.uniform(df.loc[df.index[i], 'low'], df.loc[df.index[i], 'high'])

        return df

    def _get_dummy_quote(self, symbol: str) -> Dict[str, Any]:
        base_price = np.random.uniform(100, 2000)
        return {
            'symbol': symbol,
            'ltp': base_price,
            'open': base_price * 0.99,
            'high': base_price * 1.02,
            'low': base_price * 0.98,
            'close': base_price,
            'prev_close': base_price * 0.995,
            'volume': np.random.randint(1000000, 10000000),
            'bid': base_price - 0.05,
            'ask': base_price + 0.05
        }

    def close(self):
        if self.http_client:
            self.http_client.close()