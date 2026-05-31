"""SMC Fair Value Gap (FVG) / Imbalance detection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from services.strategy_engine.strategies.base import BaseStrategy, Candle, StrategySignal


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (price imbalance)."""

    index: int  # index of the middle candle
    timestamp: datetime
    top: float
    bottom: float
    direction: str  # bullish or bearish
    size: float  # absolute size of the gap
    size_atr: float  # gap size relative to ATR
    is_filled: bool = False
    fill_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mid(self) -> float:
        return (self.top + self.bottom) / 2


class FairValueGapStrategy(BaseStrategy):
    """
    SMC Fair Value Gap detection and signal generation.

    A Fair Value Gap (FVG) or Imbalance occurs when there is a gap between
    candle[i-1].high and candle[i+1].low (bullish FVG) or
    candle[i-1].low and candle[i+1].high (bearish FVG).

    This represents price imbalance that smart money typically fills.
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        params = parameters or {}
        params.setdefault("min_gap_atr", 0.5)  # Minimum gap size in ATR units
        params.setdefault("atr_period", 14)
        params.setdefault("min_strength", 0.5)
        params.setdefault("lookback", 30)
        super().__init__("FairValueGap", params)
        self._min_bars = max(self.parameters["atr_period"] + 10, 30)

    @property
    def strategy_type(self) -> str:
        return "smc"

    def generate_signals(self, candles: list[Candle]) -> list[StrategySignal]:
        """Detect FVGs and generate signals when price returns to fill them."""
        if not self.validate_candles(candles):
            return []

        _, highs, lows, closes, _ = self._to_arrays(candles)
        atr = self._compute_atr(highs, lows, closes, self.parameters["atr_period"])
        fvgs = self._detect_fvgs(candles, highs, lows, atr)

        return self._generate_fvg_signals(candles, fvgs, atr)

    def _compute_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> np.ndarray:
        n = len(closes)
        tr = np.zeros(n)
        tr[0] = highs[0] - lows[0]
        for i in range(1, n):
            tr[i] = max(
                highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])
            )
        atr = np.zeros(n)
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        return atr

    def _detect_fvgs(
        self,
        candles: list[Candle],
        highs: np.ndarray,
        lows: np.ndarray,
        atr: np.ndarray,
    ) -> list[FairValueGap]:
        """Detect fair value gaps in price data."""
        fvgs: list[FairValueGap] = []
        min_gap_atr = self.parameters["min_gap_atr"]
        lookback = self.parameters["lookback"]
        start_idx = max(1, len(candles) - lookback - 1)

        for i in range(start_idx, len(candles) - 1):
            current_atr = atr[i] if atr[i] > 0 else 0.0001
            gap_threshold = current_atr * min_gap_atr

            # Bullish FVG: candle[i-1].low > candle[i+1].high
            # Gap exists between previous candle's low and next candle's high
            if lows[i - 1] > highs[i + 1]:
                gap_size = lows[i - 1] - highs[i + 1]
                if gap_size >= gap_threshold:
                    fvg = FairValueGap(
                        index=i,
                        timestamp=candles[i].timestamp,
                        top=lows[i - 1],
                        bottom=highs[i + 1],
                        direction="bullish",
                        size=gap_size,
                        size_atr=round(gap_size / current_atr, 2),
                        metadata={"candle_range": round(highs[i] - lows[i], 6)},
                    )
                    fvgs.append(fvg)

            # Bearish FVG: candle[i-1].high < candle[i+1].low
            elif highs[i - 1] < lows[i + 1]:
                gap_size = lows[i + 1] - highs[i - 1]
                if gap_size >= gap_threshold:
                    fvg = FairValueGap(
                        index=i,
                        timestamp=candles[i].timestamp,
                        top=lows[i + 1],
                        bottom=highs[i - 1],
                        direction="bearish",
                        size=gap_size,
                        size_atr=round(gap_size / current_atr, 2),
                        metadata={"candle_range": round(highs[i] - lows[i], 6)},
                    )
                    fvgs.append(fvg)

        # Mark filled FVGs
        for fvg in fvgs:
            for j in range(fvg.index + 2, len(candles)):
                if (
                    fvg.direction == "bullish"
                    and lows[j] <= fvg.top
                    or fvg.direction == "bearish"
                    and highs[j] >= fvg.bottom
                ):
                    fvg.is_filled = True
                    fvg.fill_index = j
                    break

        return fvgs

    def _generate_fvg_signals(
        self,
        candles: list[Candle],
        fvgs: list[FairValueGap],
        atr: np.ndarray,
    ) -> list[StrategySignal]:
        """Generate signals at unfilled FVG zones."""
        if not candles:
            return []

        signals = []
        current_candle = candles[-1]
        current_price = current_candle.close
        current_atr = atr[-1] if atr[-1] > 0 else current_price * 0.001
        min_strength = self.parameters["min_strength"]

        for fvg in fvgs:
            if fvg.is_filled:
                continue

            # Normalize strength: larger gap relative to ATR = stronger signal
            strength = min(fvg.size_atr / 3.0, 1.0)
            if strength < min_strength:
                continue

            if fvg.direction == "bullish":
                # Bullish FVG acts as support - buy when price enters the gap
                if fvg.bottom <= current_price <= fvg.top:
                    stop_loss = fvg.bottom - current_atr * 0.3
                    risk = current_price - stop_loss
                    take_profit = current_price + risk * 2.0

                    signals.append(
                        StrategySignal(
                            signal_type="entry",
                            direction="long",
                            strength=strength,
                            price=current_price,
                            stop_loss=round(stop_loss, 6),
                            take_profit=round(take_profit, 6),
                            metadata={
                                "fvg_top": fvg.top,
                                "fvg_bottom": fvg.bottom,
                                "fvg_size_atr": fvg.size_atr,
                                "fvg_timestamp": fvg.timestamp.isoformat(),
                                "strategy": "fair_value_gap",
                            },
                        )
                    )

            elif fvg.direction == "bearish":
                # Bearish FVG acts as resistance - sell when price enters the gap
                if fvg.bottom <= current_price <= fvg.top:
                    stop_loss = fvg.top + current_atr * 0.3
                    risk = stop_loss - current_price
                    take_profit = current_price - risk * 2.0

                    signals.append(
                        StrategySignal(
                            signal_type="entry",
                            direction="short",
                            strength=strength,
                            price=current_price,
                            stop_loss=round(stop_loss, 6),
                            take_profit=round(take_profit, 6),
                            metadata={
                                "fvg_top": fvg.top,
                                "fvg_bottom": fvg.bottom,
                                "fvg_size_atr": fvg.size_atr,
                                "fvg_timestamp": fvg.timestamp.isoformat(),
                                "strategy": "fair_value_gap",
                            },
                        )
                    )

        return signals

    def get_all_fvgs(self, candles: list[Candle]) -> list[FairValueGap]:
        """Public method to get all detected FVGs."""
        if not self.validate_candles(candles):
            return []
        _, highs, lows, closes, _ = self._to_arrays(candles)
        atr = self._compute_atr(highs, lows, closes, self.parameters["atr_period"])
        return self._detect_fvgs(candles, highs, lows, atr)
