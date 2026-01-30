# 🔌 API Documentation - Trading Signal Endpoint

## Overview

The `/signal` endpoint generates actionable trading recommendations by combining:
- Machine learning predictions (XGBoost binary classifier)
- Technical analysis (RSI, volatility)
- Risk management logic
- User-defined risk tolerance

---

## Endpoint Details

### `POST /signal`

Generate a trading signal with comprehensive analysis.

**URL:** `http://127.0.0.1:8000/signal`

**Method:** `POST`

**Content-Type:** `application/json`

---

## Request Schema

```json
{
  "symbol": "string",           // Required: Market symbol
  "risk_tolerance": "string"    // Optional: "LOW" | "MEDIUM" | "HIGH"
                                // Default: "MEDIUM"
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | string | Yes | - | Market symbol (AAPL, BTC-USD, etc.) |
| `risk_tolerance` | string | No | "MEDIUM" | User's risk profile |

### Valid Risk Tolerance Values

- **`LOW`**: Conservative approach
  - Confidence threshold: 75%
  - Use case: Retirement accounts, risk-averse investors
  
- **`MEDIUM`**: Balanced approach  
  - Confidence threshold: 65%
  - Use case: Standard portfolio management
  
- **`HIGH`**: Aggressive approach
  - Confidence threshold: 55%
  - Use case: Day trading, high-risk tolerance

---

## Response Schema

### Success Response (200 OK)

```json
{
  "symbol": "string",
  "action": "BUY" | "HOLD" | "AVOID",
  "confidence": float,           // 0.0 to 1.0
  "direction": "UP" | "DOWN",
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "reasons": ["string"],         // Array of decision factors
  "technical_data": {
    "rsi": float,                // 0 to 100
    "rsi_status": "OVERSOLD" | "NEUTRAL" | "OVERBOUGHT",
    "volatility": float,         // Percentage (e.g., 0.0245 = 2.45%)
    "recent_close": float        // Latest closing price
  },
  "risk_tolerance": "string"     // Echoes back user's setting
}
```

### Error Response (200 OK with error field)

```json
{
  "error": "string"              // Error message
}
```

Common errors:
- `"Invalid symbol or no data available"` - Symbol not found
- `"Not enough data to compute indicators"` - Insufficient history

---

## Action Types Explained

### 🟢 BUY
**When issued:**
- Confidence ≥ threshold for risk tolerance
- Direction = UP
- RSI < 70 (not overbought)

**Interpretation:**
Strong signal to enter a long position. Model has high confidence in upward movement, supported by technical indicators.

---

### 🟡 HOLD
**When issued:**
- Confidence below threshold OR
- Strong signal but RSI > 70 (overbought) OR
- Unclear/weak signal

**Interpretation:**
Wait for better conditions. Either signal is too weak, or market conditions suggest caution despite strong prediction.

---

### 🔴 AVOID
**When issued:**
- Confidence ≥ threshold
- Direction = DOWN
- May have high volatility or overbought RSI

**Interpretation:**
Strong signal to stay out or exit positions. Model predicts downward movement with high confidence.

---

## Example Requests & Responses

### Example 1: Conservative Investor - Apple Stock

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "risk_tolerance": "LOW"
  }'
```

**Response:**
```json
{
  "symbol": "AAPL",
  "action": "BUY",
  "confidence": 0.782,
  "direction": "UP",
  "risk_level": "LOW",
  "reasons": [
    "Strong upward prediction (78.2% confidence)",
    "RSI oversold (28.5) - good entry point",
    "Low volatility environment"
  ],
  "technical_data": {
    "rsi": 28.5,
    "rsi_status": "OVERSOLD",
    "volatility": 0.0123,
    "recent_close": 175.43
  },
  "risk_tolerance": "LOW"
}
```

---

### Example 2: Aggressive Trader - Tesla

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "risk_tolerance": "HIGH"
  }'
```

**Response:**
```json
{
  "symbol": "TSLA",
  "action": "HOLD",
  "confidence": 0.621,
  "direction": "UP",
  "risk_level": "HIGH",
  "reasons": [
    "Strong upward signal (62.1% confidence)",
    "But RSI shows overbought conditions (73.4)",
    "Waiting for pullback recommended"
  ],
  "technical_data": {
    "rsi": 73.4,
    "rsi_status": "OVERBOUGHT",
    "volatility": 0.0287,
    "recent_close": 238.91
  },
  "risk_tolerance": "HIGH"
}
```

---

### Example 3: Crypto - Bitcoin

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC-USD",
    "risk_tolerance": "MEDIUM"
  }'
```

**Response:**
```json
{
  "symbol": "BTC-USD",
  "action": "AVOID",
  "confidence": 0.712,
  "direction": "DOWN",
  "risk_level": "HIGH",
  "reasons": [
    "High confidence downward trend (71.2%)",
    "RSI confirms overbought (76.8)",
    "High volatility increases risk"
  ],
  "technical_data": {
    "rsi": 76.8,
    "rsi_status": "OVERBOUGHT",
    "volatility": 0.0487,
    "recent_close": 43251.89
  },
  "risk_tolerance": "MEDIUM"
}
```

---

### Example 4: Invalid Symbol

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "FAKE123",
    "risk_tolerance": "MEDIUM"
  }'
```

**Response:**
```json
{
  "error": "Invalid symbol or no data available"
}
```

---

## Signal Generation Algorithm

### Pseudocode

```python
def generate_signal(direction, confidence, volatility, rsi, risk_tolerance):
    
    # Step 1: Determine confidence threshold
    threshold = {
        "LOW": 0.75,
        "MEDIUM": 0.65,
        "HIGH": 0.55
    }[risk_tolerance]
    
    # Step 2: Assess risk level
    if volatility > 0.03:
        risk_level = "HIGH"
    elif volatility > 0.015:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # Step 3: Check RSI conditions
    rsi_overbought = rsi > 70
    rsi_oversold = rsi < 30
    
    # Step 4: Apply decision rules
    if confidence >= threshold and direction == "UP":
        if rsi_overbought:
            return "HOLD" (wait for pullback)
        else:
            return "BUY"
    
    elif confidence >= threshold and direction == "DOWN":
        return "AVOID"
    
    else:
        return "HOLD" (insufficient confidence)
```

---

## Technical Indicator Definitions

### RSI (Relative Strength Index)
- **Range:** 0 to 100
- **Period:** 14 days
- **Interpretation:**
  - RSI > 70: Overbought (potential reversal down)
  - RSI < 30: Oversold (potential reversal up)
  - RSI 30-70: Neutral

### Volatility
- **Calculation:** 10-day standard deviation of returns
- **Interpretation:**
  - High (>3%): Risky, unpredictable moves
  - Medium (1.5%-3%): Normal market conditions
  - Low (<1.5%): Stable, predictable

### Confidence
- **Source:** XGBoost probability output
- **Interpretation:**
  - >75%: Very strong signal
  - 65-75%: Strong signal
  - 55-65%: Moderate signal
  - <55%: Weak signal

---

## Integration Examples

### Python
```python
import requests

def get_trading_signal(symbol, risk_tolerance="MEDIUM"):
    url = "http://127.0.0.1:8000/signal"
    payload = {
        "symbol": symbol,
        "risk_tolerance": risk_tolerance
    }
    response = requests.post(url, json=payload)
    return response.json()

# Usage
signal = get_trading_signal("AAPL", "LOW")
print(f"Action: {signal['action']}")
print(f"Reasons: {signal['reasons']}")
```

### JavaScript
```javascript
async function getTradingSignal(symbol, riskTolerance = "MEDIUM") {
  const response = await fetch("http://127.0.0.1:8000/signal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol: symbol,
      risk_tolerance: riskTolerance
    })
  });
  return await response.json();
}

// Usage
const signal = await getTradingSignal("TSLA", "HIGH");
console.log(`Action: ${signal.action}`);
```

### cURL
```bash
# Quick test
curl -X POST "http://127.0.0.1:8000/signal" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "risk_tolerance": "MEDIUM"}'
```

---

## Rate Limits & Performance

- **No rate limits** currently implemented (local deployment)
- **Response time:** ~2-5 seconds (depends on yfinance API)
- **Data freshness:** Real-time via Yahoo Finance
- **Model inference:** <10ms

---

## Error Handling Best Practices

```python
def safe_get_signal(symbol, risk_tolerance="MEDIUM"):
    try:
        response = requests.post(
            "http://127.0.0.1:8000/signal",
            json={"symbol": symbol, "risk_tolerance": risk_tolerance},
            timeout=10
        )
        
        if response.status_code != 200:
            return {"error": "API request failed"}
        
        result = response.json()
        
        if "error" in result:
            return {"error": result["error"]}
        
        return result
        
    except requests.Timeout:
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

---

## Changelog

### v2.0 (Current)
- ✅ Added `/signal` endpoint
- ✅ Risk tolerance configuration
- ✅ Multi-factor decision logic
- ✅ RSI-based refinements

### v1.0 (Previous)
- ✅ Basic `/predict/latest` endpoint
- ✅ Direction prediction only

---

## Support & Documentation

- **Interactive API Docs:** http://127.0.0.1:8000/docs
- **Alternative Docs:** http://127.0.0.1:8000/redoc
- **Source Code:** Check `app_enhanced.py`

---

**⚠️ Educational Use Only - Not Financial Advice**
