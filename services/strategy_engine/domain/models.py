"""Strategy Engine - SQLAlchemy ORM models."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models.base import Base, TimestampMixin


class Strategy(TimestampMixin, Base):
    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    signals: Mapped[list["Signal"]] = relationship("Signal", back_populates="strategy")


class Signal(TimestampMixin, Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False
    )
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    strength: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)
    stop_loss: Mapped[float | None] = mapped_column(Numeric(20, 8))
    take_profit: Mapped[float | None] = mapped_column(Numeric(20, 8))
    timeframe: Mapped[str | None] = mapped_column(String(10))
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_executed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="signals")
