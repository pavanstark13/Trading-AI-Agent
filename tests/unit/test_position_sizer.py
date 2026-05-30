"""Unit tests for PositionSizer service."""

import pytest

from services.risk_management.domain.schemas import PositionSizeMethod, PositionSizeRequest
from services.risk_management.services.position_sizer import PositionSizer
from shared.exceptions import ValidationError


class TestPositionSizer:
    """Tests for PositionSizer."""

    def setup_method(self):
        self.sizer = PositionSizer()

    def _make_request(self, **kwargs) -> PositionSizeRequest:
        defaults = {
            "ticker": "AAPL",
            "entry_price": 150.0,
            "stop_loss": 145.0,
            "account_equity": 100_000.0,
            "risk_per_trade_pct": 0.01,
            "method": PositionSizeMethod.FIXED_FRACTIONAL,
        }
        defaults.update(kwargs)
        return PositionSizeRequest(**defaults)

    def test_fixed_fractional_basic(self):
        """Fixed fractional with 1% risk should calculate correct quantity."""
        request = self._make_request()
        result = self.sizer.calculate(request)

        # risk_amount = 100_000 * 0.01 = 1000
        # risk_per_unit = 150 - 145 = 5
        # qty = 1000 / 5 = 200
        assert result.quantity == pytest.approx(200.0, rel=0.01)
        assert result.risk_amount == pytest.approx(1000.0, rel=0.01)
        assert result.risk_pct == pytest.approx(0.01, rel=0.01)

    def test_fixed_fractional_position_value(self):
        """Position value should equal qty * entry_price."""
        request = self._make_request()
        result = self.sizer.calculate(request)

        expected_value = result.quantity * request.entry_price
        assert result.position_value == pytest.approx(expected_value, rel=0.01)

    def test_kelly_without_win_rate_falls_back(self):
        """Kelly without win_rate should fall back to fixed fractional."""
        request = self._make_request(method=PositionSizeMethod.KELLY)
        result = self.sizer.calculate(request)

        # Should still return a valid result
        assert result.quantity > 0
        assert result.risk_pct <= 0.05  # Should not exceed reasonable limit

    def test_kelly_with_win_rate(self):
        """Kelly with win rate and RR should compute reasonable size."""
        request = self._make_request(
            method=PositionSizeMethod.KELLY,
            win_rate=0.55,
            avg_win_loss_ratio=1.5,
            kelly_fraction=0.25,
        )
        result = self.sizer.calculate(request)
        assert result.quantity > 0
        assert result.method == "kelly"

    def test_max_position_cap(self):
        """Position size should never exceed 20% of equity."""
        request = self._make_request(
            entry_price=100.0,
            stop_loss=99.99,  # Tiny stop loss = huge position
            risk_per_trade_pct=0.10,
        )
        result = self.sizer.calculate(request)

        max_allowed = 100_000 * 0.20
        assert result.position_value <= max_allowed + 0.01

    def test_invalid_entry_price(self):
        """Entry price of 0 should raise ValidationError."""
        with pytest.raises(Exception):  # Pydantic will catch this
            self._make_request(entry_price=0)

    def test_entry_equals_stop_raises(self):
        """Entry == stop_loss should raise ValidationError."""
        request = self._make_request(entry_price=150.0, stop_loss=150.0)
        with pytest.raises(ValidationError):
            self.sizer.calculate(request)

    def test_short_trade_sizing(self):
        """Stop loss above entry (short trade) should work correctly."""
        request = self._make_request(
            entry_price=150.0,
            stop_loss=155.0,  # Stop above entry = short
        )
        result = self.sizer.calculate(request)

        # risk_per_unit = |150 - 155| = 5
        # qty = 1000 / 5 = 200
        assert result.quantity == pytest.approx(200.0, rel=0.01)

    def test_different_risk_percentages(self):
        """Higher risk percentage should produce larger positions."""
        r1 = self.sizer.calculate(self._make_request(risk_per_trade_pct=0.005))
        r2 = self.sizer.calculate(self._make_request(risk_per_trade_pct=0.02))
        assert r2.quantity > r1.quantity

    def test_response_ticker_matches(self):
        """Response ticker should match request ticker."""
        request = self._make_request(ticker="NVDA")
        result = self.sizer.calculate(request)
        assert result.ticker == "NVDA"
