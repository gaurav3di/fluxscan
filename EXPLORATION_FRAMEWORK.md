# FluxScan Exploration Framework (Amibroker Style)

## Simple Concept

Just like Amibroker, you only need to specify:
1. **Filter** - Which rows to include (True/False)
2. **Columns** - What data to display

## Scanner Format

```python
# Your calculations here
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# FILTER - Which rows to show (just like Amibroker's Filter)
Filter = True  # True means show this row, False means skip

# COLUMNS - What to display (just like Amibroker's AddColumn)
AddColumn('LTP', float(close.iloc[-1]), '1.2')
AddColumn('EMA10', float(ema10.iloc[-1]), '1.2')
AddColumn('EMA20', float(ema20.iloc[-1]), '1.2')
```

That's it! The framework handles everything else.

## Examples

### Example 1: Show All Stocks (Filter = 1)
```python
# Calculate
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Filter
Filter = 1  # Show all

# Columns
AddColumn('LTP', float(close.iloc[-1]), '1.2')
AddColumn('EMA10', float(ema10.iloc[-1]), '1.2')
AddColumn('EMA20', float(ema20.iloc[-1]), '1.2')
```

### Example 2: Show Only Bullish Stocks
```python
# Calculate
ema10 = talib.EMA(close, timeperiod=10)
ema20 = talib.EMA(close, timeperiod=20)

# Filter
Filter = float(ema10.iloc[-1]) > float(ema20.iloc[-1])

# Columns
AddColumn('LTP', float(close.iloc[-1]), '1.2')
AddColumn('EMA10', float(ema10.iloc[-1]), '1.2')
AddColumn('EMA20', float(ema20.iloc[-1]), '1.2')
AddColumn('Trend', 'BULLISH' if Filter else 'BEARISH', 'text')
```

### Example 3: RSI Oversold
```python
# Calculate
rsi = talib.RSI(close, timeperiod=14)

# Filter
Filter = float(rsi.iloc[-1]) < 30

# Columns
AddColumn('LTP', float(close.iloc[-1]), '1.2')
AddColumn('RSI', float(rsi.iloc[-1]), '1.2')
AddColumn('Status', 'OVERSOLD', 'text')
```

## Output
The results page will automatically display:
- Symbol (always)
- Date/Time (always)
- Your specified columns