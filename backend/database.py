"""
=============================================================================
backend/database.py
=============================================================================
PURPOSE:
  Setup Async PostgreSQL connection using SQLAlchemy 2.x and asyncpg.
  This removes synchronous blocking bottlenecks from the FastAPI server.
=============================================================================
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

from backend.core.config import settings

# Unified dynamic DB url loaded directly from validated pydantic BaseSettings
DATABASE_URL = settings.DATABASE_URL

# Create the asynchronous engine
# pool_size=20, max_overflow=30 allows handling high concurrency without DB lockout
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in logs
    pool_pre_ping=True,  # Check connection health before using
    pool_size=20,
    max_overflow=30,
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()

async def get_async_session() -> AsyncSession:
    """
    FastAPI dependency yielding an async database session per request.
    Closes automatically after the request finishes.
    """
    async with async_session_maker() as session:
        yield session


# =============================================================================
# BACKWARD-COMPAT SYNC SHIMS
# =============================================================================
# auth_service.py imports `get_db` and `SessionLocal` from this module at the
# module level. These stubs exist solely to prevent ImportError when importing
# pure-crypto functions (verify_password, create_access_token, etc.) from
# auth_service. The sync shims are NEVER used in the async request path.
# DO NOT use SessionLocal in new code — use get_async_session() instead.

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session

    _SYNC_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    _sync_engine   = create_engine(_SYNC_URL, pool_pre_ping=True)
    SessionLocal   = sessionmaker(bind=_sync_engine, autocommit=False, autoflush=False)

    def get_db():
        """Sync session dependency kept for backward-compat with auth_service.py."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_tables():
        """Sync helper kept for backward-compat with init_db.py."""
        Base.metadata.create_all(bind=_sync_engine)

except Exception:
    # If psycopg2 / sync driver is not available, stub everything out.
    # The async path is the only one used at runtime in the new architecture.
    SessionLocal = None  # type: ignore[assignment]

    def get_db():  # type: ignore[misc]
        raise RuntimeError("Sync DB not configured — use get_async_session() instead.")

    def create_tables():  # type: ignore[misc]
        raise RuntimeError("Sync DB not configured — use Alembic migrations.")

