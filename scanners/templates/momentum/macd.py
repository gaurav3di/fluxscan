# MACD Crossover Scanner Template

template_code = '''
# MACD Crossover Scanner
# This scanner identifies MACD bullish and bearish crossovers

# Get parameters
fast_period = params.get('fast_period', 12)
slow_period = params.get('slow_period', 26)
signal_period = params.get('signal_period', 9)
min_volume = params.get('min_volume', 100000)

# Check if we have enough data
if len(close) < slow_period + signal_period:
    signal = False
else:
    # Calculate MACD
    macd, macdsignal, macdhist = talib.MACD(
        close,
        fastperiod=fast_period,
        slowperiod=slow_period,
        signalperiod=signal_period
    )

    # Calculate average volume
    avg_volume = talib.SMA(volume, timeperiod=20)

    # Check for sufficient volume
    volume_check = volume[-1] > min_volume and volume[-1] > avg_volume[-1] * 0.8 if len(avg_volume) > 0 else True

    # Check for bullish crossover (MACD crosses above signal line)
    if len(macd) >= 2 and len(macdsignal) >= 2 and volume_check:
        if macd[-1] > macdsignal[-1] and macd[-2] <= macdsignal[-2]:
            signal = True
            signal_type = 'BUY'

            # Calculate signal strength (0-100)
            hist_change = abs(macdhist[-1] - macdhist[-2]) if len(macdhist) >= 2 else 0
            signal_strength = min(100, hist_change * 100)

            metrics = {
                'macd': float(macd[-1]),
                'signal_line': float(macdsignal[-1]),
                'histogram': float(macdhist[-1]),
                'price': float(close[-1]),
                'volume': float(volume[-1]),
                'signal_strength': float(signal_strength)
            }

        # Check for bearish crossover (MACD crosses below signal line)
        elif macd[-1] < macdsignal[-1] and macd[-2] >= macdsignal[-2]:
            signal = True
            signal_type = 'SELL'

            # Calculate signal strength
            hist_change = abs(macdhist[-1] - macdhist[-2]) if len(macdhist) >= 2 else 0
            signal_strength = min(100, hist_change * 100)

            metrics = {
                'macd': float(macd[-1]),
                'signal_line': float(macdsignal[-1]),
                'histogram': float(macdhist[-1]),
                'price': float(close[-1]),
                'volume': float(volume[-1]),
                'signal_strength': float(signal_strength)
            }
        else:
            signal = False
    else:
        signal = False
'''

default_parameters = {
    'fast_period': 12,
    'slow_period': 26,
    'signal_period': 9,
    'min_volume': 100000
}

description = "Identifies MACD crossovers with volume confirmation for momentum trading signals"