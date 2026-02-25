
import asyncio
import random
import time
from typing import AsyncIterator
from .events import PriceTickEvent

SYMBOLS = ['RELIANCE', 'HDFCBANK', 'INFY', 'TCS', 'ICICIBANK', 'WIPRO', 'SBIN', 'AXISBANK', 'LT', 'BAJFINANCE']

MOCK_PRICES: dict[str, float] = {
    'RELIANCE': 2400.0, 'HDFCBANK': 1650.0, 'INFY': 1450.0,
    'TCS': 3800.0, 'ICICIBANK': 1000.0, 'WIPRO': 470.0,
    'SBIN': 750.0, 'AXISBANK': 1100.0, 'LT': 3500.0, 'BAJFINANCE': 6800.0,
}

async def price_tick_stream(ticks_per_sec: float = 5.0) -> AsyncIterator[PriceTickEvent]:
    prices = dict(MOCK_PRICES)
    interval = 1.0 / ticks_per_sec
    while True:
        await asyncio.sleep(interval)
        sym = random.choice(SYMBOLS)
        pct = random.gauss(0, 0.0005)
        prices[sym] = max(prices[sym] * (1 + pct), 1.0)
        p = prices[sym]
        yield PriceTickEvent(
            symbol=sym,
            ts=time.time(),
            last_price=round(p, 2),
            volume=random.randint(100, 5000),
            high=round(p * 1.001, 2),
            low=round(p * 0.999, 2),
            open=round(p * (1 - pct), 2),
        )
