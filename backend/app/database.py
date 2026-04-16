"""SQLAlchemy async engine and session factory."""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


def _get_engine():
    settings = get_settings()
    db_path = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )


engine = _get_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
