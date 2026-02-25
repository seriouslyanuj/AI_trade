
SECTOR_MAP: dict[str, str] = {
    'RELIANCE': 'Energy', 'HDFCBANK': 'Financials', 'INFY': 'IT',
    'TCS': 'IT', 'ICICIBANK': 'Financials', 'WIPRO': 'IT',
    'SBIN': 'Financials', 'AXISBANK': 'Financials',
    'LT': 'Industrials', 'BAJFINANCE': 'Financials',
}

EVENT_KEYWORDS: dict[str, list[str]] = {
    'earnings': ['earnings', 'quarterly', 'results', 'profit', 'loss', 'revenue', 'q1', 'q2', 'q3', 'q4', 'fy'],
    'regulation': ['rbi', 'sebi', 'regulatory', 'fine', 'penalty', 'compliance', 'scrutiny', 'probe'],
    'deal': ['bags', 'contract', 'deal', 'acquisition', 'merger', 'buyback', 'order', 'wins'],
    'guidance': ['guidance', 'outlook', 'forecast', 'target', 'estimate', 'raises', 'cuts'],
    'macro': ['rbi policy', 'rate', 'inflation', 'gdp', 'index', 'nifty', 'sensex'],
}

EVENT_SENTIMENT_BIAS: dict[str, float] = {
    'earnings': 0.1,
    'regulation': -0.2,
    'deal': 0.3,
    'guidance': 0.0,
    'macro': 0.0,
    'other': 0.0,
}
