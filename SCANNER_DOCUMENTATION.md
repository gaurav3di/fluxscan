# FluxScan Scanner Documentation

## Table of Contents
1. [Scanner Basics](#scanner-basics)
2. [Scanner Types](#scanner-types)
3. [Writing Scanners](#writing-scanners)
4. [Available Variables](#available-variables)
5. [Required Output Format](#required-output-format)
6. [Examples](#examples)

## Scanner Basics

FluxScan scanners are Python code snippets that analyze market data and generate signals or exploration results. Each scanner must follow specific conventions to ensure proper execution and display of results.

## Scanner Types

FluxScan supports three main scanner types:

### 1. **Trading Signals** (`signal_type = 'BUY'` or `'SELL'`)
Generate trading signals with entry, target, and stop loss levels.

### 2. **Data Exploration** (`signal_type = 'DATA'` or `'EXPLORE'`)
Display data without generating trading signals (like Amibroker's Filter = 1).

### 3. **Custom Analysis** (`signal_type = 'CUSTOM'`)
For specialized analysis with custom metrics.

## Writing Scanners

### Basic Structure

Every scanner must follow this structure:

```python
# 1. Calculate indicators using TA-Lib
indicator = talib.FUNCTION(data_series, parameters)

# 2. Extract values
current_value = float(indicator.iloc[-1])

# 3. Define signal logic
signal = True/False  # Must be set
signal_type = 'BUY'/'SELL'/'DATA'/'EXPLORE'  # Must be set

# 4. Build metrics dictionary
metrics = {
    'key': value,
    # ... more metrics
}
```

## Available Variables

### Input Data (Automatically Available)
- `close` - Pandas Series of closing prices
- `open` - Pandas Series of opening prices
- `high` - Pandas Series of high prices
- `low` - Pandas Series of low prices
- `volume` - Pandas Series of volume data
- `data` - Complete DataFrame with OHLCV data
- `symbol` - Current stock symbol being scanned

### Libraries Available
- `talib` - Technical Analysis Library
- `pd` (pandas) - Data manipulation
- `np` (numpy) - Numerical computations
- `datetime` - Date/time operations

### TA-Lib Functions Available
All TA-Lib functions are available, including:
- `EMA`, `SMA`, `WMA` - Moving averages
- `RSI`, `MACD`, `STOCH` - Oscillators
- `BBANDS` - Bollinger Bands
- `ATR` - Average True Range
- And many more...

## Required Output Format

### Mandatory Variables

Every scanner MUST set these variables:

```python
signal = True/False  # Whether to include this stock in results
signal_type = 'TYPE'  # Signal type (BUY/SELL/DATA/EXPLORE/etc.)
metrics = {}  # Dictionary of metrics to display
```

### Signal Types and Their Required Metrics

#### For Trading Signals (BUY/SELL)
```python
signal = True
signal_type = 'BUY'  # or 'SELL'
metrics = {
    'price': current_price,      # Required
    'entry': entry_price,        # Required
    'target': target_price,      # Required
    'stop_loss': stop_loss,      # Required
    'risk_reward': rr_ratio,     # Optional but recommended
    # Additional metrics as needed
}
```

#### For Data Exploration (DATA/EXPLORE)
```python
signal = True  # Always True for exploration (Filter = 1)
signal_type = 'DATA'  # or 'EXPLORE'
metrics = {
    'ltp': latest_price,    # Latest Traded Price
    'ema10': ema10_value,   # Example metric
    'ema20': ema20_value,   # Example metric
    # Any additional metrics
}
```

## Examples

### Example 1: Simple Exploration (Amibroker Filter = 1)
```python
# Simple LTP, EMA10, EMA20 display
# Equivalent to Amibroker: Filter = 1; AddColumn(Close,"LTP",1.2);

# Calculate EMAs
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Get latest values
ltp = float(close.iloc[-1])
ema10_value = float(ema10.iloc[-1])
ema20_value = float(ema20.iloc[-1])

# Always show all stocks (Filter = 1)
signal = True
signal_type = 'DATA'

# Simple metrics
metrics = {
    'ltp': round(ltp, 2),
    'ema10': round(ema10_value, 2),
    'ema20': round(ema20_value, 2)
}
```

### Example 2: EMA Crossover Trading Signal
```python
# EMA Crossover with Risk Management

# Calculate EMAs
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Calculate ATR for stop loss
atr = talib.ATR(high, low, close, timeperiod=14)

# Get current and previous values
current_ema10 = float(ema10.iloc[-1])
current_ema20 = float(ema20.iloc[-1])
prev_ema10 = float(ema10.iloc[-2])
prev_ema20 = float(ema20.iloc[-2])
current_price = float(close.iloc[-1])
current_atr = float(atr.iloc[-1])

# Detect crossover
bullish_crossover = prev_ema10 <= prev_ema20 and current_ema10 > current_ema20
bearish_crossover = prev_ema10 >= prev_ema20 and current_ema10 < current_ema20

# Generate signal
if bullish_crossover:
    signal = True
    signal_type = 'BUY'

    entry_price = current_price
    stop_loss = current_price - (2 * current_atr)
    target = current_price + (3 * current_atr)

    metrics = {
        'price': round(current_price, 2),
        'entry': round(entry_price, 2),
        'target': round(target, 2),
        'stop_loss': round(stop_loss, 2),
        'risk_reward': 1.5
    }
elif bearish_crossover:
    signal = True
    signal_type = 'SELL'

    entry_price = current_price
    stop_loss = current_price + (2 * current_atr)
    target = current_price - (3 * current_atr)

    metrics = {
        'price': round(current_price, 2),
        'entry': round(entry_price, 2),
        'target': round(target, 2),
        'stop_loss': round(stop_loss, 2),
        'risk_reward': 1.5
    }
else:
    signal = False
    signal_type = None
    metrics = {}
```

### Example 3: RSI Oversold Scanner
```python
# RSI Oversold Scanner

# Calculate RSI
rsi = talib.RSI(close, timeperiod=14)
current_rsi = float(rsi.iloc[-1])
current_price = float(close.iloc[-1])

# Check for oversold condition
if current_rsi < 30:
    signal = True
    signal_type = 'BUY'

    # Simple risk management
    entry_price = current_price
    stop_loss = current_price * 0.95  # 5% stop loss
    target = current_price * 1.10     # 10% target

    metrics = {
        'price': round(current_price, 2),
        'rsi': round(current_rsi, 2),
        'entry': round(entry_price, 2),
        'target': round(target, 2),
        'stop_loss': round(stop_loss, 2),
        'risk_reward': 2.0
    }
else:
    signal = False
    signal_type = None
    metrics = {}
```

### Example 4: Volume Breakout Scanner
```python
# Volume Breakout Scanner

# Calculate average volume
avg_volume = volume.rolling(window=20).mean()
current_volume = float(volume.iloc[-1])
avg_volume_value = float(avg_volume.iloc[-1])
current_price = float(close.iloc[-1])

# Calculate price change
price_change = ((current_price - float(close.iloc[-2])) / float(close.iloc[-2])) * 100

# Check for volume breakout with price increase
if current_volume > (avg_volume_value * 2) and price_change > 2:
    signal = True
    signal_type = 'BUY'

    entry_price = current_price
    stop_loss = current_price * 0.97
    target = current_price * 1.05

    metrics = {
        'price': round(current_price, 2),
        'volume': int(current_volume),
        'avg_volume': int(avg_volume_value),
        'volume_ratio': round(current_volume / avg_volume_value, 2),
        'price_change': round(price_change, 2),
        'entry': round(entry_price, 2),
        'target': round(target, 2),
        'stop_loss': round(stop_loss, 2)
    }
else:
    signal = False
    signal_type = None
    metrics = {}
```

### Example 5: Multi-Timeframe Analysis
```python
# Multiple Indicators Exploration

# Calculate various indicators
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)
rsi = talib.RSI(close, timeperiod=14)
macd, macd_signal, macd_hist = talib.MACD(close)
upper, middle, lower = talib.BBANDS(close)

# Get latest values
current_price = float(close.iloc[-1])
current_ema10 = float(ema10.iloc[-1])
current_ema20 = float(ema20.iloc[-1])
current_rsi = float(rsi.iloc[-1])
current_macd = float(macd.iloc[-1])
bb_upper = float(upper.iloc[-1])
bb_lower = float(lower.iloc[-1])

# Always show data (exploration mode)
signal = True
signal_type = 'DATA'

# Comprehensive metrics
metrics = {
    'ltp': round(current_price, 2),
    'ema10': round(current_ema10, 2),
    'ema20': round(current_ema20, 2),
    'rsi': round(current_rsi, 2),
    'macd': round(current_macd, 2),
    'bb_upper': round(bb_upper, 2),
    'bb_lower': round(bb_lower, 2),
    'bb_position': 'Above' if current_price > bb_upper else 'Below' if current_price < bb_lower else 'Inside'
}
```

## Best Practices

1. **Always handle NaN values**: Use `pd.isna()` or provide defaults
2. **Round numeric values**: Use `round(value, 2)` for prices
3. **Type conversion**: Always convert to `float()` or `int()` as needed
4. **Error handling**: Check data availability before accessing
5. **Clear signal logic**: Make conditions explicit and readable

## Testing Your Scanner

1. Start with a small watchlist (2-3 stocks)
2. Print intermediate values for debugging
3. Verify calculations match expected results
4. Test edge cases (missing data, extreme values)

## Common Pitfalls

1. **Not setting signal variable**: Every scanner must set `signal = True/False`
2. **Missing signal_type**: Always set `signal_type` when signal is True
3. **Empty metrics**: Metrics dictionary should contain relevant data
4. **Index errors**: Check data length before accessing `.iloc[-1]`
5. **Type errors**: Convert numpy/pandas types to Python native types

## Scanner Validation

FluxScan validates scanners for:
- No use of dangerous functions (`eval`, `exec`, `import`)
- Proper variable declaration (`signal`, `signal_type`, `metrics`)
- Safe data access patterns

## Support

For scanner examples and help:
- Check existing scanners in the system
- Review this documentation
- Test with simple scanners first
- Build complexity gradually

Remember: Start simple, test often, and incrementally add complexity!