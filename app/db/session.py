# app/db/session.py

# This file sets up:
# 1. The async engine — the actual connection to Postgres
# 2. The session factory — creates individual DB sessions per request
# 3. get_db() — a FastAPI dependency that gives each request its own session
#    and closes it when the request is done (even if it crashed)

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# The engine is the low-level connection pool to Postgres.
# echo=True logs every SQL query to terminal — great for development,
# NEVER use in production (leaks data in logs, floods log storage)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",  # only log SQL in dev
    pool_size=10,  # max persistent connections in pool
    max_overflow=20,  # max extra connections beyond pool_size under load
)

# Session factory — think of it as a "session template"
# expire_on_commit=False means objects don't go "stale" after commit
# (important for async — you don't want SQLAlchemy re-fetching after every commit)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# This is a FastAPI dependency — used with Depends(get_db) in route functions.
# It creates a session for the request, yields it, then ALWAYS closes it.
# The try/finally guarantees cleanup even if the route throws an exception.
# Without this, you'd leak DB connections and eventually exhaust the pool.
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
