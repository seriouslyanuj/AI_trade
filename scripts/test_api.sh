#!/bin/bash
# Comprehensive API test suite

BASE_URL="http://localhost:8000"

echo "🧪 Testing AI Trading System API"
echo "================================"

# Test 1: Health Check
echo -n "1. Health Check... "
RESP=$(curl -s $BASE_URL/health)
if echo $RESP | grep -q '"status":"ok"'; then
    echo "✅ PASS"
else
    echo "❌ FAIL: $RESP"
fi

# Test 2: Generate Signal
echo -n "2. Generate Trading Signal... "
RESP=$(curl -s -X POST $BASE_URL/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"id":"test1","timestamp":"2024-02-24T10:00:00","title":"Reliance reports strong quarterly earnings","body":"Strong financial results","source":"test"}')
if echo $RESP | grep -q '"action"'; then
    echo "✅ PASS"
    echo "   Signal: $(echo $RESP | python3 -m json.tool 2>/dev/null | head -5)"
else
    echo "❌ FAIL: $RESP"
fi

# Test 3: Portfolio Summary
echo -n "3. Get Portfolio... "
RESP=$(curl -s $BASE_URL/v1/portfolio/summary)
if echo $RESP | grep -q '"capital"'; then
    echo "✅ PASS"
else
    echo "❌ FAIL: $RESP"
fi

# Test 4: Simulate News
echo -n "4. Simulate News Event... "
RESP=$(curl -s -X POST $BASE_URL/v1/news/simulate)
if echo $RESP | grep -q '"status"'; then
    echo "✅ PASS"
else
    echo "❌ FAIL: $RESP"
fi

# Test 5: Performance Metrics
echo -n "5. Get Performance... "
RESP=$(curl -s $BASE_URL/v1/portfolio/performance)
if echo $RESP | grep -q '"total_pnl"'; then
    echo "✅ PASS"
else
    echo "❌ FAIL: $RESP"
fi

echo "
✅ API Testing Complete!"
