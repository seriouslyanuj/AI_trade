import numpy as np
from typing import List, Dict, Any

class MetricsCalculator:
    """Calculate backtest performance metrics"""
    
    def calculate_all(self, trades: List[Dict], pnl_history: List[float], 
                     initial_capital: float, final_capital: float) -> Dict[str, Any]:
        if not trades:
            return {"error": "No trades"}
        
        pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        return {
            "sharpe_ratio": self.sharpe_ratio(pnl_history),
            "max_drawdown": self.max_drawdown(pnl_history, initial_capital),
            "win_rate": len([p for p in pnls if p > 0]) / max(len(pnls), 1),
            "avg_win": np.mean([p for p in pnls if p > 0]) if any(p > 0 for p in pnls) else 0,
            "avg_loss": abs(np.mean([p for p in pnls if p < 0])) if any(p < 0 for p in pnls) else 0
        }
    
    def sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.05) -> float:
        if len(returns) < 2:
            return 0.0
        returns_array = np.array(returns)
        excess = returns_array - (risk_free_rate / 252)
        return np.mean(excess) / (np.std(excess) + 1e-10) * np.sqrt(252)
    
    def max_drawdown(self, pnl_history: List[float], initial_capital: float) -> float:
        capital = initial_capital
        peak = capital
        max_dd = 0.0
        
        for pnl in pnl_history:
            capital += pnl
            peak = max(peak, capital)
            dd = (peak - capital) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
