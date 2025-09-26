# FluxScan Scanner Writing Guide

## Table of Contents
- [Introduction](#introduction)
- [Scanner Basics](#scanner-basics)
- [Available Variables](#available-variables)
- [Available Libraries](#available-libraries)
- [Writing Your First Scanner](#writing-your-first-scanner)
- [Advanced Scanner Techniques](#advanced-scanner-techniques)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Introduction

FluxScan scanners are Python scripts that analyze stock market data to identify trading opportunities. Each scanner runs on individual stocks in your watchlist and generates signals based on your defined criteria.

## Scanner Basics

### Scanner Structure

Every scanner must follow this basic structure:

```python
# 1. Extract parameters (optional)
parameter_value = params.get('parameter_name', default_value)

# 2. Perform analysis
# Your analysis code here

# 3. Set output variables
signal = True/False  # Required: Boolean indicating if signal found
signal_type = 'BUY'/'SELL'/'WATCH'  # Required if signal=True
metrics = {'key': value}  # Optional: Additional data to store
```

### Required Output Variables

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `signal` | Boolean | Whether a signal was found | Yes |
| `signal_type` | String | Type of signal: 'BUY', 'SELL', or 'WATCH' | Yes (if signal=True) |
| `metrics` | Dictionary | Additional data about the signal | No |

## Available Variables

### Data Variables

| Variable | Type | Description |
|----------|------|-------------|
| `data` | DataFrame | Complete OHLCV DataFrame with all columns |
| `df` | DataFrame | Alias for `data` |
| `open` | numpy.array | Opening prices |
| `high` | numpy.array | High prices |
| `low` | numpy.array | Low prices |
| `close` | numpy.array | Closing prices |
| `volume` | numpy.array | Trading volume |
| `symbol` | String | Current symbol being scanned |
| `params` | Dictionary | Scanner parameters |

### Example: Accessing Data

```python
# Get the latest close price
latest_close = close[-1]

# Get the previous close price
previous_close = close[-2]

# Get the last 10 close prices
last_10_closes = close[-10:]

# Access DataFrame columns
data['close']  # Same as close variable
data['volume']  # Same as volume variable
```

## Available Libraries

### Core Libraries

```python
# Pandas - Data manipulation
pd.DataFrame, pd.Series

# NumPy - Numerical operations
np.array, np.mean, np.std

# TA-Lib - Technical indicators (Full list below)
talib.SMA, talib.EMA, talib.RSI, talib.MACD

# Python built-ins
datetime, math, statistics
```

### TA-Lib Indicators

#### Overlap Studies
- `SMA(close, timeperiod)` - Simple Moving Average
- `EMA(close, timeperiod)` - Exponential Moving Average
- `WMA(close, timeperiod)` - Weighted Moving Average
- `BBANDS(close, timeperiod, nbdevup, nbdevdn)` - Bollinger Bands
- `SAR(high, low, acceleration, maximum)` - Parabolic SAR
- `TEMA(close, timeperiod)` - Triple Exponential Moving Average

#### Momentum Indicators
- `RSI(close, timeperiod)` - Relative Strength Index
- `MACD(close, fastperiod, slowperiod, signalperiod)` - MACD
- `STOCH(high, low, close, fastk_period, slowk_period, slowd_period)` - Stochastic
- `CCI(high, low, close, timeperiod)` - Commodity Channel Index
- `MFI(high, low, close, volume, timeperiod)` - Money Flow Index
- `WILLR(high, low, close, timeperiod)` - Williams %R
- `ROC(close, timeperiod)` - Rate of Change
- `MOM(close, timeperiod)` - Momentum

#### Volatility Indicators
- `ATR(high, low, close, timeperiod)` - Average True Range
- `NATR(high, low, close, timeperiod)` - Normalized ATR
- `TRANGE(high, low, close)` - True Range

#### Volume Indicators
- `OBV(close, volume)` - On Balance Volume
- `AD(high, low, close, volume)` - Chaikin A/D Line
- `ADOSC(high, low, close, volume, fastperiod, slowperiod)` - Chaikin A/D Oscillator

#### Trend Indicators
- `ADX(high, low, close, timeperiod)` - Average Directional Index
- `AROON(high, low, timeperiod)` - Aroon
- `AROONOSC(high, low, timeperiod)` - Aroon Oscillator

## Writing Your First Scanner

### Example 1: Simple Moving Average Crossover

```python
# Simple Moving Average Crossover Scanner
# Detects when fast MA crosses above slow MA (Golden Cross)

# Parameters
fast_period = params.get('fast_period', 50)
slow_period = params.get('slow_period', 200)

# Check if we have enough data
if len(close) < slow_period:
    signal = False
else:
    # Calculate moving averages
    fast_ma = talib.SMA(close, timeperiod=fast_period)
    slow_ma = talib.SMA(close, timeperiod=slow_period)

    # Check for crossover
    if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
        signal = True
        signal_type = 'BUY'
        metrics = {
            'fast_ma': float(fast_ma[-1]),
            'slow_ma': float(slow_ma[-1]),
            'price': float(close[-1])
        }
    else:
        signal = False
```

### Example 2: RSI Oversold with Volume Confirmation

```python
# RSI Oversold Scanner with Volume Confirmation
# Finds oversold stocks with increasing volume

# Parameters
rsi_period = params.get('rsi_period', 14)
oversold_level = params.get('oversold_level', 30)
volume_increase = params.get('volume_increase', 1.5)

if len(close) < rsi_period + 1:
    signal = False
else:
    # Calculate RSI
    rsi = talib.RSI(close, timeperiod=rsi_period)

    # Calculate average volume
    avg_volume = talib.SMA(volume, timeperiod=20)

    # Check conditions
    if (rsi[-1] < oversold_level and
        volume[-1] > avg_volume[-1] * volume_increase):

        signal = True
        signal_type = 'BUY'
        metrics = {
            'rsi': float(rsi[-1]),
            'volume_ratio': float(volume[-1] / avg_volume[-1]),
            'price': float(close[-1])
        }
    else:
        signal = False
```

## Advanced Scanner Techniques

### Multi-Condition Scanners

```python
# Multiple Condition Scanner
# Combines RSI, MACD, and Volume

# Calculate indicators
rsi = talib.RSI(close, timeperiod=14)
macd, signal_line, histogram = talib.MACD(close)
avg_volume = talib.SMA(volume, timeperiod=20)

# Define conditions
rsi_oversold = rsi[-1] < 35
macd_bullish = histogram[-1] > histogram[-2]
volume_surge = volume[-1] > avg_volume[-1] * 1.5

# Combine conditions
if rsi_oversold and macd_bullish and volume_surge:
    signal = True
    signal_type = 'BUY'

    # Calculate signal strength (0-100)
    strength = 0
    strength += 33 if rsi_oversold else 0
    strength += 33 if macd_bullish else 0
    strength += 34 if volume_surge else 0

    metrics = {
        'rsi': float(rsi[-1]),
        'macd_hist': float(histogram[-1]),
        'volume_ratio': float(volume[-1] / avg_volume[-1]),
        'signal_strength': strength
    }
else:
    signal = False
```

### Pattern Recognition

```python
# Bullish Engulfing Pattern Scanner

if len(close) < 2:
    signal = False
else:
    # Previous candle was bearish
    prev_bearish = close[-2] < open[-2]

    # Current candle is bullish
    curr_bullish = close[-1] > open[-1]

    # Current candle engulfs previous
    engulfing = (open[-1] < close[-2] and
                 close[-1] > open[-2])

    if prev_bearish and curr_bullish and engulfing:
        signal = True
        signal_type = 'BUY'
        metrics = {
            'pattern': 'Bullish Engulfing',
            'strength': float((close[-1] - open[-1]) / open[-1] * 100),
            'price': float(close[-1])
        }
    else:
        signal = False
```

### Support/Resistance Levels

```python
# Support/Resistance Breakout Scanner

# Parameters
lookback = params.get('lookback', 20)
breakout_percent = params.get('breakout_percent', 2)

if len(close) < lookback:
    signal = False
else:
    # Calculate support and resistance
    resistance = max(high[-lookback:])
    support = min(low[-lookback:])

    # Check for breakout
    if close[-1] > resistance * (1 + breakout_percent/100):
        signal = True
        signal_type = 'BUY'
        metrics = {
            'breakout_type': 'Resistance',
            'level': float(resistance),
            'breakout_strength': float((close[-1] - resistance) / resistance * 100),
            'price': float(close[-1])
        }
    elif close[-1] < support * (1 - breakout_percent/100):
        signal = True
        signal_type = 'SELL'
        metrics = {
            'breakout_type': 'Support',
            'level': float(support),
            'breakout_strength': float((support - close[-1]) / support * 100),
            'price': float(close[-1])
        }
    else:
        signal = False
```

### Divergence Detection

```python
# RSI Divergence Scanner
# Detects bullish divergence (price makes lower low, RSI makes higher low)

lookback = params.get('lookback', 14)
rsi_period = params.get('rsi_period', 14)

if len(close) < rsi_period + lookback:
    signal = False
else:
    rsi = talib.RSI(close, timeperiod=rsi_period)

    # Find recent lows
    price_lows = []
    rsi_lows = []

    for i in range(1, lookback-1):
        if low[-i] < low[-i-1] and low[-i] < low[-i+1]:
            price_lows.append((i, low[-i]))
            rsi_lows.append((i, rsi[-i]))

    # Check for divergence
    if len(price_lows) >= 2:
        # Bullish divergence
        if (price_lows[0][1] < price_lows[1][1] and
            rsi_lows[0][1] > rsi_lows[1][1]):

            signal = True
            signal_type = 'BUY'
            metrics = {
                'divergence_type': 'Bullish',
                'price_low1': float(price_lows[0][1]),
                'price_low2': float(price_lows[1][1]),
                'rsi_low1': float(rsi_lows[0][1]),
                'rsi_low2': float(rsi_lows[1][1])
            }
        else:
            signal = False
    else:
        signal = False
```

## Common Patterns

### Trend Following

```python
# ADX Trend Strength Scanner
adx = talib.ADX(high, low, close, timeperiod=14)
plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)
minus_di = talib.MINUS_DI(high, low, close, timeperiod=14)

strong_trend = adx[-1] > 25
bullish = plus_di[-1] > minus_di[-1]

if strong_trend and bullish:
    signal = True
    signal_type = 'BUY'
    metrics = {
        'adx': float(adx[-1]),
        'trend_strength': 'Strong' if adx[-1] > 40 else 'Moderate'
    }
```

### Mean Reversion

```python
# Bollinger Band Mean Reversion
upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)

# Price touches lower band
if close[-1] <= lower[-1]:
    signal = True
    signal_type = 'BUY'
    metrics = {
        'bb_position': 'Lower Band',
        'distance_to_mean': float((middle[-1] - close[-1]) / close[-1] * 100)
    }
```

### Momentum

```python
# Momentum Burst Scanner
momentum = talib.MOM(close, timeperiod=10)
roc = talib.ROC(close, timeperiod=10)

if momentum[-1] > momentum[-2] * 1.5 and roc[-1] > 5:
    signal = True
    signal_type = 'BUY'
    metrics = {
        'momentum': float(momentum[-1]),
        'rate_of_change': float(roc[-1])
    }
```

## Best Practices

### 1. Always Check Data Availability

```python
# Good practice
if len(close) < required_period:
    signal = False
    return  # or continue with next symbol
```

### 2. Handle Edge Cases

```python
# Avoid division by zero
if avg_volume[-1] > 0:
    volume_ratio = volume[-1] / avg_volume[-1]
else:
    volume_ratio = 0
```

### 3. Use Meaningful Metrics

```python
# Provide context in metrics
metrics = {
    'entry_price': float(close[-1]),
    'stop_loss': float(support),
    'target': float(resistance),
    'risk_reward': float((resistance - close[-1]) / (close[-1] - support))
}
```

### 4. Optimize for Performance

```python
# Calculate once, use multiple times
sma_20 = talib.SMA(close, timeperiod=20)
sma_50 = talib.SMA(close, timeperiod=50)

# Use the calculated values
above_sma20 = close[-1] > sma_20[-1]
above_sma50 = close[-1] > sma_50[-1]
```

### 5. Add Signal Strength

```python
# Provide confidence levels
signal_strength = 0

# Add points for each confirmed condition
if rsi_oversold: signal_strength += 30
if macd_bullish: signal_strength += 35
if volume_high: signal_strength += 35

metrics['signal_strength'] = signal_strength
```

## Troubleshooting

### Common Errors and Solutions

#### Error: "IndexError: index -1 is out of bounds"
**Solution**: Check data length before accessing
```python
if len(close) > 0:
    latest_price = close[-1]
```

#### Error: "TypeError: Cannot convert NaN to float"
**Solution**: Check for NaN values
```python
if not pd.isna(rsi[-1]):
    metrics['rsi'] = float(rsi[-1])
```

#### Error: "Signal not defined"
**Solution**: Always initialize signal
```python
signal = False  # Default value
# Your logic here
```

### Debugging Tips

1. **Use print statements** (visible in test mode):
```python
print(f"RSI: {rsi[-1]}, Close: {close[-1]}")
```

2. **Add debug metrics**:
```python
metrics['debug_data_length'] = len(close)
metrics['debug_last_5_closes'] = list(close[-5:])
```

3. **Test with known symbols**:
Start with liquid stocks like RELIANCE, TCS to ensure data availability

4. **Validate parameters**:
```python
fast_period = max(1, params.get('fast_period', 10))
slow_period = max(fast_period + 1, params.get('slow_period', 20))
```

## Scanner Examples Library

### Volume Spike Scanner
```python
# Detect unusual volume activity
avg_vol = talib.SMA(volume, timeperiod=20)
vol_spike = volume[-1] > avg_vol[-1] * 3
price_move = abs((close[-1] - close[-2]) / close[-2] * 100) > 2

if vol_spike and price_move:
    signal = True
    signal_type = 'WATCH'
```

### Gap Scanner
```python
# Detect opening gaps
gap_percent = (open[-1] - close[-2]) / close[-2] * 100

if abs(gap_percent) > 2:
    signal = True
    signal_type = 'BUY' if gap_percent > 0 else 'SELL'
```

### Consolidation Breakout
```python
# Detect breakout from consolidation
atr = talib.ATR(high, low, close, timeperiod=14)
consolidation = max(high[-10:]) - min(low[-10:]) < atr[-1] * 2
breakout = close[-1] > max(high[-10:-1])

if consolidation and breakout:
    signal = True
    signal_type = 'BUY'
```

## Conclusion

Writing effective scanners requires understanding both technical analysis and Python programming. Start with simple scanners and gradually add complexity. Always test your scanners with different market conditions and symbols to ensure reliability.

Remember:
- Keep scanners focused on specific patterns or conditions
- Provide meaningful metrics for analysis
- Handle edge cases and data availability
- Test thoroughly before using in production
- Document your scanner logic for future reference