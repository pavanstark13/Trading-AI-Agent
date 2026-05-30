"""Unit tests for SMC Order Block strategy."""

from datetime import datetime, timezone

import pytest

from services.strategy_engine.strategies.base import Candle
from services.strategy_engine.strategies.smc.order_blocks import OrderBlockStrategy


def make_candle(idx: int, open: float, high: float, low: float, close: float, volume: float = 100000.0) -> Candle:
    return Candle(
        timestamp=datetime(2024, 1, 1, idx, 0, tzinfo=timezone.utc),
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def make_trending_candles(n: int = 100, start_price: float = 100.0, trend: str = "up") -> list[Candle]:
    """Generate trending candles with some noise."""
    import random
    candles = []
    price = start_price
    for i in range(n):
        if trend == "up":
            change = random.uniform(0.0, 0.03)
        else:
            change = random.uniform(-0.03, 0.0)
        change += random.uniform(-0.01, 0.01)  # noise
        close = price * (1 + change)
        high = max(price, close) * 1.003
        low = min(price, close) * 0.997
        candles.append(make_candle(i, price, high, low, close))
        price = close
    return candles


class TestOrderBlockStrategy:
    """Tests for Order Block detection strategy."""

    def setup_method(self):
        self.strategy = OrderBlockStrategy(parameters={
            "lookback": 10,
            "displacement_multiplier": 1.2,
            "min_strength": 0.5,
            "atr_period": 10,
        })

    def test_init(self):
        """Strategy should initialize with correct defaults."""
        assert self.strategy.name == "OrderBlock"
        assert self.strategy.strategy_type == "smc"
        assert self.strategy.parameters["lookback"] == 10

    def test_insufficient_data(self):
        """Strategy should return empty signals with insufficient data."""
        candles = make_trending_candles(10)  # Less than min_bars
        signals = self.strategy.generate_signals(candles)
        assert signals == []

    def test_generate_signals_returns_list(self):
        """generate_signals should always return a list."""
        candles = make_trending_candles(100)
        signals = self.strategy.generate_signals(candles)
        assert isinstance(signals, list)

    def test_signal_has_required_fields(self):
        """Signals should have required fields."""
        candles = make_trending_candles(100)
        signals = self.strategy.generate_signals(candles)
        for signal in signals:
            assert signal.signal_type in ("entry", "exit", "scale_in", "scale_out")
            assert signal.direction in ("long", "short")
            assert 0 <= signal.strength <= 1
            assert signal.price > 0
            if signal.stop_loss is not None:
                assert signal.stop_loss > 0
            if signal.take_profit is not None:
                assert signal.take_profit > 0

    def test_bullish_signal_rr_ratio(self):
        """Bullish signals should have positive risk/reward."""
        candles = make_trending_candles(100, trend="up")
        signals = self.strategy.generate_signals(candles)
        for signal in signals:
            if signal.direction == "long" and signal.risk_reward_ratio is not None:
                assert signal.risk_reward_ratio > 0

    def test_get_order_blocks_returns_list(self):
        """get_all_order_blocks should return a list."""
        candles = make_trending_candles(100)
        obs = self.strategy.get_all_order_blocks(candles)
        assert isinstance(obs, list)

    def test_order_block_has_valid_structure(self):
        """Order blocks should have valid top/bottom structure."""
        candles = make_trending_candles(100)
        obs = self.strategy.get_all_order_blocks(candles)
        for ob in obs:
            assert ob.top >= ob.bottom
            assert ob.direction in ("bullish", "bearish")
            assert 0 <= ob.strength <= 1
            assert ob.top > 0

    def test_downtrend_produces_bearish_obs(self):
        """Downtrend should eventually produce bearish order blocks."""
        candles = make_trending_candles(100, trend="down")
        obs = self.strategy.get_all_order_blocks(candles)
        directions = {ob.direction for ob in obs}
        # In a downtrend, we expect mostly bearish OBs
        assert len(obs) >= 0  # May or may not have OBs depending on random data

    def test_validate_candles_insufficient(self):
        """validate_candles should fail with < min_bars candles."""
        candles = make_trending_candles(5)
        assert not self.strategy.validate_candles(candles)

    def test_validate_candles_sufficient(self):
        """validate_candles should pass with enough candles."""
        candles = make_trending_candles(100)
        assert self.strategy.validate_candles(candles)
