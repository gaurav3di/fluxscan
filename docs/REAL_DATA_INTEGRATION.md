# FluxScan - Real Data Integration with OpenAlgo SDK

## Overview

FluxScan is fully integrated with the OpenAlgo SDK to provide real-time and historical market data for scanning. This document explains how the integration works and how to use real data in your scanners.

## Supported Exchanges

OpenAlgo supports the following exchanges:
- **NSE** - National Stock Exchange
- **BSE** - Bombay Stock Exchange
- **NFO** - NSE Futures & Options
- **BFO** - BSE Futures & Options
- **CDS** - Currency Derivatives
- **BCD** - BSE Currency Derivatives
- **MCX** - Multi Commodity Exchange

## Supported Timeframes

Based on OpenAlgo SDK intervals, FluxScan supports:
- **Minutes**: 1m, 3m, 5m, 10m, 15m, 30m
- **Hours**: 1h
- **Days**: D (Daily)

## Data Service Integration

### Configuration

The DataService class (`services/data_service.py`) uses the OpenAlgo Python SDK to fetch real market data:

```python
from openalgo import api as openalgo_api

class DataService:
    def __init__(self, api_key: str, host: str):
        self.client = openalgo_api(api_key=api_key, host=host)
```

### Real-Time Quotes

Fetch real-time quotes for any symbol:

```python
# Get real-time quote
response = data_service.get_quote('RELIANCE', 'NSE')
# Returns: {
#     'symbol': 'RELIANCE',
#     'ltp': 1234.50,
#     'open': 1230.00,
#     'high': 1240.00,
#     'low': 1225.00,
#     'volume': 1234567,
#     'bid': 1234.45,
#     'ask': 1234.55
# }
```

### Historical Data

Fetch historical data for technical analysis:

```python
# Get historical data
df = data_service.get_historical_data(
    symbol='RELIANCE',
    exchange='NSE',
    interval='5m',     # Use OpenAlgo intervals
    lookback_days=30
)
# Returns pandas DataFrame with columns: open, high, low, close, volume
```

### Market Depth

Get order book depth:

```python
# Get market depth
depth = data_service.get_market_depth('RELIANCE', 'NSE')
# Returns: {
#     'bids': [{'price': 1234.45, 'quantity': 100}, ...],
#     'asks': [{'price': 1234.55, 'quantity': 150}, ...],
#     'totalbuyqty': 5000,
#     'totalsellqty': 4500
# }
```

## Scanner Engine with Real Data

The scanner engine (`scanners/scanner_engine.py`) automatically fetches real data for each symbol during scanning:

```python
def execute_scanner(self, scanner_code, symbols, parameters):
    for symbol in symbols:
        # Fetches real data from OpenAlgo
        data = self.data_service.get_historical_data(
            symbol=symbol,
            exchange=parameters.get('exchange', 'NSE'),
            interval=parameters.get('interval', 'D'),
            lookback_days=parameters.get('lookback_days', 100)
        )

        # Execute scanner on real data
        result = self._execute_for_symbol(
            compiled_code,
            namespace,
            data,  # Real market data
            symbol,
            parameters
        )
```

## Writing Scanners with Real Data

### Example 1: RSI Scanner with Real Data

```python
# Scanner code that runs on real market data
rsi_period = params.get('rsi_period', 14)
oversold_level = params.get('oversold_level', 30)

# Calculate RSI on real price data
rsi = talib.RSI(close, timeperiod=rsi_period)

# Generate signal based on real RSI values
if len(rsi) > 0 and rsi[-1] < oversold_level:
    signal = True
    signal_type = 'BUY'
    metrics = {
        'rsi': float(rsi[-1]),
        'price': float(close[-1]),  # Real current price
        'volume': float(volume[-1])  # Real current volume
    }
else:
    signal = False
```

### Example 2: Volume Breakout with Real Data

```python
# Analyze real volume data
avg_volume = talib.SMA(volume, timeperiod=20)
current_volume = volume[-1]
volume_ratio = current_volume / avg_volume[-1]

# Check for real volume surge
if volume_ratio > 2.0 and close[-1] > close[-2]:
    signal = True
    signal_type = 'BUY'
    metrics = {
        'volume': float(current_volume),
        'avg_volume': float(avg_volume[-1]),
        'volume_ratio': float(volume_ratio),
        'price': float(close[-1])
    }
```

## Running Real Scans

### Via API

```python
import httpx
import json

# Run a scan with real data
response = httpx.post('http://localhost:5001/scanners/api/scan',
    json={
        'scanner_id': 1,
        'watchlist_id': 1,
        'parameters': {
            'exchange': 'NSE',
            'interval': '5m',  # Real 5-minute data
            'lookback_days': 5
        }
    }
)

results = response.json()
# Results contain real signals from actual market data
```

### Via Web Interface

1. Create a scanner with your strategy
2. Select a watchlist with real symbols
3. Choose timeframe (1m, 3m, 5m, 10m, 15m, 30m, 1h, D)
4. Click "Run Scan"
5. View real-time results

## Testing with Real Data

Use the test script to verify real data integration:

```bash
# Set your OpenAlgo credentials
export OPENALGO_API_KEY='your_api_key'
export OPENALGO_HOST='http://127.0.0.1:5000'

# Run the test
python test_real_scan.py
```

This will:
1. Connect to OpenAlgo
2. Fetch real market data
3. Run sample scanners
4. Display actual results

## Performance Considerations

### Caching

FluxScan caches market data to reduce API calls:
- Quote data: 10 seconds
- Historical data: 5 minutes
- Market depth: Not cached (always real-time)

### Parallel Processing

The scanner engine supports parallel scanning:
```python
# Scans multiple symbols in parallel using real data
results = scanner_engine.execute_parallel(
    scanner_code,
    symbols=['RELIANCE', 'TCS', 'INFY', ...],
    parameters={'interval': '5m'},
    max_workers=5
)
```

## Troubleshooting

### No Data Received

If you're not getting data:
1. Verify OpenAlgo is running
2. Check API key is correct
3. Ensure market is open (for live data)
4. Verify symbol exists on exchange

### Fallback Mode

When OpenAlgo is unavailable, DataService provides fallback data for development:
- Fallback data is clearly marked
- Uses realistic price movements
- Allows testing without live connection

### Debug Mode

Enable debug logging to see actual API calls:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Rate Limits

Be aware of OpenAlgo API limits:
- Respect rate limiting
- Use caching effectively
- Batch requests when possible

## Best Practices

1. **Always specify exchange**: Different exchanges may have different data
2. **Use appropriate timeframes**: Higher timeframes for long-term analysis
3. **Cache strategically**: Balance freshness vs API calls
4. **Handle errors gracefully**: Market data may be unavailable
5. **Test during market hours**: For most accurate real-time data

## Example Output

When running with real data, you'll see actual market information:

```
📊 RSI Scanner Result:
   Symbol: RELIANCE
   RSI: 42.35 (Real RSI value)
   Price: ₹2,456.75 (Actual market price)
   Signal: HOLD

📈 Volume Analysis:
   Current Volume: 5,234,567 (Real volume)
   Avg Volume: 3,456,789
   Volume Ratio: 1.51x
   Signal: Potential breakout
```

## Support

For issues with OpenAlgo integration:
1. Check OpenAlgo documentation
2. Verify API endpoints
3. Review FluxScan logs
4. Test with provided test script