
import logging
logger = logging.getLogger('ai_trade.monitoring')

def check_alpha_decay(recent_performance: dict, baseline_performance: dict) -> bool:
    recent_sharpe = recent_performance.get('sharpe', 0)
    baseline_sharpe = baseline_performance.get('sharpe', 0)
    decay = (baseline_sharpe - recent_sharpe) / max(abs(baseline_sharpe), 1e-9)
    if decay > 0.30:
        logger.warning(f'Alpha decay detected: {decay:.2%}')
        return True
    return False

def feature_importance_drift(importances: dict, baseline: dict) -> list[str]:
    drifted = []
    for feat, imp in importances.items():
        base = baseline.get(feat, 0.0)
        if base > 0 and abs(imp - base) / base > 0.50:
            drifted.append(feat)
    return drifted
