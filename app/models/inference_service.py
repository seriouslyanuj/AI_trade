
from typing import Tuple
from ..config import settings
from .xgb_model import XGBClassifierWrapper

class InferenceService:
    def __init__(self) -> None:
        self.clf = XGBClassifierWrapper(settings.XGB_MODEL_PATH)

    def predict(self, features: list[float]) -> Tuple[float, float]:
        prob_up = self.clf.predict_proba(features)
        size_raw = max(0.0, min(1.0, (prob_up - 0.5) * 2.0))
        return round(prob_up, 4), round(size_raw, 4)

    def reload(self) -> None:
        self.clf = XGBClassifierWrapper(settings.XGB_MODEL_PATH)
