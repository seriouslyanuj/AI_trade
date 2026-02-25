
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger('ai_trade.retraining')

async def weekly_retraining_loop() -> None:
    logger.info('Retraining scheduler started')
    while True:
        await asyncio.sleep(3600)  # check every hour
        now = datetime.utcnow()
        if now.weekday() == 0 and now.hour == 2:  # Monday 02:00 UTC
            logger.info('Starting weekly retraining job')
            try:
                await run_retraining_job()
            except Exception as e:
                logger.error(f'Retraining failed: {e}')
            await asyncio.sleep(3600)

async def run_retraining_job() -> None:
    from .xgb_training import train_and_save
    path = await asyncio.get_event_loop().run_in_executor(None, train_and_save)
    logger.info(f'New model saved at: {path}')
