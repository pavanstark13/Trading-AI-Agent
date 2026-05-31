"""Signal generation service - coordinates strategies to produce trade signals."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from services.strategy_engine.strategies.base import Candle, StrategySignal
from services.strategy_engine.strategies.rule_based.moving_average import (
    MovingAverageCrossoverStrategy,
)
from services.strategy_engine.strategies.rule_based.rsi import RSIMeanReversionStrategy
from services.strategy_engine.strategies.smc.fair_value_gaps import FairValueGapStrategy
from services.strategy_engine.strategies.smc.market_structure import MarketStructureStrategy
from services.strategy_engine.strategies.smc.order_blocks import OrderBlockStrategy

logger = structlog.get_logger(__name__)


STRATEGY_REGISTRY = {
    "order_block": OrderBlockStrategy,
    "fair_value_gap": FairValueGapStrategy,
    "market_structure": MarketStructureStrategy,
    "ma_crossover": MovingAverageCrossoverStrategy,
    "rsi_mean_reversion": RSIMeanReversionStrategy,
}


class SignalGeneratorService:
    """Generates trading signals from market data using configured strategies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _build_candles(self, ohlcv_data: list[dict]) -> list[Candle]:
        """Convert OHLCV dicts to Candle objects."""
        return [
            Candle(
                timestamp=bar.get("timestamp", datetime.now(UTC)),
                open=float(bar["open"]),
                high=float(bar["high"]),
                low=float(bar["low"]),
                close=float(bar["close"]),
                volume=float(bar["volume"]),
            )
            for bar in ohlcv_data
        ]

    def generate_signals(
        self,
        ohlcv_data: list[dict],
        strategy_names: list[str] | None = None,
        strategy_params: dict | None = None,
    ) -> list[StrategySignal]:
        """
        Run multiple strategies on OHLCV data and aggregate signals.

        Args:
            ohlcv_data: List of OHLCV bar dicts with open/high/low/close/volume/timestamp
            strategy_names: List of strategy names to run (defaults to all)
            strategy_params: Per-strategy parameter overrides

        Returns:
            List of StrategySignal objects
        """
        candles = self._build_candles(ohlcv_data)
        if not candles:
            return []

        to_run = strategy_names or list(STRATEGY_REGISTRY.keys())
        params = strategy_params or {}
        all_signals: list[StrategySignal] = []

        for name in to_run:
            strategy_cls = STRATEGY_REGISTRY.get(name)
            if strategy_cls is None:
                logger.warning("Unknown strategy", name=name)
                continue
            try:
                strategy = strategy_cls(parameters=params.get(name))
                signals = strategy.generate_signals(candles)
                logger.debug("Strategy generated signals", strategy=name, count=len(signals))
                all_signals.extend(signals)
            except Exception as e:
                logger.error("Strategy failed", strategy=name, error=str(e))

        return all_signals

    def aggregate_signals(self, signals: list[StrategySignal]) -> list[StrategySignal]:
        """
        Aggregate and deduplicate signals.
        Combine overlapping signals in same direction into higher-confidence signals.
        """
        if not signals:
            return []

        long_signals = [s for s in signals if s.direction == "long"]
        short_signals = [s for s in signals if s.direction == "short"]

        aggregated = []

        if long_signals:
            avg_strength = sum(s.strength for s in long_signals) / len(long_signals)
            if len(long_signals) > 1:
                avg_strength = min(avg_strength * 1.2, 1.0)  # Boost for confluence

            best = max(long_signals, key=lambda s: s.strength)
            best.strength = round(avg_strength, 4)
            best.metadata["confluence_count"] = len(long_signals)
            best.metadata["strategies"] = [
                s.metadata.get("strategy", "unknown") for s in long_signals
            ]
            aggregated.append(best)

        if short_signals:
            avg_strength = sum(s.strength for s in short_signals) / len(short_signals)
            if len(short_signals) > 1:
                avg_strength = min(avg_strength * 1.2, 1.0)

            best = max(short_signals, key=lambda s: s.strength)
            best.strength = round(avg_strength, 4)
            best.metadata["confluence_count"] = len(short_signals)
            best.metadata["strategies"] = [
                s.metadata.get("strategy", "unknown") for s in short_signals
            ]
            aggregated.append(best)

        return aggregated
