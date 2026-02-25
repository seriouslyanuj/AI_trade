
import os
from typing import Optional
import numpy as np

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

class XGBClassifierWrapper:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.bst: Optional[object] = None
        if XGB_AVAILABLE and os.path.exists(model_path):
            self.bst = xgb.Booster()
            self.bst.load_model(model_path)

    def predict_proba(self, X: list[float]) -> float:
        if self.bst is None or not XGB_AVAILABLE:
            return self._heuristic(X)
        arr = np.array(X, dtype=np.float32).reshape(1, -1)
        dmat = xgb.DMatrix(arr)
        return float(self.bst.predict(dmat)[0])

    def _heuristic(self, X: list[float]) -> float:
        # Fallback: weighted sum of sentiment + rsi deviation + macd direction
        sentiment = X[0] if len(X) > 0 else 0.0
        rsi_val = X[2] if len(X) > 2 else 50.0
        macd_val = X[3] if len(X) > 3 else 0.0
        macd_sig = X[4] if len(X) > 4 else 0.0
        score = 0.5
        score += sentiment * 0.3
        score += (50 - rsi_val) / 500.0  # oversold boost
        score += 0.05 if macd_val > macd_sig else -0.05
        return float(max(0.1, min(0.9, score)))
