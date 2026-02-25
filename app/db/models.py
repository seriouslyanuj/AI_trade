from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, BigInteger, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(16), unique=True, index=True, nullable=False)
    name = Column(String(255))
    sector = Column(String(64), index=True)
    exchange = Column(String(8), nullable=False, default="NSE")
    lot_size = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PriceData(Base):
    __tablename__ = "price_data"
    id = Column(BigInteger, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True, nullable=False)
    ts = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    stock = relationship("Stock")

class News(Base):
    __tablename__ = "news"
    id = Column(BigInteger, primary_key=True, index=True)
    ts = Column(DateTime, index=True, nullable=False, default=datetime.utcnow)
    source = Column(String(64))
    title = Column(String(512))
    body = Column(Text)

class ExtractedEvent(Base):
    __tablename__ = "extracted_events"
    id = Column(BigInteger, primary_key=True, index=True)
    news_id = Column(BigInteger, ForeignKey("news.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    sector = Column(String(64))
    event_type = Column(String(64))
    sentiment_score = Column(Float)
    urgency = Column(String(16))
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    news = relationship("News")
    stock = relationship("Stock")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(BigInteger, primary_key=True, index=True)
    ts = Column(DateTime, index=True, nullable=False, default=datetime.utcnow)
    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True)
    side = Column(String(4))
    qty = Column(Float)
    price = Column(Float)
    notional = Column(Float)
    fees = Column(Float)
    pnl = Column(Float, default=0.0)
    is_live = Column(Boolean, default=False)
    backtest_run_id = Column(BigInteger, index=True, nullable=True)
    stock = relationship("Stock")

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"
    id = Column(BigInteger, primary_key=True, index=True)
    ts = Column(DateTime, index=True, default=datetime.utcnow)
    total_equity = Column(Float)
    cash = Column(Float)
    gross_exposure = Column(Float)
    net_exposure = Column(Float)
    drawdown = Column(Float)
    is_live = Column(Boolean, default=False)
    backtest_run_id = Column(BigInteger, index=True, nullable=True)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String(32))
    version_tag = Column(String(64), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    path = Column(String(255))
    meta = Column(JSON)
    is_active = Column(Boolean, default=False)

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    id = Column(BigInteger, primary_key=True, index=True)
    model_version_id = Column(Integer, ForeignKey("model_versions.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    sharpe = Column(Float)
    sortino = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    beta = Column(Float)
    alpha = Column(Float)
    is_live = Column(Boolean, default=False)
    model_version = relationship("ModelVersion")
