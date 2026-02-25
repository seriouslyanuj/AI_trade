from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from .config import settings

# Optional SQLAlchemy (requires DB)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    engine = create_async_engine(
        settings.POSTGRES_DSN,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
    SessionLocal = None
    engine = None

async def get_db():
    if not DB_AVAILABLE or SessionLocal is None:
        yield None
        return
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

_redis_client: Optional[aioredis.Redis] = None
_redis_available: bool = True

async def get_redis() -> Optional[aioredis.Redis]:
    global _redis_client, _redis_available
    if not _redis_available:
        return None
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            await _redis_client.ping()
        except Exception:
            _redis_available = False
            _redis_client = None
            return None
    return _redis_client

async def close_redis() -> None:
    global _redis_client, _redis_available
    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
    _redis_available = True
