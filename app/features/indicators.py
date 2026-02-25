
from collections import deque
from typing import Deque, Optional

def ema_step(prev: Optional[float], price: float, period: int) -> float:
    alpha = 2.0 / (period + 1)
    if prev is None:
        return price
    return alpha * price + (1 - alpha) * prev

def rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = closes[-i] - closes[-i - 1]
        (gains if diff >= 0 else losses).append(abs(diff))
    avg_gain = sum(gains) / period if gains else 1e-9
    avg_loss = sum(losses) / period if losses else 1e-9
    return round(100 - 100 / (1 + avg_gain / avg_loss), 4)

def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    if len(closes) < slow + signal:
        return 0.0, 0.0
    ef, es = closes[0], closes[0]
    macd_vals = []
    for p in closes:
        ef = ema_step(ef, p, fast)
        es = ema_step(es, p, slow)
        macd_vals.append(ef - es)
    sig = macd_vals[0]
    for m in macd_vals[1:]:
        sig = ema_step(sig, m, signal)
    return round(macd_vals[-1], 4), round(sig, 4)

def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> float:
    if len(highs) <= 1:
        return 0.0
    trs = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
           for i in range(1, len(highs))]
    n = min(period, len(trs))
    return round(sum(trs[-n:]) / n, 4)

def volume_spike(vols: list[float], window: int = 20) -> float:
    if len(vols) < 2:
        return 1.0
    avg = sum(vols[-window-1:-1]) / max(len(vols[-window-1:-1]), 1)
    return round(vols[-1] / max(avg, 1), 4)
