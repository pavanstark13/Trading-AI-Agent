"""SMC Market Structure Analysis - BOS and CHoCH detection."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from services.strategy_engine.strategies.base import BaseStrategy, Candle, StrategySignal


class MarketStructureType(str, Enum):
    BOS = "bos"     # Break of Structure (trend continuation)
    CHOCH = "choch"  # Change of Character (trend reversal)
    NONE = "none"


@dataclass
class SwingPoint:
    """High or low swing point."""
    index: int
    timestamp: datetime
    price: float
    point_type: str  # 'high' or 'low'


@dataclass
class StructureEvent:
    """Market structure event (BOS or CHoCH)."""
    index: int
    timestamp: datetime
    event_type: MarketStructureType
    direction: str  # 'bullish' or 'bearish'
    break_price: float
    prev_swing: SwingPoint
    metadata: dict[str, Any]


class MarketStructureStrategy(BaseStrategy):
    """
    Market Structure Analysis using Break of Structure (BOS) and
    Change of Character (CHoCH) detection.

    BOS: Price breaks a previous swing high (bullish) or low (bearish)
         indicating trend continuation.

    CHoCH: A reversal of the previous BOS direction, indicating
           potential trend change.

    Market is in uptrend when: Higher Highs (HH) and Higher Lows (HL)
    Market is in downtrend when: Lower Lows (LL) and Lower Highs (LH)
    """

    def __init__(self, parameters: dict[str, Any] | None = None) -> None:
        params = parameters or {}
        params.setdefault("swing_lookback", 5)  # bars left and right to confirm swing
        params.setdefault("min_strength", 0.6)
        super().__init__("MarketStructure", params)
        self._min_bars = max(params["swing_lookback"] * 3 + 10, 30)

    @property
    def strategy_type(self) -> str:
        return "smc"

    def generate_signals(self, candles: list[Candle]) -> list[StrategySignal]:
        """Generate signals based on market structure breaks."""
        if not self.validate_candles(candles):
            return []

        _, highs, lows, closes, _ = self._to_arrays(candles)
        swing_highs, swing_lows = self._identify_swings(candles, highs, lows)
        trend = self._determine_trend(swing_highs, swing_lows)
        events = self._detect_structure_events(candles, swing_highs, swing_lows, closes)

        return self._generate_structure_signals(candles, events, trend, highs, lows, closes)

    def _identify_swings(
        self,
        candles: list[Candle],
        highs: np.ndarray,
        lows: np.ndarray,
    ) -> tuple[list[SwingPoint], list[SwingPoint]]:
        """Identify swing highs and lows."""
        lookback = self.parameters["swing_lookback"]
        swing_highs: list[SwingPoint] = []
        swing_lows: list[SwingPoint] = []

        for i in range(lookback, len(candles) - lookback):
            # Swing high: highest point in lookback window
            window_high = highs[i - lookback: i + lookback + 1]
            if highs[i] == np.max(window_high):
                swing_highs.append(SwingPoint(
                    index=i,
                    timestamp=candles[i].timestamp,
                    price=highs[i],
                    point_type="high",
                ))

            # Swing low: lowest point in lookback window
            window_low = lows[i - lookback: i + lookback + 1]
            if lows[i] == np.min(window_low):
                swing_lows.append(SwingPoint(
                    index=i,
                    timestamp=candles[i].timestamp,
                    price=lows[i],
                    point_type="low",
                ))

        return swing_highs, swing_lows

    def _determine_trend(
        self,
        swing_highs: list[SwingPoint],
        swing_lows: list[SwingPoint],
    ) -> str:
        """Determine current market trend from swing points."""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "neutral"

        # Check last 2 swing highs and lows
        last_hh = swing_highs[-1].price > swing_highs[-2].price  # higher high
        last_hl = swing_lows[-1].price > swing_lows[-2].price    # higher low
        last_ll = swing_lows[-1].price < swing_lows[-2].price    # lower low
        last_lh = swing_highs[-1].price < swing_highs[-2].price  # lower high

        if last_hh and last_hl:
            return "uptrend"
        elif last_ll and last_lh:
            return "downtrend"
        return "ranging"

    def _detect_structure_events(
        self,
        candles: list[Candle],
        swing_highs: list[SwingPoint],
        swing_lows: list[SwingPoint],
        closes: np.ndarray,
    ) -> list[StructureEvent]:
        """Detect BOS and CHoCH events."""
        events: list[StructureEvent] = []
        prev_event_direction: str | None = None

        # Merge and sort all swings
        all_swings = sorted(swing_highs + swing_lows, key=lambda s: s.index)

        for i, swing in enumerate(all_swings):
            # Look for price breaking this swing level
            break_idx = self._find_break(candles, swing, closes)
            if break_idx is None:
                continue

            if swing.point_type == "high":
                # Bullish BOS or CHoCH
                event_type = MarketStructureType.CHOCH if prev_event_direction == "bearish" else MarketStructureType.BOS
                events.append(StructureEvent(
                    index=break_idx,
                    timestamp=candles[break_idx].timestamp,
                    event_type=event_type,
                    direction="bullish",
                    break_price=swing.price,
                    prev_swing=swing,
                    metadata={"swing_index": swing.index, "swing_price": swing.price},
                ))
                prev_event_direction = "bullish"

            elif swing.point_type == "low":
                # Bearish BOS or CHoCH
                event_type = MarketStructureType.CHOCH if prev_event_direction == "bullish" else MarketStructureType.BOS
                events.append(StructureEvent(
                    index=break_idx,
                    timestamp=candles[break_idx].timestamp,
                    event_type=event_type,
                    direction="bearish",
                    break_price=swing.price,
                    prev_swing=swing,
                    metadata={"swing_index": swing.index, "swing_price": swing.price},
                ))
                prev_event_direction = "bearish"

        return events

    def _find_break(
        self,
        candles: list[Candle],
        swing: SwingPoint,
        closes: np.ndarray,
    ) -> int | None:
        """Find the first candle that breaks the swing level."""
        for i in range(swing.index + 1, len(candles)):
            if swing.point_type == "high" and closes[i] > swing.price:
                return i
            elif swing.point_type == "low" and closes[i] < swing.price:
                return i
        return None

    def _generate_structure_signals(
        self,
        candles: list[Candle],
        events: list[StructureEvent],
        trend: str,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
    ) -> list[StrategySignal]:
        """Generate signals from the most recent structure events."""
        signals = []
        if not events:
            return signals

        min_strength = self.parameters["min_strength"]
        # Focus on the last few events
        recent_events = events[-3:]
        current_price = closes[-1]

        for event in recent_events:
            # Only signal on CHoCH (trend reversal) with high confidence
            if event.event_type == MarketStructureType.CHOCH:
                strength = 0.85
                if strength < min_strength:
                    continue

                atr = self._estimate_atr(highs, lows, closes)

                if event.direction == "bullish":
                    stop_loss = event.prev_swing.price - atr * 0.3
                    risk = current_price - stop_loss
                    take_profit = current_price + risk * 2.0
                    signals.append(StrategySignal(
                        signal_type="entry",
                        direction="long",
                        strength=strength,
                        price=current_price,
                        stop_loss=round(stop_loss, 6),
                        take_profit=round(take_profit, 6),
                        metadata={
                            "event": "CHoCH",
                            "break_price": event.break_price,
                            "trend_before": "bearish",
                            "strategy": "market_structure",
                        },
                    ))
                elif event.direction == "bearish":
                    stop_loss = event.prev_swing.price + atr * 0.3
                    risk = stop_loss - current_price
                    take_profit = current_price - risk * 2.0
                    signals.append(StrategySignal(
                        signal_type="entry",
                        direction="short",
                        strength=strength,
                        price=current_price,
                        stop_loss=round(stop_loss, 6),
                        take_profit=round(take_profit, 6),
                        metadata={
                            "event": "CHoCH",
                            "break_price": event.break_price,
                            "trend_before": "bullish",
                            "strategy": "market_structure",
                        },
                    ))

        return signals

    def _estimate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """Quick ATR estimate."""
        n = min(period, len(closes))
        trs = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(-n, 0)]
        return float(np.mean(trs)) if trs else closes[-1] * 0.001

    def get_trend(self, candles: list[Candle]) -> str:
        """Get current market trend."""
        if not self.validate_candles(candles):
            return "neutral"
        _, highs, lows, closes, _ = self._to_arrays(candles)
        swing_highs, swing_lows = self._identify_swings(candles, highs, lows)
        return self._determine_trend(swing_highs, swing_lows)
