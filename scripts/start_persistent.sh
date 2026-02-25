#!/bin/bash
# Auto-restart persistent trading system

cd /workspaces/AI_trade

MAX_RESTARTS=10
RESTART_COUNT=0

echo "🚀 Starting AI Trading System with auto-restart..."

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    echo "[$(date)] Starting server (attempt $((RESTART_COUNT+1)))..."
    
    # Start server
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date)] Server stopped gracefully. Exiting."
        exit 0
    fi
    
    echo "[$(date)] ⚠️  Server crashed with code $EXIT_CODE. Restarting in 5s..."
    RESTART_COUNT=$((RESTART_COUNT+1))
    sleep 5
done

echo "[$(date)] ❌ Max restart attempts reached. Exiting."
exit 1
