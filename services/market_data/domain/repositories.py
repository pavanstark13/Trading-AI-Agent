"""Market Data Service - Database repository layer."""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.market_data.domain.models import OHLCV, MarketSnapshot, Symbol
from shared.exceptions import RecordNotFoundError

logger = structlog.get_logger(__name__)


class SymbolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, symbol_id: uuid.UUID) -> Symbol:
        result = await self.session.execute(select(Symbol).where(Symbol.id == symbol_id))
        obj = result.scalar_one_or_none()
        if not obj:
            raise RecordNotFoundError("Symbol", symbol_id)
        return obj

    async def get_by_ticker(self, ticker: str) -> Symbol:
        result = await self.session.execute(select(Symbol).where(Symbol.ticker == ticker.upper()))
        obj = result.scalar_one_or_none()
        if not obj:
            raise RecordNotFoundError("Symbol", ticker)
        return obj

    async def list_active(self) -> list[Symbol]:
        result = await self.session.execute(select(Symbol).where(Symbol.is_active == True))  # noqa: E712
        return list(result.scalars().all())

    async def create(self, ticker: str, name: str, exchange: str, asset_type: str = "stock") -> Symbol:
        symbol = Symbol(ticker=ticker.upper(), name=name, exchange=exchange, asset_type=asset_type)
        self.session.add(symbol)
        await self.session.flush()
        logger.info("Symbol created", ticker=ticker)
        return symbol

    async def update_active(self, symbol_id: uuid.UUID, is_active: bool) -> Symbol:
        symbol = await self.get_by_id(symbol_id)
        symbol.is_active = is_active
        await self.session.flush()
        return symbol


class OHLCVRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_bars(
        self,
        symbol_id: uuid.UUID,
        timeframe: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[OHLCV]:
        conditions = [
            OHLCV.symbol_id == symbol_id,
            OHLCV.timeframe == timeframe,
            OHLCV.timestamp >= start,
        ]
        if end:
            conditions.append(OHLCV.timestamp <= end)

        query = (
            select(OHLCV)
            .where(and_(*conditions))
            .order_by(desc(OHLCV.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(query)
        bars = list(result.scalars().all())
        return bars[::-1]  # Return in chronological order

    async def bulk_insert(self, bars: list[dict]) -> int:
        """Bulk insert OHLCV bars, ignoring conflicts."""
        if not bars:
            return 0
        from sqlalchemy.dialects.postgresql import insert  # noqa: PLC0415

        stmt = insert(OHLCV).values(bars).on_conflict_do_nothing()
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def get_latest(self, symbol_id: uuid.UUID, timeframe: str) -> OHLCV | None:
        result = await self.session.execute(
            select(OHLCV)
            .where(OHLCV.symbol_id == symbol_id, OHLCV.timeframe == timeframe)
            .order_by(desc(OHLCV.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()


class MarketSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, snapshot: MarketSnapshot) -> MarketSnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_latest(self, symbol_id: uuid.UUID) -> MarketSnapshot | None:
        result = await self.session.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol_id == symbol_id)
            .order_by(desc(MarketSnapshot.snapshot_time))
            .limit(1)
        )
        return result.scalar_one_or_none()
