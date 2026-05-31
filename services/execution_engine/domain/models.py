"""Execution Engine - ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_order_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategies.id")
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signals.id")
    )
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    stop_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    time_in_force: Mapped[str] = mapped_column(String(10), nullable=False, default="day")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    filled_qty: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    avg_fill_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    broker_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="order")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False
    )
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    pnl: Mapped[float | None] = mapped_column(Numeric(20, 8))
    pnl_pct: Mapped[float | None] = mapped_column(Numeric(10, 6))
    is_closing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="trades")


class Position(TimestampMixin, Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id"), unique=True
    )
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    avg_entry_price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    current_price: Mapped[float | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl: Mapped[float | None] = mapped_column(Numeric(20, 8))
    unrealized_pnl_pct: Mapped[float | None] = mapped_column(Numeric(10, 6))
    realized_pnl: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
