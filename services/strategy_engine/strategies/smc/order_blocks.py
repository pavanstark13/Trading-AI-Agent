"""SMC Order Block detection strategy."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from services.strategy_engine.strategies.base import BaseStrategy, Candle, StrategySignal


@dataclass
class OrderBlock:
    """Represents an SMC Order Block."""

    index: int
    timestamp: datetime
    top: float
    bottom: float
    direction: str  # bullish or bearish
    strength: float  # 0-1 based on displacement
    is_mitigated: bool = False
    mitigation_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mid(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def size(self) -> float:
        return self.top - self.bottom


class OrderBlockStrategy(BaseStrategy):
    """
    Smart Money Concepts Order Block detection.

    Order blocks are the last bullish/bearish candle before a significant
    displacement move. They represent areas where institutions place orders.

    Bullish Order Block: Last bearish candle before a bullish displacement (BOS)
    Bearish Order Block: Last bullish candle before a bearish displacement (BOS)
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        params = parameters or {}
        params.setdefault("lookback", 20)
        params.setdefault("displacement_multiplier", 1.5)  # ATR multiplier for displacement
        params.setdefault("min_strength", 0.6)
        params.setdefault("atr_period", 14)
        super().__init__("OrderBlock", params)
        self._min_bars = max(self.parameters["lookback"] + self.parameters["atr_period"] + 5, 50)

    @property
    def strategy_type(self) -> str:
        return "smc"

    def generate_signals(self, candles: list[Candle]) -> list[StrategySignal]:
        """Detect order blocks and generate signals when price returns to them."""
        if not self.validate_candles(candles):
            return []

        opens, highs, lows, closes, volumes = self._to_arrays(candles)
        atr = self._compute_atr(highs, lows, closes, self.parameters["atr_period"])
        order_blocks = self._detect_order_blocks(candles, highs, lows, closes, atr)

        return self._generate_ob_signals(candles, order_blocks, atr)

    def _compute_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int,
    ) -> np.ndarray:
        """Compute Average True Range."""
        n = len(closes)
        tr = np.zeros(n)
        tr[0] = highs[0] - lows[0]
        for i in range(1, n):
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
        atr = np.zeros(n)
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        return atr

    def _detect_order_blocks(
        self,
        candles: list[Candle],
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        atr: np.ndarray,
    ) -> list[OrderBlock]:
        """Identify bullish and bearish order blocks."""
        order_blocks: list[OrderBlock] = []
        lookback = self.parameters["lookback"]
        displacement_mult = self.parameters["displacement_multiplier"]

        for i in range(lookback, len(candles) - 1):
            current_atr = atr[i] if atr[i] > 0 else 0.001
            displacement_threshold = current_atr * displacement_mult

            # Check for bullish displacement (strong upward move)
            if closes[i] > closes[i - 1] + displacement_threshold:
                # Find the last bearish candle before this displacement
                ob_index = self._find_last_bearish_candle(candles, i - 1, lookback)
                if ob_index is not None:
                    c = candles[ob_index]
                    displacement = (closes[i] - closes[i - 1]) / current_atr
                    strength = min(displacement / (displacement_mult * 2), 1.0)
                    ob = OrderBlock(
                        index=ob_index,
                        timestamp=c.timestamp,
                        top=max(c.open, c.close),
                        bottom=min(c.open, c.close),
                        direction="bullish",
                        strength=strength,
                        metadata={"displacement_atr": round(displacement, 2)},
                    )
                    # Mark existing OBs as mitigated if price broke through them
                    self._check_mitigation(order_blocks, candles, i)
                    order_blocks.append(ob)

            # Check for bearish displacement (strong downward move)
            elif closes[i] < closes[i - 1] - displacement_threshold:
                # Find the last bullish candle before this displacement
                ob_index = self._find_last_bullish_candle(candles, i - 1, lookback)
                if ob_index is not None:
                    c = candles[ob_index]
                    displacement = (closes[i - 1] - closes[i]) / current_atr
                    strength = min(displacement / (displacement_mult * 2), 1.0)
                    ob = OrderBlock(
                        index=ob_index,
                        timestamp=c.timestamp,
                        top=max(c.open, c.close),
                        bottom=min(c.open, c.close),
                        direction="bearish",
                        strength=strength,
                        metadata={"displacement_atr": round(displacement, 2)},
                    )
                    self._check_mitigation(order_blocks, candles, i)
                    order_blocks.append(ob)

        # Final mitigation check
        self._check_mitigation(order_blocks, candles, len(candles) - 1)
        return order_blocks

    def _find_last_bearish_candle(
        self, candles: list[Candle], end_idx: int, lookback: int
    ) -> int | None:
        """Find the most recent bearish candle within lookback period."""
        start = max(0, end_idx - lookback)
        for i in range(end_idx, start - 1, -1):
            if candles[i].close < candles[i].open:
                return i
        return None

    def _find_last_bullish_candle(
        self, candles: list[Candle], end_idx: int, lookback: int
    ) -> int | None:
        """Find the most recent bullish candle within lookback period."""
        start = max(0, end_idx - lookback)
        for i in range(end_idx, start - 1, -1):
            if candles[i].close > candles[i].open:
                return i
        return None

    def _check_mitigation(
        self, order_blocks: list[OrderBlock], candles: list[Candle], current_idx: int
    ) -> None:
        """Mark order blocks as mitigated if price has entered their zone."""
        for ob in order_blocks:
            if ob.is_mitigated:
                continue
            c = candles[current_idx]
            if ob.direction == "bullish":
                # Bullish OB is mitigated when price trades through the bottom
                if c.low <= ob.bottom:
                    ob.is_mitigated = True
                    ob.mitigation_index = current_idx
            elif ob.direction == "bearish":
                # Bearish OB is mitigated when price trades through the top
                if c.high >= ob.top:
                    ob.is_mitigated = True
                    ob.mitigation_index = current_idx

    def _generate_ob_signals(
        self,
        candles: list[Candle],
        order_blocks: list[OrderBlock],
        atr: np.ndarray,
    ) -> list[StrategySignal]:
        """Generate signals when price returns to unmitigated order blocks."""
        signals = []
        if not candles:
            return signals

        current_candle = candles[-1]
        current_price = current_candle.close
        current_atr = atr[-1] if atr[-1] > 0 else current_price * 0.001
        min_strength = self.parameters["min_strength"]

        for ob in order_blocks:
            if ob.is_mitigated or ob.strength < min_strength:
                continue

            # Check if current price is at/near the order block zone
            if ob.direction == "bullish":
                # Price returning to bullish OB (support)
                if ob.bottom <= current_price <= ob.top * 1.002:
                    stop_loss = ob.bottom - current_atr * 0.5
                    risk = current_price - stop_loss
                    take_profit = current_price + risk * 2.0  # 2:1 RR

                    signals.append(StrategySignal(
                        signal_type="entry",
                        direction="long",
                        strength=ob.strength,
                        price=current_price,
                        stop_loss=round(stop_loss, 6),
                        take_profit=round(take_profit, 6),
                        metadata={
                            "ob_top": ob.top,
                            "ob_bottom": ob.bottom,
                            "ob_timestamp": ob.timestamp.isoformat(),
                            "ob_direction": "bullish",
                            "strategy": "order_block",
                        },
                    ))

            elif ob.direction == "bearish":
                # Price returning to bearish OB (resistance)
                if ob.bottom * 0.998 <= current_price <= ob.top:
                    stop_loss = ob.top + current_atr * 0.5
                    risk = stop_loss - current_price
                    take_profit = current_price - risk * 2.0  # 2:1 RR

                    signals.append(StrategySignal(
                        signal_type="entry",
                        direction="short",
                        strength=ob.strength,
                        price=current_price,
                        stop_loss=round(stop_loss, 6),
                        take_profit=round(take_profit, 6),
                        metadata={
                            "ob_top": ob.top,
                            "ob_bottom": ob.bottom,
                            "ob_timestamp": ob.timestamp.isoformat(),
                            "ob_direction": "bearish",
                            "strategy": "order_block",
                        },
                    ))

        return signals

    def get_all_order_blocks(self, candles: list[Candle]) -> list[OrderBlock]:
        """Public method to get all detected order blocks."""
        if not self.validate_candles(candles):
            return []
        opens, highs, lows, closes, volumes = self._to_arrays(candles)
        atr = self._compute_atr(highs, lows, closes, self.parameters["atr_period"])
        return self._detect_order_blocks(candles, highs, lows, closes, atr)
