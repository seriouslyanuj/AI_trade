
import re
from typing import Tuple

# Rule-based lightweight sentiment analyzer
# Used in critical path. FinBERT/HuggingFace used only offline.

POS_WORDS = [
    'profit', 'record', 'growth', 'strong', 'rises', 'wins', 'bags', 'deal',
    'buyback', 'milestone', 'positive', 'beat', 'upgrade', 'surges', 'gain',
    'dividend', 'acquisition', 'expansion', 'success', 'award', 'contract',
    'breakthrough', 'excellent', 'robust', 'outperform', 'rally', 'bullish',
]

NEG_WORDS = [
    'loss', 'fine', 'penalty', 'scrutiny', 'probe', 'falls', 'cuts',
    'slowdown', 'decline', 'regulatory', 'fraud', 'risk', 'concern',
    'downgrade', 'weak', 'miss', 'disappoints', 'drops', 'bearish',
    'lawsuit', 'debt', 'default', 'warning', 'crisis', 'slump',
]

URGENCY_HIGH = ['breaking', 'urgent', 'immediately', 'halt', 'suspended', 'crash']
URGENCY_MED = ['today', 'now', 'announces', 'reports', 'updates']

class LightweightSentimentAnalyzer:
    def __init__(self):
        self.pos = set(POS_WORDS)
        self.neg = set(NEG_WORDS)

    def predict(self, text: str) -> Tuple[float, float]:
        words = re.findall(r'\b\w+\b', text.lower())
        pos_count = sum(1 for w in words if w in self.pos)
        neg_count = sum(1 for w in words if w in self.neg)
        total = pos_count + neg_count
        if total == 0:
            return 0.0, 0.4
        score = (pos_count - neg_count) / total
        confidence = min(0.5 + total * 0.05, 0.95)
        return float(score), float(confidence)

    def urgency(self, text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in URGENCY_HIGH):
            return 'high'
        if any(w in lower for w in URGENCY_MED):
            return 'medium'
        return 'low'

_analyzer: LightweightSentimentAnalyzer | None = None

def get_analyzer() -> LightweightSentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = LightweightSentimentAnalyzer()
    return _analyzer
