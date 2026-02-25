
import time, re
from ..schemas import NewsEventIn, ProcessedEvent
from .taxonomy import SECTOR_MAP, EVENT_KEYWORDS, EVENT_SENTIMENT_BIAS
from .nlp_models import get_analyzer

class NewsProcessor:
    def __init__(self) -> None:
        self.analyzer = get_analyzer()

    def _extract_stock(self, title: str, body: str) -> str:
        text = (title + ' ' + body).upper()
        for sym in SECTOR_MAP:
            if sym in text:
                return sym
        return 'RELIANCE'

    def _classify_event(self, text: str) -> str:
        tl = text.lower()
        for evt_type, kws in EVENT_KEYWORDS.items():
            if any(kw in tl for kw in kws):
                return evt_type
        return 'other'

    def process(self, evt: NewsEventIn) -> ProcessedEvent:
        t0 = time.perf_counter()
        full_text = f'{evt.title}. {evt.body}'
        stock = self._extract_stock(evt.title, evt.body)
        sector = SECTOR_MAP.get(stock, 'Unknown')
        event_type = self._classify_event(full_text)
        score, conf = self.analyzer.predict(full_text)
        bias = EVENT_SENTIMENT_BIAS.get(event_type, 0.0)
        score = max(-1.0, min(1.0, score + bias))
        urgency = self.analyzer.urgency(full_text)
        return ProcessedEvent(
            stock=stock, sector=sector,
            event_type=event_type,
            sentiment_score=round(score, 4),
            urgency=urgency,
            confidence=round(conf, 4),
            received_ts=evt.timestamp,
            processed_ts=time.perf_counter() - t0,
        )
