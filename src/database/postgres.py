"""PostgreSQL database connection and operations using asyncpg."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.database.models import Base

logger = logging.getLogger(__name__)


class PostgresDB:
    """PostgreSQL database manager with async support."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        """Initialize PostgreSQL connection.

        Args:
            dsn: Database connection string. Defaults to settings.
            pool_size: Connection pool size.
            max_overflow: Maximum overflow connections.
        """
        self.dsn = dsn or settings.postgres_dsn
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        """Get or create async engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.dsn,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                echo=settings.debug,
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager.

        Yields:
            AsyncSession: Database session.
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")

    async def execute_raw(self, sql: str, params: Optional[dict] = None) -> Any:
        """Execute raw SQL query.

        Args:
            sql: SQL query string.
            params: Query parameters.

        Returns:
            Query result.
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            return result

    async def fetch_all(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        """Fetch all rows from a query.

        Args:
            sql: SQL query string.
            params: Query parameters.

        Returns:
            List of rows as dictionaries.
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]

    async def fetch_one(self, sql: str, params: Optional[dict] = None) -> Optional[dict]:
        """Fetch a single row from a query.

        Args:
            sql: SQL query string.
            params: Query parameters.

        Returns:
            Row as dictionary or None.
        """
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            row = result.fetchone()
            if row is None:
                return None
            columns = result.keys()
            return dict(zip(columns, row))

    async def close(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connection closed")

    async def health_check(self) -> bool:
        """Check database connectivity.

        Returns:
            True if connected, False otherwise.
        """
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global instance
_db_instance: Optional[PostgresDB] = None


def get_postgres_db() -> PostgresDB:
    """Get global PostgreSQL database instance.

    Returns:
        PostgresDB instance.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDB(
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
        )
    return _db_instance


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session.

    Yields:
        Database session.
    """
    db = get_postgres_db()
    async with db.get_session() as session:
        yield session
