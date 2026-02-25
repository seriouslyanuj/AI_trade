from dataclasses import dataclass, field
from typing import Literal
import time

@dataclass
class PriceTickEvent:
    symbol: str
    ts: float
    last_price: float
    volume: int
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0

@dataclass
class NewsRawEvent:
    id: str
    ts: float
    source: str
    title: str
    body: str = ""

@dataclass
class MacroEvent:
    ts: float
    india_vix: float
    fii_flow: float
    dii_flow: float
    regime: Literal["low_vol", "med_vol", "high_vol"] = "med_vol"
