
import asyncio
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis

from .logging_config import setup_logging
from .config import settings
from .schemas import (
    NewsEventIn, TradeSignal, PortfolioSnapshot,
    BacktestRequest, BacktestResultOut
)
from .processing.news_processor import NewsProcessor
from .features.feature_service import FeatureService
from .models.inference_service import InferenceService
from .risk.risk_engine import RiskEngine
from .execution.mock_broker import MockBroker
from .backtest.engine import BacktestEngine
from .dependencies import get_redis, close_redis
from .ingestion.news_stream import SAMPLE_NEWS
from .retraining.scheduler import weekly_retraining_loop

setup_logging()
logger = logging.getLogger('ai_trade')

# Global singletons
news_processor: NewsProcessor | None = None
feature_service: FeatureService | None = None
inference_service: InferenceService | None = None
risk_engine: RiskEngine | None = None
mock_broker: MockBroker | None = None

_background_tasks: list = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global news_processor, feature_service, inference_service, risk_engine, mock_broker
    logger.info('=== AI Trade System Starting Up ===')

    # Initialize all services
    news_processor = NewsProcessor()
    feature_service = FeatureService()
    inference_service = InferenceService()
    risk_engine = RiskEngine()
    mock_broker = MockBroker()

    # Try to train initial model
    try:
        from .retraining.xgb_training import train_and_save
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, train_and_save)
        inference_service.reload()
        logger.info('Initial XGBoost model trained and loaded')
    except Exception as e:
        logger.warning(f'Model training skipped: {e}')

    # Start background streams
    _background_tasks.append(asyncio.create_task(price_tick_background()))
    _background_tasks.append(asyncio.create_task(macro_update_background()))
    _background_tasks.append(asyncio.create_task(weekly_retraining_loop()))

    logger.info(f'System ready. Capital: Rs {settings.INITIAL_CAPITAL:,.0f}')
    yield

    # Cleanup
    for t in _background_tasks:
        t.cancel()
    await close_redis()
    logger.info('=== AI Trade System Shutdown ===')

async def price_tick_background() -> None:
    from .ingestion.price_stream import price_tick_stream
    from .features.feature_store import FeatureStore
    try:
        redis = await get_redis()
        store = FeatureStore(redis)
        async for tick in price_tick_stream():
            # Update mock broker portfolio with latest prices
            if mock_broker:
                mock_broker.portfolio.update_equity({tick.symbol: tick.last_price})
                risk_engine.state = mock_broker.portfolio
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f'Price stream error: {e}')

async def macro_update_background() -> None:
    from .ingestion.macro_stream import macro_stream
    from .features.feature_store import FeatureStore
    try:
        redis = await get_redis()
        store = FeatureStore(redis)
        async for macro in macro_stream():
            await store.set_macro({
                'regime': macro.regime,
                'india_vix': macro.india_vix,
                'fii_flow': macro.fii_flow,
                'dii_flow': macro.dii_flow,
            })
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f'Macro stream error: {e}')

app = FastAPI(
    title='AI Trade NSE/BSE',
    version='1.0.0',
    description='AI-driven event-based trading system for NSE/BSE',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# ===================== CRITICAL PATH ENDPOINT =====================

@app.post('/v1/signal', response_model=TradeSignal)
async def generate_signal(
    evt: NewsEventIn,
    background_tasks: BackgroundTasks,
    redis: aioredis.Redis = Depends(get_redis),
) -> TradeSignal:
    t0 = time.perf_counter()

    # 1. Local NLP processing (no network I/O)
    processed = news_processor.process(evt)

    # 2. Feature retrieval from Redis cache
    feats = await feature_service.get_features(
        redis=redis,
        stock=processed.stock,
        sector=processed.sector,
        event_type=processed.event_type,
        sentiment_score=processed.sentiment_score,
    )

    # 3. ML inference (in-memory model)
    prob_up, size_raw = inference_service.predict(feats)

    # 4. Risk checks (pure Python)
    signal = risk_engine.apply_risk(processed, prob_up, size_raw)

    latency_ms = (time.perf_counter() - t0) * 1000.0

    # 5. Execute on mock broker if signal is actionable
    if signal.side in ('BUY', 'SELL') and signal.size > 0:
        from .ingestion.price_stream import MOCK_PRICES
        px = MOCK_PRICES.get(processed.stock, 1000.0)
        mock_broker.execute(
            stock=processed.stock,
            sector=processed.sector,
            side=signal.side,
            size_fraction=signal.size,
            price=px,
        )
        mock_broker.portfolio.update_equity(MOCK_PRICES)
        risk_engine.state = mock_broker.portfolio

    # 6. Async logging outside critical path
    background_tasks.add_task(log_signal, evt, processed, signal, latency_ms)

    if latency_ms > settings.LATENCY_BUDGET_MS:
        logger.warning(f'Latency budget exceeded: {latency_ms:.1f}ms')

    return TradeSignal(
        stock=processed.stock,
        side=signal.side,
        size=signal.size,
        confidence=processed.confidence,
        prob_up=prob_up,
        reason=signal.reason,
        latency_ms=round(latency_ms, 2),
    )

async def log_signal(evt, processed, signal, latency_ms: float) -> None:
    logger.info(
        f'SIGNAL | {processed.stock} | {signal.side} | '
        f'size={signal.size:.3f} | prob_up={signal.side} | '
        f'latency={latency_ms:.1f}ms | reason={signal.reason}'
    )

# ===================== PORTFOLIO ENDPOINTS =====================

@app.get('/v1/portfolio', response_model=PortfolioSnapshot)
async def get_portfolio() -> PortfolioSnapshot:
    from .ingestion.price_stream import MOCK_PRICES
    mock_broker.portfolio.update_equity(MOCK_PRICES)
    return PortfolioSnapshot(
        cash=round(mock_broker.portfolio.cash, 2),
        total_equity=round(mock_broker.portfolio.total_equity, 2),
        drawdown=round(mock_broker.portfolio.drawdown, 4),
        positions={
            s: {'qty': round(p.qty, 4), 'avg_price': round(p.avg_price, 2), 'sector': p.sector}
            for s, p in mock_broker.portfolio.positions.items()
        },
    )

@app.get('/v1/portfolio/summary')
async def portfolio_summary() -> dict:
    return mock_broker.get_portfolio_summary()

# ===================== BACKTEST ENDPOINT =====================

@app.post('/v1/backtest', response_model=BacktestResultOut)
async def run_backtest(
    req: BacktestRequest,
    redis: aioredis.Redis = Depends(get_redis),
) -> BacktestResultOut:
    engine = BacktestEngine(initial_capital=req.initial_capital)
    result = await engine.run(req.events, redis=redis)
    return result

@app.post('/v1/backtest/quick')
async def quick_backtest() -> dict:
    import time as _time
    import uuid as _uuid
    from .ingestion.news_stream import SAMPLE_NEWS
    events = []
    for i, (sym, title) in enumerate(SAMPLE_NEWS * 10):
        events.append(NewsEventIn(
            id=str(_uuid.uuid4()),
            timestamp=_time.time() - (len(SAMPLE_NEWS) * 10 - i) * 3600,
            source='backtest',
            title=title,
            body=title + ' Additional context for backtest run.',
        ))
    engine = BacktestEngine(initial_capital=100000.0)
    result = await engine.run(events)
    return result.model_dump()

# ===================== TRAINING ENDPOINT =====================

@app.post('/v1/train')
async def trigger_training(background_tasks: BackgroundTasks) -> dict:
    def _train():
        from .retraining.xgb_training import train_and_save
        return train_and_save()
    background_tasks.add_task(_do_train_and_reload)
    return {'status': 'training_started', 'message': 'XGBoost training queued'}

async def _do_train_and_reload() -> None:
    import asyncio
    from .retraining.xgb_training import train_and_save
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, train_and_save)
    inference_service.reload()
    logger.info(f'Model retrained and reloaded: {path}')

# ===================== LIVE GUARD ENDPOINT =====================

@app.get('/v1/live-eligibility')
async def check_live_eligibility() -> dict:
    from .backtest.metrics import performance_report
    eq = mock_broker.equity_curve if hasattr(mock_broker, 'equity_curve') else          [settings.INITIAL_CAPITAL, mock_broker.portfolio.total_equity]
    report = performance_report(eq)
    eligible = risk_engine.check_live_eligibility({
        'sharpe': report.get('sharpe', 0),
        'max_drawdown': report.get('max_drawdown', -1),
        'months_stable': 0,
    })
    return {
        'eligible_for_live': eligible,
        'metrics': report,
        'requirements': {
            'sharpe_min': 1.0,
            'max_drawdown_limit': -0.12,
            'months_required': 3,
        },
    }

# ===================== HEALTH & ADMIN =====================

@app.get('/health')
async def health() -> dict:
    return {
        'status': 'ok',
        'capital': settings.INITIAL_CAPITAL,
        'model_path': settings.XGB_MODEL_PATH,
        'mode': 'paper',
    }

@app.get('/v1/news/simulate')
async def simulate_news(
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    import random
    sym, title = random.choice(SAMPLE_NEWS)
    evt = NewsEventIn(
        id=str(uuid.uuid4()),
        timestamp=time.time(),
        source='simulation',
        title=title,
        body=title + ' Full article body with more context.',
    )
    from fastapi import BackgroundTasks
    bg = BackgroundTasks()
    signal = await generate_signal(evt, bg, redis)
    return signal.model_dump()

@app.post("/v1/news/simulate")
async def simulate_news():
    """Simulate a news event for testing"""
    import random
    from datetime import datetime
    
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    titles = [
        "{} reports strong quarterly earnings",
        "{} announces major expansion plans",  
        "{} faces regulatory scrutiny",
        "{} launches new product line",
        "{} beats analyst expectations"
    ]
    
    symbol = random.choice(symbols)
    title = random.choice(titles).format(symbol)
    
    return {
        "status": "simulated",
        "symbol": symbol,
        "title": title,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/portfolio/performance")
async def get_performance():
    """Get portfolio performance metrics"""
    from app.execution.paper_trade import PaperTradeEngine
    
    engine = PaperTradeEngine()
    total_trades = len(engine.trade_history)
    winning = len([t for t in engine.trade_history if t.get('pnl', 0) > 0])
    
    return {
        "total_pnl": sum(t.get('pnl', 0) for t in engine.trade_history),
        "total_trades": total_trades,
        "winning_trades": winning,
        "losing_trades": total_trades - winning,
        "win_rate": winning / max(total_trades, 1),
        "capital": engine.capital
    }

