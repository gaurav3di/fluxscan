# Sample Screeners for FluxScan
# These are comprehensive sample screeners for various trading strategies

SAMPLE_SCREENERS = {
    # MOMENTUM SCREENERS
    "momentum_breakout": {
        "name": "Momentum Breakout",
        "description": "Identifies stocks breaking out with strong momentum",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Momentum Breakout Scanner
    Finds stocks breaking above recent highs with volume confirmation
    """
    lookback = params.get('lookback', 20)
    volume_multiplier = params.get('volume_multiplier', 1.5)
    rsi_threshold = params.get('rsi_threshold', 60)

    # Calculate indicators
    high_20 = data['high'].rolling(window=lookback).max()
    avg_volume = data['volume'].rolling(window=20).mean()
    rsi = talib.RSI(data['close'], timeperiod=14)

    # Current values
    current_price = data['close'].iloc[-1]
    current_volume = data['volume'].iloc[-1]
    current_high = high_20.iloc[-2]  # Yesterday's 20-day high

    # Check breakout conditions
    price_breakout = current_price > current_high
    volume_surge = current_volume > avg_volume.iloc[-1] * volume_multiplier
    momentum_strong = rsi.iloc[-1] > rsi_threshold

    if price_breakout and volume_surge and momentum_strong:
        return {
            'signal': 'BUY',
            'metrics': {
                'price': float(current_price),
                'breakout_level': float(current_high),
                'volume_ratio': float(current_volume / avg_volume.iloc[-1]),
                'rsi': float(rsi.iloc[-1]),
                'signal_strength': min(100, float(rsi.iloc[-1]))
            }
        }

    return None
''',
        "params": {
            "lookback": 20,
            "volume_multiplier": 1.5,
            "rsi_threshold": 60
        }
    },

    # MEAN REVERSION SCREENERS
    "bollinger_squeeze": {
        "name": "Bollinger Band Squeeze",
        "description": "Detects potential breakouts from Bollinger Band squeeze",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Bollinger Band Squeeze Scanner
    Identifies stocks in a squeeze pattern ready to breakout
    """
    bb_period = params.get('bb_period', 20)
    bb_std = params.get('bb_std', 2)
    squeeze_threshold = params.get('squeeze_threshold', 0.02)

    # Calculate Bollinger Bands
    upper, middle, lower = talib.BBANDS(
        data['close'],
        timeperiod=bb_period,
        nbdevup=bb_std,
        nbdevdn=bb_std,
        matype=0
    )

    # Calculate band width
    band_width = (upper - lower) / middle
    avg_band_width = band_width.rolling(window=50).mean()

    # ATR for volatility
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)

    # Current values
    current_price = data['close'].iloc[-1]
    current_width = band_width.iloc[-1]

    # Check for squeeze
    in_squeeze = current_width < avg_band_width.iloc[-1] * 0.5
    near_middle = abs(current_price - middle.iloc[-1]) / middle.iloc[-1] < squeeze_threshold

    # Volume analysis
    volume_picking_up = data['volume'].iloc[-1] > data['volume'].rolling(5).mean().iloc[-1]

    if in_squeeze and near_middle and volume_picking_up:
        # Determine potential direction
        price_position = (current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
        signal = 'BUY' if price_position > 0.5 else 'HOLD'

        return {
            'signal': signal,
            'metrics': {
                'price': float(current_price),
                'upper_band': float(upper.iloc[-1]),
                'lower_band': float(lower.iloc[-1]),
                'band_width': float(current_width),
                'squeeze_ratio': float(current_width / avg_band_width.iloc[-1]),
                'signal_strength': float((1 - current_width / avg_band_width.iloc[-1]) * 100)
            }
        }

    return None
''',
        "params": {
            "bb_period": 20,
            "bb_std": 2,
            "squeeze_threshold": 0.02
        }
    },

    # TREND FOLLOWING SCREENERS
    "supertrend_signal": {
        "name": "SuperTrend Signal",
        "description": "Generates signals based on SuperTrend indicator",
        "code": '''
import talib
import numpy as np
import pandas as pd

def calculate_supertrend(data, period=7, multiplier=3):
    """Calculate SuperTrend indicator"""
    hl_avg = (data['high'] + data['low']) / 2
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=period)

    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)

    supertrend = pd.Series(index=data.index, dtype=float)
    direction = pd.Series(index=data.index, dtype=int)

    for i in range(period, len(data)):
        if data['close'].iloc[i] <= upper_band.iloc[i]:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1

        # Maintain trend
        if i > period:
            if direction.iloc[i] == 1:
                if supertrend.iloc[i] < supertrend.iloc[i-1]:
                    supertrend.iloc[i] = supertrend.iloc[i-1]
            else:
                if supertrend.iloc[i] > supertrend.iloc[i-1]:
                    supertrend.iloc[i] = supertrend.iloc[i-1]

    return supertrend, direction

def scan(data, params):
    """
    SuperTrend Scanner
    Generates buy/sell signals based on SuperTrend crossovers
    """
    period = params.get('period', 7)
    multiplier = params.get('multiplier', 3)

    # Calculate SuperTrend
    supertrend, direction = calculate_supertrend(data, period, multiplier)

    # Check for signal
    if len(direction) < 2:
        return None

    # Trend change detection
    current_direction = direction.iloc[-1]
    prev_direction = direction.iloc[-2]

    # Additional confirmation with ADX
    adx = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)

    if current_direction == 1 and prev_direction == -1:  # Bullish crossover
        if adx.iloc[-1] > 25:  # Trend strength confirmation
            return {
                'signal': 'BUY',
                'metrics': {
                    'price': float(data['close'].iloc[-1]),
                    'supertrend': float(supertrend.iloc[-1]),
                    'adx': float(adx.iloc[-1]),
                    'trend_strength': float(adx.iloc[-1]),
                    'signal_strength': float(min(100, adx.iloc[-1] * 2))
                }
            }
    elif current_direction == -1 and prev_direction == 1:  # Bearish crossover
        if adx.iloc[-1] > 25:
            return {
                'signal': 'SELL',
                'metrics': {
                    'price': float(data['close'].iloc[-1]),
                    'supertrend': float(supertrend.iloc[-1]),
                    'adx': float(adx.iloc[-1]),
                    'trend_strength': float(adx.iloc[-1]),
                    'signal_strength': float(min(100, adx.iloc[-1] * 2))
                }
            }

    return None
''',
        "params": {
            "period": 7,
            "multiplier": 3
        }
    },

    # VOLATILITY SCREENERS
    "volatility_breakout": {
        "name": "Volatility Breakout",
        "description": "Finds stocks with expanding volatility patterns",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Volatility Breakout Scanner
    Identifies stocks with expanding volatility and directional movement
    """
    atr_period = params.get('atr_period', 14)
    volatility_threshold = params.get('volatility_threshold', 1.5)

    # Calculate ATR and historical volatility
    atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=atr_period)
    avg_atr = atr.rolling(window=50).mean()

    # Calculate Keltner Channels
    ema = talib.EMA(data['close'], timeperiod=20)
    kc_upper = ema + (2 * atr)
    kc_lower = ema - (2 * atr)

    # Current values
    current_price = data['close'].iloc[-1]
    current_atr = atr.iloc[-1]
    volatility_ratio = current_atr / avg_atr.iloc[-1]

    # Check for volatility expansion
    volatility_expanding = volatility_ratio > volatility_threshold

    # Price breaking Keltner Channel
    breaking_upper = current_price > kc_upper.iloc[-1]
    breaking_lower = current_price < kc_lower.iloc[-1]

    if volatility_expanding and (breaking_upper or breaking_lower):
        signal = 'BUY' if breaking_upper else 'SELL'

        return {
            'signal': signal,
            'metrics': {
                'price': float(current_price),
                'atr': float(current_atr),
                'volatility_ratio': float(volatility_ratio),
                'kc_upper': float(kc_upper.iloc[-1]),
                'kc_lower': float(kc_lower.iloc[-1]),
                'signal_strength': float(min(100, volatility_ratio * 40))
            }
        }

    return None
''',
        "params": {
            "atr_period": 14,
            "volatility_threshold": 1.5
        }
    },

    # VOLUME SCREENERS
    "volume_price_trend": {
        "name": "Volume Price Trend",
        "description": "Analyzes volume-price relationship for trend confirmation",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Volume Price Trend Scanner
    Identifies stocks with strong volume-price correlation
    """
    vpt_period = params.get('vpt_period', 14)
    volume_surge = params.get('volume_surge', 2.0)

    # Calculate Volume Price Trend
    price_change = data['close'].pct_change()
    vpt = (price_change * data['volume']).cumsum()
    vpt_sma = vpt.rolling(window=vpt_period).mean()

    # On-Balance Volume
    obv = talib.OBV(data['close'], data['volume'])
    obv_sma = obv.rolling(window=20).mean()

    # Volume analysis
    avg_volume = data['volume'].rolling(window=20).mean()
    current_volume = data['volume'].iloc[-1]
    volume_ratio = current_volume / avg_volume.iloc[-1]

    # Price trend
    ema_short = talib.EMA(data['close'], timeperiod=10)
    ema_long = talib.EMA(data['close'], timeperiod=20)

    # Check conditions
    vpt_rising = vpt.iloc[-1] > vpt_sma.iloc[-1]
    obv_rising = obv.iloc[-1] > obv_sma.iloc[-1]
    volume_high = volume_ratio > volume_surge
    trend_up = ema_short.iloc[-1] > ema_long.iloc[-1]

    if vpt_rising and obv_rising and volume_high and trend_up:
        return {
            'signal': 'BUY',
            'metrics': {
                'price': float(data['close'].iloc[-1]),
                'volume': float(current_volume),
                'volume_ratio': float(volume_ratio),
                'vpt': float(vpt.iloc[-1]),
                'obv': float(obv.iloc[-1]),
                'signal_strength': float(min(100, volume_ratio * 30))
            }
        }

    return None
''',
        "params": {
            "vpt_period": 14,
            "volume_surge": 2.0
        }
    },

    # PATTERN RECOGNITION SCREENERS
    "candlestick_patterns": {
        "name": "Candlestick Pattern Scanner",
        "description": "Identifies bullish and bearish candlestick patterns",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Candlestick Pattern Scanner
    Detects various candlestick patterns for trading signals
    """
    min_pattern_strength = params.get('min_pattern_strength', 100)

    # Detect patterns
    patterns = {
        'hammer': talib.CDLHAMMER(data['open'], data['high'], data['low'], data['close']),
        'inverted_hammer': talib.CDLINVERTEDHAMMER(data['open'], data['high'], data['low'], data['close']),
        'bullish_engulfing': talib.CDLENGULFING(data['open'], data['high'], data['low'], data['close']),
        'morning_star': talib.CDLMORNINGSTAR(data['open'], data['high'], data['low'], data['close']),
        'three_white_soldiers': talib.CDL3WHITESOLDIERS(data['open'], data['high'], data['low'], data['close']),
        'shooting_star': talib.CDLSHOOTINGSTAR(data['open'], data['high'], data['low'], data['close']),
        'bearish_engulfing': talib.CDLENGULFING(data['open'], data['high'], data['low'], data['close']),
        'evening_star': talib.CDLEVENINGSTAR(data['open'], data['high'], data['low'], data['close']),
        'three_black_crows': talib.CDL3BLACKCROWS(data['open'], data['high'], data['low'], data['close'])
    }

    # Check for patterns in the last candle
    bullish_patterns = []
    bearish_patterns = []

    for pattern_name, pattern_values in patterns.items():
        if pattern_values.iloc[-1] > 0:
            if pattern_name in ['hammer', 'inverted_hammer', 'bullish_engulfing', 'morning_star', 'three_white_soldiers']:
                bullish_patterns.append(pattern_name)
            else:
                bearish_patterns.append(pattern_name)
        elif pattern_values.iloc[-1] < 0:
            bearish_patterns.append(pattern_name)

    # Additional confirmation with trend
    sma_20 = talib.SMA(data['close'], timeperiod=20)
    trend = 'UP' if data['close'].iloc[-1] > sma_20.iloc[-1] else 'DOWN'

    if bullish_patterns and trend == 'DOWN':  # Reversal signal
        pattern_strength = len(bullish_patterns) * 50
        if pattern_strength >= min_pattern_strength:
            return {
                'signal': 'BUY',
                'metrics': {
                    'price': float(data['close'].iloc[-1]),
                    'patterns': ', '.join(bullish_patterns),
                    'pattern_count': len(bullish_patterns),
                    'trend': trend,
                    'sma_20': float(sma_20.iloc[-1]),
                    'signal_strength': float(min(100, pattern_strength))
                }
            }
    elif bearish_patterns and trend == 'UP':  # Reversal signal
        pattern_strength = len(bearish_patterns) * 50
        if pattern_strength >= min_pattern_strength:
            return {
                'signal': 'SELL',
                'metrics': {
                    'price': float(data['close'].iloc[-1]),
                    'patterns': ', '.join(bearish_patterns),
                    'pattern_count': len(bearish_patterns),
                    'trend': trend,
                    'sma_20': float(sma_20.iloc[-1]),
                    'signal_strength': float(min(100, pattern_strength))
                }
            }

    return None
''',
        "params": {
            "min_pattern_strength": 100
        }
    },

    # MULTI-INDICATOR SCREENERS
    "triple_confirmation": {
        "name": "Triple Confirmation System",
        "description": "Uses RSI, MACD, and Stochastic for high-probability signals",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Triple Confirmation Scanner
    Combines RSI, MACD, and Stochastic for strong signals
    """
    rsi_oversold = params.get('rsi_oversold', 30)
    rsi_overbought = params.get('rsi_overbought', 70)

    # Calculate indicators
    rsi = talib.RSI(data['close'], timeperiod=14)
    macd, macd_signal, macd_hist = talib.MACD(data['close'])
    slowk, slowd = talib.STOCH(data['high'], data['low'], data['close'])

    # Additional trend filter
    ema_50 = talib.EMA(data['close'], timeperiod=50)
    ema_200 = talib.EMA(data['close'], timeperiod=200)

    # Current values
    current_price = data['close'].iloc[-1]

    # Buy conditions
    rsi_buy = rsi.iloc[-1] < rsi_oversold and rsi.iloc[-1] > rsi.iloc[-2]
    macd_buy = macd_hist.iloc[-1] > macd_hist.iloc[-2] and macd_hist.iloc[-1] > -0.1
    stoch_buy = slowk.iloc[-1] < 20 and slowk.iloc[-1] > slowd.iloc[-1]
    trend_buy = ema_50.iloc[-1] > ema_200.iloc[-1]

    # Sell conditions
    rsi_sell = rsi.iloc[-1] > rsi_overbought and rsi.iloc[-1] < rsi.iloc[-2]
    macd_sell = macd_hist.iloc[-1] < macd_hist.iloc[-2] and macd_hist.iloc[-1] < 0.1
    stoch_sell = slowk.iloc[-1] > 80 and slowk.iloc[-1] < slowd.iloc[-1]
    trend_sell = ema_50.iloc[-1] < ema_200.iloc[-1]

    # Count confirmations
    buy_signals = sum([rsi_buy, macd_buy, stoch_buy])
    sell_signals = sum([rsi_sell, macd_sell, stoch_sell])

    if buy_signals >= 2 and trend_buy:
        return {
            'signal': 'BUY',
            'metrics': {
                'price': float(current_price),
                'rsi': float(rsi.iloc[-1]),
                'macd_hist': float(macd_hist.iloc[-1]),
                'stochastic': float(slowk.iloc[-1]),
                'confirmations': buy_signals,
                'signal_strength': float(buy_signals * 33)
            }
        }
    elif sell_signals >= 2 and trend_sell:
        return {
            'signal': 'SELL',
            'metrics': {
                'price': float(current_price),
                'rsi': float(rsi.iloc[-1]),
                'macd_hist': float(macd_hist.iloc[-1]),
                'stochastic': float(slowk.iloc[-1]),
                'confirmations': sell_signals,
                'signal_strength': float(sell_signals * 33)
            }
        }

    return None
''',
        "params": {
            "rsi_oversold": 30,
            "rsi_overbought": 70
        }
    },

    # FIBONACCI SCREENERS
    "fibonacci_retracement": {
        "name": "Fibonacci Retracement",
        "description": "Identifies stocks at key Fibonacci levels",
        "code": '''
import talib
import numpy as np

def scan(data, params):
    """
    Fibonacci Retracement Scanner
    Finds stocks at key Fibonacci retracement levels
    """
    lookback = params.get('lookback', 50)
    tolerance = params.get('tolerance', 0.02)

    # Find recent high and low
    recent_high = data['high'].rolling(window=lookback).max()
    recent_low = data['low'].rolling(window=lookback).min()

    # Calculate Fibonacci levels
    high = recent_high.iloc[-1]
    low = recent_low.iloc[-1]
    diff = high - low

    fib_levels = {
        '0.236': low + 0.236 * diff,
        '0.382': low + 0.382 * diff,
        '0.500': low + 0.500 * diff,
        '0.618': low + 0.618 * diff,
        '0.786': low + 0.786 * diff
    }

    current_price = data['close'].iloc[-1]

    # Check if price is near any Fibonacci level
    for level_name, level_price in fib_levels.items():
        if abs(current_price - level_price) / level_price < tolerance:
            # Additional confirmation with RSI
            rsi = talib.RSI(data['close'], timeperiod=14)

            # Determine signal based on level and RSI
            if level_name in ['0.618', '0.786'] and rsi.iloc[-1] < 40:
                signal = 'BUY'
            elif level_name in ['0.236', '0.382'] and rsi.iloc[-1] > 60:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            if signal != 'HOLD':
                return {
                    'signal': signal,
                    'metrics': {
                        'price': float(current_price),
                        'fib_level': level_name,
                        'fib_price': float(level_price),
                        'high': float(high),
                        'low': float(low),
                        'rsi': float(rsi.iloc[-1]),
                        'signal_strength': float(70)
                    }
                }

    return None
''',
        "params": {
            "lookback": 50,
            "tolerance": 0.02
        }
    },

    # MARKET STRUCTURE SCREENERS
    "support_resistance": {
        "name": "Support/Resistance Breakout",
        "description": "Detects breakouts of key support and resistance levels",
        "code": '''
import talib
import numpy as np
from scipy.signal import argrelextrema

def find_support_resistance(data, order=5):
    """Find support and resistance levels"""
    highs = data['high'].values
    lows = data['low'].values

    # Find local maxima and minima
    resistance_idx = argrelextrema(highs, np.greater, order=order)[0]
    support_idx = argrelextrema(lows, np.less, order=order)[0]

    resistance_levels = highs[resistance_idx] if len(resistance_idx) > 0 else []
    support_levels = lows[support_idx] if len(support_idx) > 0 else []

    return support_levels, resistance_levels

def scan(data, params):
    """
    Support/Resistance Scanner
    Identifies breakouts of key levels
    """
    lookback = params.get('lookback', 100)
    breakout_threshold = params.get('breakout_threshold', 0.01)
    volume_confirm = params.get('volume_confirm', 1.2)

    # Get recent data
    recent_data = data.tail(lookback)

    # Find support and resistance levels
    support_levels, resistance_levels = find_support_resistance(recent_data)

    current_price = data['close'].iloc[-1]
    prev_close = data['close'].iloc[-2]
    current_volume = data['volume'].iloc[-1]
    avg_volume = data['volume'].rolling(window=20).mean().iloc[-1]

    # Check for resistance breakout
    for resistance in resistance_levels:
        if prev_close < resistance and current_price > resistance * (1 + breakout_threshold):
            if current_volume > avg_volume * volume_confirm:
                return {
                    'signal': 'BUY',
                    'metrics': {
                        'price': float(current_price),
                        'breakout_level': float(resistance),
                        'breakout_pct': float((current_price - resistance) / resistance * 100),
                        'volume_ratio': float(current_volume / avg_volume),
                        'signal_strength': float(min(100, 50 + (current_volume / avg_volume) * 20))
                    }
                }

    # Check for support breakdown
    for support in support_levels:
        if prev_close > support and current_price < support * (1 - breakout_threshold):
            if current_volume > avg_volume * volume_confirm:
                return {
                    'signal': 'SELL',
                    'metrics': {
                        'price': float(current_price),
                        'breakdown_level': float(support),
                        'breakdown_pct': float((support - current_price) / support * 100),
                        'volume_ratio': float(current_volume / avg_volume),
                        'signal_strength': float(min(100, 50 + (current_volume / avg_volume) * 20))
                    }
                }

    return None
''',
        "params": {
            "lookback": 100,
            "breakout_threshold": 0.01,
            "volume_confirm": 1.2
        }
    }
}

def get_screener_list():
    """Get list of available screeners with descriptions"""
    return [
        {
            "id": key,
            "name": screener["name"],
            "description": screener["description"],
            "category": get_screener_category(key)
        }
        for key, screener in SAMPLE_SCREENERS.items()
    ]

def get_screener_category(screener_id):
    """Categorize screeners"""
    categories = {
        "momentum": ["momentum_breakout"],
        "mean_reversion": ["bollinger_squeeze"],
        "trend": ["supertrend_signal"],
        "volatility": ["volatility_breakout"],
        "volume": ["volume_price_trend"],
        "patterns": ["candlestick_patterns"],
        "multi_indicator": ["triple_confirmation"],
        "fibonacci": ["fibonacci_retracement"],
        "structure": ["support_resistance"]
    }

    for category, screeners in categories.items():
        if screener_id in screeners:
            return category
    return "other"

def get_screener_code(screener_id):
    """Get screener code by ID"""
    if screener_id in SAMPLE_SCREENERS:
        return SAMPLE_SCREENERS[screener_id]
    return None