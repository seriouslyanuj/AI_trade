from pydantic import BaseModel, Field
from typing import Literal, Optional, List
import time

class NewsEventIn(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    source: str = "unknown"
    title: str
    body: str = ""

class ProcessedEvent(BaseModel):
    stock: str
    sector: str
    event_type: str
    sentiment_score: float
    urgency: Literal["low", "medium", "high"]
    confidence: float
    received_ts: float
    processed_ts: float

class RiskAdjustedSignal(BaseModel):
    side: Literal["BUY", "SELL", "HOLD"]
    size: float
    reason: str

class TradeSignal(BaseModel):
    stock: str
    side: Literal["BUY", "SELL", "HOLD"]
    size: float
    confidence: float
    prob_up: float
    reason: str
    latency_ms: float

class PortfolioSnapshot(BaseModel):
    cash: float
    total_equity: float
    drawdown: float
    positions: dict

class BacktestRequest(BaseModel):
    events: List[NewsEventIn]
    initial_capital: float = 100000.0

class BacktestResultOut(BaseModel):
    sharpe: float
    sortino: float
    max_drawdown: float
    win_rate: float
    final_equity: float
    total_trades: int
