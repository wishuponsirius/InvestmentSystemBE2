import asyncpg
from contextlib import asynccontextmanager
from config import settings


_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        database=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        min_size=settings.POOL_MIN_SIZE,
        max_size=settings.POOL_MAX_SIZE,
    )


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    if _pool is None:
        raise RuntimeError("Pool not initialized. Call init_pool() on startup.")
    async with _pool.acquire() as conn:
        yield conn