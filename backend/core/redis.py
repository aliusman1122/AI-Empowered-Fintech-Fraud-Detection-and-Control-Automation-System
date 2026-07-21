"""
backend/core/redis.py
======================
Async Redis client singleton using redis-py >= 5.0 (which includes aioredis logic).
"""
import logging
from redis.asyncio import ConnectionPool, Redis

from backend.core.config import settings

logger = logging.getLogger("finguard.redis")

class RedisClient:
    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._redis: Redis | None = None

    async def connect(self) -> None:
        """Initialize connection pool for Redis"""
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL not set in config, running without caching/velocity engine.")
            return

        try:
            # decode_responses=True means we get strings instead of bytes
            kw = {"decode_responses": True, "max_connections": 50}
            if settings.REDIS_PASSWORD:
                kw["password"] = settings.REDIS_PASSWORD
                
            self._pool = ConnectionPool.from_url(settings.REDIS_URL, **kw)
            self._redis = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._redis.ping()
            logger.info("Connected to Redis at %s", settings.REDIS_URL)
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            self._redis = None

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> Redis | None:
        return self._redis

# Singleton instance
redis_client = RedisClient()
