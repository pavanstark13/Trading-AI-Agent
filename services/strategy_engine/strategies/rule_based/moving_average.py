"""Moving Average Crossover strategy."""

from typing import Any

import numpy as np

from services.strategy_engine.strategies.base import BaseStrategy, Candle, StrategySignal


class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover strategy.

    Generates long signals when fast MA crosses above slow MA,
    and short signals when fast MA crosses below slow MA.
    Uses EMA by default.
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        params = parameters or {}
        params.setdefault("fast_period", 20)
        params.setdefault("slow_period", 50)
        params.setdefault("signal_period", 9)
        params.setdefault("ma_type", "ema")  # ema or sma
        params.setdefault("min_strength", 0.5)
        super().__init__("MovingAverageCrossover", params)
        self._min_bars = params["slow_period"] + params["signal_period"] + 10

    @property
    def strategy_type(self) -> str:
        return "rule_based"

    def generate_signals(self, candles: list[Candle]) -> list[StrategySignal]:
        if not self.validate_candles(candles):
            return []

        _, _, _, closes, _ = self._to_arrays(candles)
        fast_ma = self._compute_ma(closes, self.parameters["fast_period"])
        slow_ma = self._compute_ma(closes, self.parameters["slow_period"])

        return self._detect_crossovers(candles, closes, fast_ma, slow_ma)

    def _compute_ma(self, closes: np.ndarray, period: int) -> np.ndarray:
        ma_type = self.parameters["ma_type"]
        if ma_type == "ema":
            return self._ema(closes, period)
        return self._sma(closes, period)

    def _sma(self, closes: np.ndarray, period: int) -> np.ndarray:
        sma = np.full(len(closes), np.nan)
        for i in range(period - 1, len(closes)):
            sma[i] = np.mean(closes[i - period + 1: i + 1])
        return sma

    def _ema(self, closes: np.ndarray, period: int) -> np.ndarray:
        ema = np.full(len(closes), np.nan)
        k = 2.0 / (period + 1)
        ema[period - 1] = np.mean(closes[:period])
        for i in range(period, len(closes)):
            ema[i] = closes[i] * k + ema[i - 1] * (1 - k)
        return ema

    def _detect_crossovers(
        self,
        candles: list[Candle],
        closes: np.ndarray,
        fast_ma: np.ndarray,
        slow_ma: np.ndarray,
    ) -> list[StrategySignal]:
        signals = []
        min_strength = self.parameters["min_strength"]

        # Check most recent crossover (last 3 bars)
        for i in range(max(1, len(candles) - 3), len(candles)):
            if np.isnan(fast_ma[i]) or np.isnan(slow_ma[i]) or np.isnan(fast_ma[i-1]) or np.isnan(slow_ma[i-1]):
                continue

            current_price = closes[i]
            # Spread as percentage for strength calculation
            spread_pct = abs(fast_ma[i] - slow_ma[i]) / slow_ma[i]
            strength = min(spread_pct * 50, 1.0)  # Scale spread to 0-1

            if strength < min_strength:
                continue

            # Bullish crossover: fast crosses above slow
            if fast_ma[i] > slow_ma[i] and fast_ma[i-1] <= slow_ma[i-1]:
                atr = self._estimate_atr_simple(closes, i)
                stop_loss = current_price - atr * 2.0
                take_profit = current_price + atr * 4.0

                signals.append(StrategySignal(
                    signal_type="entry",
                    direction="long",
                    strength=strength,
                    price=current_price,
                    stop_loss=round(stop_loss, 6),
                    take_profit=round(take_profit, 6),
                    metadata={
                        "fast_ma": round(float(fast_ma[i]), 4),
                        "slow_ma": round(float(slow_ma[i]), 4),
                        "crossover_type": "bullish",
                        "strategy": "ma_crossover",
                    },
                ))

            # Bearish crossover: fast crosses below slow
            elif fast_ma[i] < slow_ma[i] and fast_ma[i-1] >= slow_ma[i-1]:
                atr = self._estimate_atr_simple(closes, i)
                stop_loss = current_price + atr * 2.0
                take_profit = current_price - atr * 4.0

                signals.append(StrategySignal(
                    signal_type="entry",
                    direction="short",
                    strength=strength,
                    price=current_price,
                    stop_loss=round(stop_loss, 6),
                    take_profit=round(take_profit, 6),
                    metadata={
                        "fast_ma": round(float(fast_ma[i]), 4),
                        "slow_ma": round(float(slow_ma[i]), 4),
                        "crossover_type": "bearish",
                        "strategy": "ma_crossover",
                    },
                ))

        return signals

    def _estimate_atr_simple(self, closes: np.ndarray, idx: int, period: int = 14) -> float:
        start = max(1, idx - period)
        diffs = np.abs(np.diff(closes[start: idx + 1]))
        return float(np.mean(diffs)) if len(diffs) > 0 else closes[idx] * 0.01
