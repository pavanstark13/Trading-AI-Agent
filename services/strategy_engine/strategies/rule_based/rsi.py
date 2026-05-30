"""RSI Mean Reversion strategy."""

from typing import Any

import numpy as np

from services.strategy_engine.strategies.base import BaseStrategy, Candle, StrategySignal


class RSIMeanReversionStrategy(BaseStrategy):
    """
    RSI Mean Reversion strategy.

    Generates long signals when RSI is oversold (< 30) and
    short signals when RSI is overbought (> 70).
    Uses divergence confirmation for higher quality signals.
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        params = parameters or {}
        params.setdefault("rsi_period", 14)
        params.setdefault("oversold", 30)
        params.setdefault("overbought", 70)
        params.setdefault("extreme_oversold", 20)
        params.setdefault("extreme_overbought", 80)
        params.setdefault("min_strength", 0.5)
        super().__init__("RSIMeanReversion", params)
        self._min_bars = params["rsi_period"] + 20

    @property
    def strategy_type(self) -> str:
        return "rule_based"

    def generate_signals(self, candles: list[Candle]) -> list[StrategySignal]:
        if not self.validate_candles(candles):
            return []

        _, _, _, closes, _ = self._to_arrays(candles)
        rsi = self._compute_rsi(closes, self.parameters["rsi_period"])

        return self._detect_rsi_signals(candles, closes, rsi)

    def _compute_rsi(self, closes: np.ndarray, period: int) -> np.ndarray:
        """Compute RSI using Wilder's smoothing method."""
        n = len(closes)
        rsi = np.full(n, np.nan)
        if n < period + 1:
            return rsi

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Initial average
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        for i in range(period, n):
            delta = deltas[i - 1]
            gain = delta if delta > 0 else 0.0
            loss = -delta if delta < 0 else 0.0

            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

            if avg_loss == 0:
                rsi[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    def _detect_rsi_signals(
        self,
        candles: list[Candle],
        closes: np.ndarray,
        rsi: np.ndarray,
    ) -> list[StrategySignal]:
        """Generate signals based on RSI levels and divergence."""
        signals = []
        oversold = self.parameters["oversold"]
        overbought = self.parameters["overbought"]
        extreme_oversold = self.parameters["extreme_oversold"]
        extreme_overbought = self.parameters["extreme_overbought"]
        min_strength = self.parameters["min_strength"]

        # Check last few bars for signals
        check_range = range(max(1, len(candles) - 5), len(candles))

        for i in check_range:
            if np.isnan(rsi[i]) or np.isnan(rsi[i - 1]):
                continue

            current_price = closes[i]
            current_rsi = rsi[i]
            prev_rsi = rsi[i - 1]

            # Oversold - potential long
            if current_rsi < oversold and prev_rsi < oversold:
                # Strength increases as RSI gets more extreme
                if current_rsi < extreme_oversold:
                    strength = 0.9
                else:
                    strength = 0.5 + (oversold - current_rsi) / (oversold - extreme_oversold) * 0.4

                if strength < min_strength:
                    continue

                # Confirm with RSI turning up
                if current_rsi > prev_rsi:
                    atr = self._estimate_atr(closes, i)
                    stop_loss = current_price - atr * 1.5
                    take_profit = current_price + atr * 3.0

                    signals.append(StrategySignal(
                        signal_type="entry",
                        direction="long",
                        strength=round(strength, 4),
                        price=current_price,
                        stop_loss=round(stop_loss, 6),
                        take_profit=round(take_profit, 6),
                        metadata={
                            "rsi": round(float(current_rsi), 2),
                            "rsi_level": "extreme_oversold" if current_rsi < extreme_oversold else "oversold",
                            "strategy": "rsi_mean_reversion",
                        },
                    ))

            # Overbought - potential short
            elif current_rsi > overbought and prev_rsi > overbought:
                if current_rsi > extreme_overbought:
                    strength = 0.9
                else:
                    strength = 0.5 + (current_rsi - overbought) / (extreme_overbought - overbought) * 0.4

                if strength < min_strength:
                    continue

                # Confirm with RSI turning down
                if current_rsi < prev_rsi:
                    atr = self._estimate_atr(closes, i)
                    stop_loss = current_price + atr * 1.5
                    take_profit = current_price - atr * 3.0

                    signals.append(StrategySignal(
                        signal_type="entry",
                        direction="short",
                        strength=round(strength, 4),
                        price=current_price,
                        stop_loss=round(stop_loss, 6),
                        take_profit=round(take_profit, 6),
                        metadata={
                            "rsi": round(float(current_rsi), 2),
                            "rsi_level": "extreme_overbought" if current_rsi > extreme_overbought else "overbought",
                            "strategy": "rsi_mean_reversion",
                        },
                    ))

        return signals

    def _estimate_atr(self, closes: np.ndarray, idx: int, period: int = 14) -> float:
        start = max(1, idx - period)
        diffs = np.abs(np.diff(closes[start: idx + 1]))
        return float(np.mean(diffs)) if len(diffs) > 0 else closes[idx] * 0.01

    def get_rsi(self, candles: list[Candle]) -> list[float]:
        """Get RSI values for all candles."""
        if not candles:
            return []
        _, _, _, closes, _ = self._to_arrays(candles)
        rsi = self._compute_rsi(closes, self.parameters["rsi_period"])
        return [float(v) if not np.isnan(v) else 0.0 for v in rsi]
