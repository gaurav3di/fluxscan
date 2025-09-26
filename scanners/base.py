import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple

class BaseScanner(ABC):
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
        self.results = []

    @abstractmethod
    def scan(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        if data is None or data.empty:
            return False

        required_columns = self.get_required_columns()
        for col in required_columns:
            if col not in data.columns:
                return False

        return True

    def get_required_columns(self) -> List[str]:
        return ['open', 'high', 'low', 'close', 'volume']

    def add_result(self, symbol: str, signal: str, metrics: Dict[str, Any]):
        self.results.append({
            'symbol': symbol,
            'signal': signal,
            'metrics': metrics
        })

    def get_results(self) -> List[Dict[str, Any]]:
        return self.results

    def clear_results(self):
        self.results = []

    def calculate_change(self, series: pd.Series, periods: int = 1) -> pd.Series:
        return series.pct_change(periods) * 100

    def calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        return series.rolling(window=period).mean()

    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger_bands(self, series: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        middle_band = self.calculate_sma(series, period)
        std = series.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return upper_band, middle_band, lower_band

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    def calculate_volume_profile(self, volume: pd.Series, price: pd.Series) -> pd.Series:
        return volume * price

    def is_bullish_crossover(self, fast: pd.Series, slow: pd.Series) -> bool:
        if len(fast) < 2 or len(slow) < 2:
            return False

        return (fast.iloc[-1] > slow.iloc[-1]) and (fast.iloc[-2] <= slow.iloc[-2])

    def is_bearish_crossover(self, fast: pd.Series, slow: pd.Series) -> bool:
        if len(fast) < 2 or len(slow) < 2:
            return False

        return (fast.iloc[-1] < slow.iloc[-1]) and (fast.iloc[-2] >= slow.iloc[-2])

    def get_trend(self, series: pd.Series, lookback: int = 20) -> str:
        if len(series) < lookback:
            return 'neutral'

        current = series.iloc[-1]
        past = series.iloc[-lookback]

        change_pct = ((current - past) / past) * 100

        if change_pct > 2:
            return 'bullish'
        elif change_pct < -2:
            return 'bearish'
        else:
            return 'neutral'

    def get_support_resistance(self, high: pd.Series, low: pd.Series, lookback: int = 20) -> Dict[str, float]:
        if len(high) < lookback or len(low) < lookback:
            return {'support': None, 'resistance': None}

        recent_high = high.tail(lookback)
        recent_low = low.tail(lookback)

        resistance = recent_high.max()
        support = recent_low.min()

        return {
            'support': support,
            'resistance': resistance
        }