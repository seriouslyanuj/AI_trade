
from dataclasses import dataclass
from typing import Literal
from .portfolio_state import PortfolioState
from ..schemas import ProcessedEvent, RiskAdjustedSignal
from ..config import settings

class RiskEngine:
    def __init__(self) -> None:
        self.state = PortfolioState(cash=settings.INITIAL_CAPITAL,
                                    total_equity=settings.INITIAL_CAPITAL,
                                    max_equity=settings.INITIAL_CAPITAL)
        self.max_cap = settings.MAX_CAPITAL_PER_TRADE
        self.max_sector = settings.MAX_SECTOR_EXPOSURE
        self.kill_drawdown = settings.KILL_SWITCH_DRAWDOWN
        self.min_edge = 0.55

    def apply_risk(
        self,
        processed: ProcessedEvent,
        prob_up: float,
        size_raw: float,
    ) -> RiskAdjustedSignal:
        if self.state.drawdown <= self.kill_drawdown:
            return RiskAdjustedSignal(side='HOLD', size=0.0, reason='KillSwitch:MaxDrawdown')

        if prob_up < self.min_edge and prob_up > (1 - self.min_edge):
            return RiskAdjustedSignal(side='HOLD', size=0.0, reason='InsuffEdge')

        side: Literal['BUY', 'SELL'] = 'BUY' if prob_up >= 0.5 else 'SELL'

        if side == 'BUY':
            sec_exp = self.state.sector_exposure(processed.sector)
            if sec_exp >= self.max_sector:
                return RiskAdjustedSignal(side='HOLD', size=0.0, reason='SectorLimit')

        trade_size = min(size_raw, self.max_cap)

        if self.state.cash < self.state.total_equity * trade_size * 0.5:
            trade_size = min(trade_size, self.state.cash / self.state.total_equity)

        if trade_size < 0.001:
            return RiskAdjustedSignal(side='HOLD', size=0.0, reason='SizeTooSmall')

        return RiskAdjustedSignal(side=side, size=round(trade_size, 4), reason='OK')

    def get_atr_stop_loss(self, entry_price: float, atr_val: float, side: str) -> float:
        multiplier = 2.0
        if side == 'BUY':
            return entry_price - multiplier * atr_val
        return entry_price + multiplier * atr_val

    def check_live_eligibility(self, metrics: dict) -> bool:
        return (
            metrics.get('sharpe', 0) > 1.0 and
            metrics.get('max_drawdown', -1) > -0.12 and
            metrics.get('months_stable', 0) >= 3
        )
