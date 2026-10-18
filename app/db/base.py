# app/db/base.py

# SQLAlchemy 2.0 style — we use DeclarativeBase instead of the old declarative_base()
# This Base class is what all our models will inherit from.
# It keeps track of all models so Alembic can detect them for migrations.

# WHY async SQLAlchemy?
# FastAPI is async — if you use sync SQLAlchemy, your DB call BLOCKS the event loop,
# meaning while one request waits for Postgres, ALL other requests wait too.
# Async SQLAlchemy + asyncpg lets FastAPI handle other requests while waiting for DB.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
