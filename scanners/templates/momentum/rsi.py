# RSI Overbought/Oversold Scanner Template

template_code = '''
# RSI Overbought/Oversold Scanner
# This scanner identifies stocks in overbought or oversold conditions using RSI

# Get parameters
rsi_period = params.get('rsi_period', 14)
oversold_level = params.get('oversold_level', 30)
overbought_level = params.get('overbought_level', 70)
min_volume = params.get('min_volume', 100000)

# Check if we have enough data
if len(close) < rsi_period + 1:
    signal = False
else:
    # Calculate RSI
    rsi = talib.RSI(close, timeperiod=rsi_period)

    # Calculate price change
    price_change = ((close[-1] - close[-2]) / close[-2] * 100) if len(close) >= 2 else 0

    # Volume check
    volume_check = volume[-1] > min_volume

    if len(rsi) > 0 and volume_check:
        current_rsi = rsi[-1]

        # Check for oversold condition (potential buy signal)
        if current_rsi < oversold_level:
            signal = True
            signal_type = 'BUY'

            # Calculate signal strength based on how oversold
            signal_strength = max(0, (oversold_level - current_rsi) * 3)

            metrics = {
                'rsi': float(current_rsi),
                'price': float(close[-1]),
                'volume': float(volume[-1]),
                'price_change': float(price_change),
                'signal_strength': float(signal_strength),
                'condition': 'oversold'
            }

        # Check for overbought condition (potential sell signal)
        elif current_rsi > overbought_level:
            signal = True
            signal_type = 'SELL'

            # Calculate signal strength based on how overbought
            signal_strength = max(0, (current_rsi - overbought_level) * 3)

            metrics = {
                'rsi': float(current_rsi),
                'price': float(close[-1]),
                'volume': float(volume[-1]),
                'price_change': float(price_change),
                'signal_strength': float(signal_strength),
                'condition': 'overbought'
            }
        else:
            signal = False
    else:
        signal = False
'''

default_parameters = {
    'rsi_period': 14,
    'oversold_level': 30,
    'overbought_level': 70,
    'min_volume': 100000
}

description = "Identifies overbought and oversold conditions using the Relative Strength Index (RSI)"