from typing import Optional, Any
from .indicators import rsi, macd, atr, volume_spike
import random

EVENT_MAP = {'earnings': 1, 'regulation': 2, 'deal': 3, 'guidance': 4, 'macro': 5, 'other': 0}

MOCK_BASE_PRICES = {
    'RELIANCE': 2400, 'HDFCBANK': 1650, 'INFY': 1450, 'TCS': 3800,
    'ICICIBANK': 1000, 'WIPRO': 470, 'SBIN': 750, 'AXISBANK': 1100,
    'LT': 3500, 'BAJFINANCE': 6800,
}

class FeatureService:
    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    async def get_features(
        self,
        redis,  # Optional - can be None
        stock: str,
        sector: str,
        event_type: str,
        sentiment_score: float,
    ) -> list[float]:
        # Try Redis cache first
        if redis is not None:
            try:
                import json
                cached_raw = await redis.get(f'features:{stock}')
                if cached_raw:
                    cached = json.loads(cached_raw)
                    return self._assemble(cached, sentiment_score, event_type)
            except Exception:
                pass

        # In-memory cache fallback
        if stock in self._cache:
            return self._assemble(self._cache[stock], sentiment_score, event_type)

        # Generate features from mock data
        base = MOCK_BASE_PRICES.get(stock, 1000)
        rng = random.Random(hash(stock) % 10000)
        closes = [base * (1 + rng.gauss(0, 0.01)) for _ in range(50)]
        highs = [c * 1.005 for c in closes]
        lows = [c * 0.995 for c in closes]
        vols = [rng.randint(10000, 100000) for _ in range(50)]

        feat: dict[str, Any] = {
            'rsi_14': rsi(closes, 14),
            'macd_line': macd(closes)[0],
            'macd_signal': macd(closes)[1],
            'ema_20': sum(closes[-20:]) / 20,
            'atr_14': atr(highs, lows, closes, 14),
            'vol_spike': volume_spike(vols),
            'sector_strength': 1.0,
            'vol_regime': 0.5,
        }

        # Try to get macro from Redis
        if redis is not None:
            try:
                import json
                macro_raw = await redis.get('macro:latest')
                if macro_raw:
                    macro = json.loads(macro_raw)
                    regime_map = {'low_vol': 0.0, 'med_vol': 0.5, 'high_vol': 1.0}
                    feat['vol_regime'] = regime_map.get(macro.get('regime', 'med_vol'), 0.5)
                    feat['sector_strength'] = float(macro.get(f'sector:{sector}', 1.0))
            except Exception:
                pass

        # Cache in memory for hot path
        self._cache[stock] = feat

        # Cache in Redis if available
        if redis is not None:
            try:
                import json
                await redis.set(f'features:{stock}', json.dumps(feat), ex=15)
            except Exception:
                pass

        return self._assemble(feat, sentiment_score, event_type)

    def _assemble(self, feat: dict, sentiment_score: float, event_type: str) -> list[float]:
        return [
            float(sentiment_score),
            float(EVENT_MAP.get(event_type, 0)),
            float(feat.get('rsi_14', 50.0)),
            float(feat.get('macd_line', 0.0)),
            float(feat.get('macd_signal', 0.0)),
            float(feat.get('ema_20', 1000.0)),
            float(feat.get('atr_14', 10.0)),
            float(feat.get('vol_spike', 1.0)),
            float(feat.get('sector_strength', 1.0)),
            float(feat.get('vol_regime', 0.5)),
        ]
