import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
from app.backtest.metrics import MetricsCalculator

class BacktestEngine:
    """Event-driven backtesting with historical simulation"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, Dict] = {}  # symbol -> position
        self.trades: List[Dict] = []
        self.pnl_history: List[float] = []
        self.metrics_calc = MetricsCalculator()
        
    async def simulate_day(self, date: str, news_events: List[Dict], price_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """Simulate one trading day
        
        Args:
            date: Trading date (YYYY-MM-DD)
            news_events: List of news events for the day
            price_data: {symbol: [open, high, low, close, volume]}
        """
        day_trades = []
        day_pnl = 0.0
        
        # Sort news by timestamp
        sorted_news = sorted(news_events, key=lambda x: x.get('timestamp', ''))
        
        for news in sorted_news:
            # Extract signal from news (mock decision)
            signal = await self._generate_signal_from_news(news, price_data)
            
            if signal and signal.get('action') != 'HOLD':
                # Execute trade
                trade_result = await self._execute_backtest_trade(signal, price_data, news['timestamp'])
                if trade_result:
                    day_trades.append(trade_result)
                    day_pnl += trade_result.get('pnl', 0.0)
        
        # Mark-to-market at end of day
        mtm_pnl = self._mark_to_market(price_data)
        day_pnl += mtm_pnl
        
        self.pnl_history.append(day_pnl)
        
        return {
            'date': date,
            'trades': len(day_trades),
            'pnl': day_pnl,
            'capital': self.current_capital,
            'positions': len(self.positions)
        }
    
    async def _generate_signal_from_news(self, news: Dict, prices: Dict) -> Optional[Dict]:
        """Generate trading signal from news event"""
        symbol = news.get('symbol', 'RELIANCE')
        sentiment = news.get('sentiment', 0.0)
        
        # Simple rules-based logic for backtesting
        if abs(sentiment) < 0.3:
            return None  # Weak signal, ignore
        
        action = 'BUY' if sentiment > 0 else 'SELL'
        confidence = abs(sentiment)
        
        # Get current price
        price = prices.get(symbol, [1000.0])[3]  # Close price
        
        # Position sizing based on confidence
        allocation = min(0.1 * confidence, 0.2)  # Max 20% per trade
        quantity = int((self.current_capital * allocation) / price)
        
        if quantity == 0:
            return None
        
        return {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'confidence': confidence,
            'reason': news.get('title', 'News event')
        }
    
    async def _execute_backtest_trade(self, signal: Dict, prices: Dict, timestamp: str) -> Optional[Dict]:
        """Execute a trade in backtest mode"""
        symbol = signal['symbol']
        action = signal['action']
        quantity = signal['quantity']
        price = signal['price']
        
        # Simulate slippage (0.1%)
        slippage = 0.001
        exec_price = price * (1 + slippage) if action == 'BUY' else price * (1 - slippage)
        
        # Simulate commission (0.05%)
        commission = abs(quantity * exec_price * 0.0005)
        
        trade_value = quantity * exec_price
        
        if action == 'BUY':
            # Check capital
            if trade_value + commission > self.current_capital:
                return None  # Insufficient capital
            
            self.current_capital -= (trade_value + commission)
            
            # Update or create position
            if symbol in self.positions:
                pos = self.positions[symbol]
                total_qty = pos['quantity'] + quantity
                total_cost = pos['quantity'] * pos['avg_price'] + trade_value
                pos['avg_price'] = total_cost / total_qty
                pos['quantity'] = total_qty
            else:
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': exec_price,
                    'entry_time': timestamp
                }
        
        elif action == 'SELL':
            # Check position
            if symbol not in self.positions or self.positions[symbol]['quantity'] < quantity:
                return None  # No position or insufficient quantity
            
            pos = self.positions[symbol]
            proceeds = trade_value - commission
            self.current_capital += proceeds
            
            # Calculate PnL
            cost_basis = quantity * pos['avg_price']
            pnl = proceeds - cost_basis
            
            # Update position
            pos['quantity'] -= quantity
            if pos['quantity'] == 0:
                del self.positions[symbol]
            
            trade = {
                'timestamp': timestamp,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': exec_price,
                'commission': commission,
                'pnl': pnl,
                'reason': signal.get('reason', '')
            }
            self.trades.append(trade)
            return trade
        
        # For BUY, return trade without PnL (realized on SELL)
        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': exec_price,
            'commission': commission,
            'pnl': 0.0,
            'reason': signal.get('reason', '')
        }
        self.trades.append(trade)
        return trade
    
    def _mark_to_market(self, prices: Dict) -> float:
        """Calculate unrealized PnL"""
        mtm_pnl = 0.0
        for symbol, pos in self.positions.items():
            if symbol in prices:
                current_price = prices[symbol][3]  # Close price
                market_value = pos['quantity'] * current_price
                cost_basis = pos['quantity'] * pos['avg_price']
                mtm_pnl += (market_value - cost_basis)
        return mtm_pnl
    
    async def run_backtest(self, start_date: str, end_date: str, data_generator) -> Dict[str, Any]:
        """Run full backtest simulation
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            data_generator: Async generator yielding (date, news, prices)
        """
        daily_results = []
        
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            
            # Get data for this date
            news, prices = await data_generator(date_str)
            
            # Simulate day
            day_result = await self.simulate_day(date_str, news, prices)
            daily_results.append(day_result)
            
            current += timedelta(days=1)
        
        # Calculate final metrics
        metrics = self.metrics_calc.calculate_all(
            self.trades,
            self.pnl_history,
            self.initial_capital,
            self.current_capital
        )
        
        return {
            'summary': {
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital,
                'total_pnl': self.current_capital - self.initial_capital,
                'total_return_pct': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
                'total_trades': len(self.trades),
                'winning_trades': len([t for t in self.trades if t.get('pnl', 0) > 0]),
                'losing_trades': len([t for t in self.trades if t.get('pnl', 0) < 0])
            },
            'metrics': metrics,
            'daily_results': daily_results,
            'trades': self.trades[-100:]  # Last 100 trades
        }
