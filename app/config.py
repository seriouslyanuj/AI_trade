from pydantic_settings import BaseSettings
from pydantic import AnyUrl
import os

class Settings(BaseSettings):
    APP_NAME: str = "AI Trade NSE/BSE"
    ENV: str = "dev"
    DEBUG: bool = True
    POSTGRES_DSN: str = "postgresql+asyncpg://trader:password@localhost:5432/ai_trade"
    REDIS_URL: str = "redis://localhost:6379/0"
    HF_API_KEY: str = ""
    COHERE_API_KEY: str = ""
    MODEL_DIR: str = "/workspaces/AI_trade/models"
    XGB_MODEL_PATH: str = "/workspaces/AI_trade/models/xgb_latest.json"
    LATENCY_BUDGET_MS: int = 500
    INITIAL_CAPITAL: float = 100000.0
    MAX_CAPITAL_PER_TRADE: float = 0.05
    MAX_SECTOR_EXPOSURE: float = 0.20
    KILL_SWITCH_DRAWDOWN: float = -0.10
    BROKERAGE_RATE: float = 0.0003
    TAX_RATE: float = 0.0005
    SLIPPAGE_BPS: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
