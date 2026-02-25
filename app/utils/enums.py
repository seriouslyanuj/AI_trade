
from enum import Enum

class TradingMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"

class SignalSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class VolRegime(str, Enum):
    LOW = "low_vol"
    MED = "med_vol"
    HIGH = "high_vol"
