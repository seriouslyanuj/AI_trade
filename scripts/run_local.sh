
#!/bin/bash
set -e
echo '=== AI Trade - Local Run ==='
echo 'Installing dependencies...'
pip install -r requirements.txt --quiet

echo 'Creating models directory...'
mkdir -p models

echo 'Training initial XGBoost model...'
python3 -c "
from app.retraining.xgb_training import train_and_save
path = train_and_save()
print(f'Model saved: {path}')
"

echo 'Starting FastAPI server...'
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
