"""Test configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    try:
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        yield engine
        await engine.dispose()
    except ImportError:
        pytest.skip("aiosqlite not installed")


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh DB session for each test."""
    from shared.models.base import Base

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def sample_candles():
    """Generate sample OHLCV candle data for strategy testing."""
    from services.strategy_engine.strategies.base import Candle

    candles = []
    price = 100.0
    for i in range(100):
        import random

        change = random.uniform(-0.02, 0.02)
        close = price * (1 + change)
        high = max(price, close) * random.uniform(1.001, 1.005)
        low = min(price, close) * random.uniform(0.995, 0.999)
        candles.append(
            Candle(
                timestamp=datetime(2024, 1, 1, i // 24, i % 24, tzinfo=UTC),
                open=round(price, 4),
                high=round(high, 4),
                low=round(low, 4),
                close=round(close, 4),
                volume=round(random.uniform(10000, 500000), 0),
            )
        )
        price = close
    return candles


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV dict data for backtesting."""
    import random
    from datetime import timedelta

    data = []
    price = 100.0
    now = datetime(2024, 1, 1, tzinfo=UTC)
    for i in range(200):
        change = random.uniform(-0.02, 0.02)
        close = price * (1 + change)
        high = max(price, close) * random.uniform(1.001, 1.005)
        low = min(price, close) * random.uniform(0.995, 0.999)
        data.append(
            {
                "timestamp": now + timedelta(hours=i),
                "open": round(price, 4),
                "high": round(high, 4),
                "low": round(low, 4),
                "close": round(close, 4),
                "volume": round(random.uniform(10000, 500000), 0),
            }
        )
        price = close
    return data


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.exists = AsyncMock(return_value=False)
    return mock
