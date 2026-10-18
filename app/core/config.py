# app/core/config.py

# pydantic-settings reads your .env file automatically and maps variables
# to typed Python attributes. This means:
# 1. You get type safety — if DATABASE_URL is missing, app FAILS LOUDLY on startup
#    instead of silently failing on first DB call (which is hard to debug)
# 2. One place to access all config — no os.getenv() scattered everywhere
# 3. Different .env files for dev/staging/prod — same code, different config

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "LinkForge"
    APP_ENV: str = "development"

    # Database
    # asyncpg driver = async postgres — required for FastAPI async routes
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        # tells pydantic-settings WHERE to read the .env file from
        env_file = ".env"
        case_sensitive = True  # DATABASE_URL != database_url


# lru_cache means this function runs ONCE and caches the result.
# Without this, every call to get_settings() would re-read the .env file
# from disk — wasteful and slow. With cache, it reads once at startup.
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Convenience — import this directly instead of calling get_settings() each time
settings = get_settings()