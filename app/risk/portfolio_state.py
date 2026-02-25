
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Position:
    qty: float
    avg_price: float
    sector: str
    symbol: str

    @property
    def notional(self) -> float:
        return self.qty * self.avg_price

@dataclass
class PortfolioState:
    cash: float = 100000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    total_equity: float = 100000.0
    max_equity: float = 100000.0
    trade_count: int = 0

    def update_equity(self, prices: dict[str, float]) -> None:
        equity = self.cash
        for sym, pos in self.positions.items():
            equity += pos.qty * prices.get(sym, pos.avg_price)
        self.total_equity = equity
        if equity > self.max_equity:
            self.max_equity = equity

    @property
    def drawdown(self) -> float:
        if self.max_equity <= 0:
            return 0.0
        return (self.total_equity / self.max_equity) - 1.0

    @property
    def gross_exposure(self) -> float:
        return sum(p.qty * p.avg_price for p in self.positions.values())

    def sector_exposure(self, sector: str) -> float:
        if self.total_equity <= 0:
            return 0.0
        return sum(
            p.qty * p.avg_price for p in self.positions.values() if p.sector == sector
        ) / self.total_equity
