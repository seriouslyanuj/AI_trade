
import asyncio, random, time
from typing import AsyncIterator
from .events import MacroEvent

async def macro_stream(interval_sec: float = 60.0) -> AsyncIterator[MacroEvent]:
    while True:
        await asyncio.sleep(interval_sec)
        vix = random.uniform(10.0, 28.0)
        regime = 'low_vol' if vix < 14 else ('high_vol' if vix > 22 else 'med_vol')
        yield MacroEvent(
            ts=time.time(),
            india_vix=round(vix, 2),
            fii_flow=round(random.uniform(-2000.0, 2000.0), 2),
            dii_flow=round(random.uniform(-1000.0, 1000.0), 2),
            regime=regime,
        )
