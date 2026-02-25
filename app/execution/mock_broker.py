
from dataclasses import dataclass
from typing import Literal, Optional, List
from ..risk.portfolio_state import PortfolioState, Position
from ..config import settings
import time

@dataclass
class ExecutedOrder:
    stock: str
    side: str
    qty: float
    price: float
    slippage_price: float
    fees: float
    notional: float
    ts: float

class MockBroker:
    def __init__(self, initial_capital: float = None) -> None:
        cap = initial_capital or settings.INITIAL_CAPITAL
        self.portfolio = PortfolioState(cash=cap, total_equity=cap, max_equity=cap)
        self.brokerage_rate = settings.BROKERAGE_RATE
        self.tax_rate = settings.TAX_RATE
        self.slippage_bps = settings.SLIPPAGE_BPS
        self.order_log: List[ExecutedOrder] = []

    def execute(
        self,
        stock: str,
        sector: str,
        side: Literal['BUY', 'SELL'],
        size_fraction: float,
        price: float,
    ) -> Optional[ExecutedOrder]:
        capital = self.portfolio.total_equity
        notional = capital * size_fraction
        if notional < 100:
            return None

        slip = price * self.slippage_bps / 10000.0
        slip_price = price + slip if side == 'BUY' else price - slip
        qty = notional / slip_price
        fees = notional * (self.brokerage_rate + self.tax_rate)

        if side == 'BUY':
            cost = qty * slip_price + fees
            if cost > self.portfolio.cash:
                qty = (self.portfolio.cash - fees) / slip_price
                if qty <= 0:
                    return None
                cost = qty * slip_price + fees
            self.portfolio.cash -= cost
            pos = self.portfolio.positions.get(stock)
            if pos:
                new_qty = pos.qty + qty
                pos.avg_price = (pos.avg_price * pos.qty + slip_price * qty) / new_qty
                pos.qty = new_qty
            else:
                self.portfolio.positions[stock] = Position(
                    qty=qty, avg_price=slip_price, sector=sector, symbol=stock
                )
        else:
            pos = self.portfolio.positions.get(stock)
            if not pos or pos.qty <= 0:
                return None
            sell_qty = min(pos.qty, qty)
            proceeds = sell_qty * slip_price - fees
            self.portfolio.cash += proceeds
            pos.qty -= sell_qty
            if pos.qty < 0.01:
                del self.portfolio.positions[stock]

        order = ExecutedOrder(
            stock=stock, side=side, qty=qty,
            price=price, slippage_price=slip_price,
            fees=fees, notional=notional, ts=time.time(),
        )
        self.order_log.append(order)
        self.portfolio.trade_count += 1
        return order

    def get_portfolio_summary(self) -> dict:
        return {
            'cash': round(self.portfolio.cash, 2),
            'total_equity': round(self.portfolio.total_equity, 2),
            'drawdown': round(self.portfolio.drawdown, 4),
            'trade_count': self.portfolio.trade_count,
            'positions': {s: {'qty': p.qty, 'avg': p.avg_price, 'sector': p.sector}
                          for s, p in self.portfolio.positions.items()},
        }
