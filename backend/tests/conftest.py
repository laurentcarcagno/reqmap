"""Shared pytest fixtures for the backend test suite."""

import os
import pytest
from pathlib import Path
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set env vars BEFORE importing any app module so pydantic-settings picks them up
_CONFIG_PATH = str(Path(__file__).resolve().parents[2] / "config" / "customers.json")
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:?cache=shared&uri=true"
os.environ["CUSTOMERS_CONFIG_PATH"] = _CONFIG_PATH

# Now safe to import app modules
from app.database import Base, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
import app.models.document  # noqa: F401, E402
import app.models.node  # noqa: F401, E402

# Create a test-local engine (in-memory, same connection for all operations)
_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_test_engine = create_async_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
_TestSession = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with _TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


_app = create_app()
_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
async def create_tables():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as ac:
        yield ac
