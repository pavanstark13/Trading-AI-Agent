"""Market Data Service - SQLAlchemy ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin


class Symbol(TimestampMixin, Base):
    __tablename__ = "symbols"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, default="stock")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    ohlcv_bars: Mapped[list["OHLCV"]] = relationship(
        "OHLCV", back_populates="symbol", lazy="select"
    )
    snapshots: Mapped[list["MarketSnapshot"]] = relationship(
        "MarketSnapshot", back_populates="symbol", lazy="select"
    )


class OHLCV(Base):
    __tablename__ = "ohlcv"
    __table_args__ = (UniqueConstraint("symbol_id", "timeframe", "timestamp"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="ohlcv_bars")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    bid: Mapped[float | None] = mapped_column(Numeric(20, 8))
    ask: Mapped[float | None] = mapped_column(Numeric(20, 8))
    last: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[float | None] = mapped_column(Numeric(20, 2))
    bid_size: Mapped[float | None] = mapped_column(Numeric(20, 2))
    ask_size: Mapped[float | None] = mapped_column(Numeric(20, 2))
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    symbol: Mapped["Symbol"] = relationship("Symbol", back_populates="snapshots")
