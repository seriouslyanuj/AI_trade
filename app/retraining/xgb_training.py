import asyncio
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class XGBoostRetrainer:
    """Continuous learning pipeline for XGBoost model"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "xgb_latest.json"
        self.history_path = self.model_dir / "training_history.json"
        self.data_buffer: List[Dict] = []
        self.buffer_limit = 1000  # Retrain after 1000 new samples
        self.model = None
        self.training_history = self._load_history()
        
    def _load_history(self) -> List[Dict]:
        """Load training history"""
        if self.history_path.exists():
            with open(self.history_path, 'r') as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        """Save training history"""
        with open(self.history_path, 'w') as f:
            json.dump(self.training_history, f, indent=2)
    
    async def collect_feedback(self, signal_data: Dict, actual_outcome: Dict):
        """Collect feedback from executed trades
        
        Args:
            signal_data: Original signal features
            actual_outcome: Actual trade result (pnl, accuracy, etc.)
        """
        sample = {
            'timestamp': datetime.now().isoformat(),
            'features': signal_data.get('features', {}),
            'predicted_action': signal_data.get('action'),
            'actual_pnl': actual_outcome.get('pnl', 0.0),
            'success': actual_outcome.get('pnl', 0.0) > 0
        }
        
        self.data_buffer.append(sample)
        
        # Trigger retraining if buffer is full
        if len(self.data_buffer) >= self.buffer_limit:
            await self.retrain_model()
    
    async def retrain_model(self) -> Dict[str, Any]:
        """Retrain XGBoost model with new data"""
        if len(self.data_buffer) < 100:
            return {'status': 'skipped', 'reason': 'Insufficient data'}
        
        print(f"🔄 Retraining model with {len(self.data_buffer)} new samples...")
        
        # Prepare training data
        X_new, y_new = self._prepare_training_data(self.data_buffer)
        
        # Load existing model or create new
        if self.model_path.exists():
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(self.model_path))
        else:
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                objective='binary:logistic',
                eval_metric='logloss',
                random_state=42
            )
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_new, y_new, test_size=0.2, random_state=42
        )
        
        # Incremental training
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        metrics = {
            'accuracy': float(accuracy_score(y_val, y_pred)),
            'precision': float(precision_score(y_val, y_pred, zero_division=0)),
            'recall': float(recall_score(y_val, y_pred, zero_division=0)),
            'f1': float(f1_score(y_val, y_pred, zero_division=0))
        }
        
        # Save model
        self.model.save_model(str(self.model_path))
        
        # Update history
        training_record = {
            'timestamp': datetime.now().isoformat(),
            'samples': len(self.data_buffer),
            'metrics': metrics
        }
        self.training_history.append(training_record)
        self._save_history()
        
        # Clear buffer
        self.data_buffer.clear()
        
        print(f"✅ Model retrained. Accuracy: {metrics['accuracy']:.3f}, F1: {metrics['f1']:.3f}")
        
        return {
            'status': 'success',
            'metrics': metrics,
            'training_samples': len(X_train),
            'validation_samples': len(X_val)
        }
    
    def _prepare_training_data(self, samples: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Convert samples to feature matrix and labels"""
        X = []
        y = []
        
        for sample in samples:
            features = sample['features']
            # Extract numeric features (extend as needed)
            feature_vec = [
                features.get('sentiment', 0.0),
                features.get('rsi', 50.0),
                features.get('macd', 0.0),
                features.get('volume_ratio', 1.0),
                features.get('price_change', 0.0),
                features.get('volatility', 0.0),
                float(features.get('prob_up', 0.5)),
                float(features.get('confidence', 0.5))
            ]
            X.append(feature_vec)
            y.append(1 if sample['success'] else 0)
        
        return np.array(X), np.array(y)
    
    async def scheduled_retrain(self, interval_hours: int = 24):
        """Scheduled retraining loop"""
        while True:
            await asyncio.sleep(interval_hours * 3600)
            
            if len(self.data_buffer) >= 50:  # Minimum samples
                try:
                    result = await self.retrain_model()
                    print(f"Scheduled retrain completed: {result}")
                except Exception as e:
                    print(f"Error in scheduled retrain: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get training performance summary"""
        if not self.training_history:
            return {'status': 'no_history'}
        
        latest = self.training_history[-1]
        
        # Calculate trends
        if len(self.training_history) >= 2:
            prev = self.training_history[-2]
            acc_trend = latest['metrics']['accuracy'] - prev['metrics']['accuracy']
        else:
            acc_trend = 0.0
        
        return {
            'latest_training': latest,
            'total_retrains': len(self.training_history),
            'accuracy_trend': acc_trend,
            'buffer_size': len(self.data_buffer)
        }
