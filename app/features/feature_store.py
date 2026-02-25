
import json
from typing import Any, Optional
import redis.asyncio as aioredis

class FeatureStore:
    def __init__(self, client: aioredis.Redis) -> None:
        self.client = client

    async def get(self, key: str) -> Optional[dict]:
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, features: dict[str, Any], ttl: int = 30) -> None:
        await self.client.set(key, json.dumps(features), ex=ttl)

    async def get_price_history(self, symbol: str) -> Optional[dict]:
        return await self.get(f'prices:{symbol}')

    async def set_price_history(self, symbol: str, data: dict) -> None:
        await self.set(f'prices:{symbol}', data, ttl=60)

    async def set_macro(self, data: dict) -> None:
        await self.set('macro:latest', data, ttl=300)

    async def get_macro(self) -> Optional[dict]:
        return await self.get('macro:latest')
