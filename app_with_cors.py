import yfinance as yf
import pandas as pd

from fastapi import FastAPI
from pydantic import BaseModel
from xgboost import XGBClassifier

from utils.feature_engineering import compute_features


# --------------------------------------------------
# APP INIT
# --------------------------------------------------
app = FastAPI(title="Stock Trend Prediction API")


# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
FEATURE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "SMA_5",
    "SMA_10",
    "SMA_20",
    "Daily_Return",
    "RSI_14",
    "Volatility_10",
    "Volume_Change",
    "Volume_SMA_10",
]


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------
model = XGBClassifier()
model.load_model("model/xgb_model.json")


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------
class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    lookback_days: int = 30


class MultiPredictRequest(BaseModel):
    symbol: str = "AAPL"
    days: int = 3


class SignalRequest(BaseModel):
    symbol: str = "AAPL"
    risk_tolerance: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    portfolio_size: float = 10000.0  # Total portfolio value in USD


# --------------------------------------------------
# SIGNAL GENERATION LOGIC
# --------------------------------------------------
def calculate_position_size(
    confidence: float,
    risk_level: str,
    portfolio_size: float,
    risk_tolerance: str
):
    """
    Calculate recommended position size using Kelly Criterion and risk-based allocation
    
    Returns: dict with position_pct, position_dollar, kelly_pct, reasoning
    """
    
    # Base allocation by risk tolerance (% of portfolio)
    base_allocations = {
        "LOW": 0.05,      # 5% max per position
        "MEDIUM": 0.10,   # 10% max per position
        "HIGH": 0.15      # 15% max per position
    }
    
    max_position_pct = base_allocations.get(risk_tolerance, 0.10)
    
    # Kelly Criterion: f = (bp - q) / b
    # Simplified: f = confidence - (1 - confidence) = 2*confidence - 1
    # But we'll use conservative Kelly (half Kelly for safety)
    win_rate = confidence
    kelly_fraction = max(0, 2 * win_rate - 1)  # Full Kelly
    kelly_conservative = kelly_fraction * 0.5  # Half Kelly (safer)
    
    # Adjust for risk level (reduce position if high volatility)
    risk_multipliers = {
        "LOW": 1.0,      # Full position
        "MEDIUM": 0.8,   # 80% of calculated
        "HIGH": 0.6      # 60% of calculated (reduce due to volatility)
    }
    
    risk_multiplier = risk_multipliers.get(risk_level, 0.8)
    
    # Calculate final position size
    # Use minimum of: Kelly, max_position, and confidence-based allocation
    confidence_based = confidence * max_position_pct
    
    recommended_pct = min(
        kelly_conservative,
        max_position_pct,
        confidence_based
    ) * risk_multiplier
    
    # Floor at 0.5% (minimum viable position)
    recommended_pct = max(0.005, recommended_pct)
    
    # Cap at max allocation
    recommended_pct = min(recommended_pct, max_position_pct)
    
    position_dollar = portfolio_size * recommended_pct
    
    # Generate reasoning
    reasoning = []
    reasoning.append(f"Base allocation for {risk_tolerance.lower()} risk: {max_position_pct:.1%}")
    reasoning.append(f"Kelly Criterion suggests: {kelly_conservative:.1%}")
    reasoning.append(f"Adjusted for {risk_level.lower()} volatility: {risk_multiplier:.0%} multiplier")
    
    if recommended_pct == 0.005:
        reasoning.append("⚠️ Position very small due to low confidence or high risk")
    elif recommended_pct >= max_position_pct:
        reasoning.append(f"✅ Maximum position reached ({max_position_pct:.1%})")
    
    return {
        "position_pct": round(recommended_pct, 4),
        "position_dollar": round(position_dollar, 2),
        "kelly_pct": round(kelly_conservative, 4),
        "max_position_pct": max_position_pct,
        "reasoning": reasoning
    }


def calculate_stop_loss_take_profit(
    current_price: float,
    volatility: float,
    confidence: float,
    direction: str
):
    """
    Calculate stop-loss and take-profit levels based on ATR (volatility proxy)
    
    ATR-based stops: Stop at 2x volatility below entry
    Take-profit: 2:1 or 3:1 risk-reward ratio
    """
    
    # Use volatility as ATR proxy (10-day volatility)
    # Stop-loss: 2x volatility
    stop_distance_pct = volatility * 2.0
    
    # Take profit distance based on confidence
    # Higher confidence = larger profit target
    if confidence >= 0.75:
        tp_multiplier = 3.0  # 3:1 risk-reward
    elif confidence >= 0.65:
        tp_multiplier = 2.5  # 2.5:1 risk-reward
    else:
        tp_multiplier = 2.0  # 2:1 risk-reward
    
    tp_distance_pct = stop_distance_pct * tp_multiplier
    
    if direction == "UP":
        stop_loss = current_price * (1 - stop_distance_pct)
        take_profit_1 = current_price * (1 + stop_distance_pct * 2.0)
        take_profit_2 = current_price * (1 + tp_distance_pct)
    else:
        # For short positions (AVOID signals)
        stop_loss = current_price * (1 + stop_distance_pct)
        take_profit_1 = current_price * (1 - stop_distance_pct * 2.0)
        take_profit_2 = current_price * (1 - tp_distance_pct)
    
    risk_reward = tp_multiplier
    
    return {
        "entry_price": round(current_price, 2),
        "stop_loss": round(stop_loss, 2),
        "stop_loss_pct": round(stop_distance_pct * 100, 2),
        "take_profit_1": round(take_profit_1, 2),
        "take_profit_2": round(take_profit_2, 2),
        "risk_reward_ratio": f"1:{risk_reward:.1f}",
        "atr_proxy": round(volatility, 4)
    }


def generate_trading_signal(
    direction: str,
    confidence: float,
    volatility: float,
    rsi: float,
    risk_tolerance: str = "MEDIUM"
):
    """
    Generate actionable trading signal based on:
    - Prediction direction & confidence
    - Market volatility (risk)
    - RSI (overbought/oversold conditions)
    - User risk tolerance
    
    Returns: action, reason, risk_level
    """
    
    # Define confidence thresholds based on risk tolerance
    confidence_thresholds = {
        "LOW": 0.75,      # Very conservative
        "MEDIUM": 0.65,   # Balanced
        "HIGH": 0.55      # Aggressive
    }
    
    threshold = confidence_thresholds.get(risk_tolerance, 0.65)
    
    # Determine risk level based on volatility
    if volatility > 0.03:
        risk_level = "HIGH"
    elif volatility > 0.015:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # RSI analysis
    rsi_status = "NEUTRAL"
    if rsi > 70:
        rsi_status = "OVERBOUGHT"
    elif rsi < 30:
        rsi_status = "OVERSOLD"
    
    # Decision logic
    reasons = []
    
    # Rule 1: High confidence predictions
    if confidence >= threshold and direction == "UP":
        if rsi_status == "OVERBOUGHT":
            action = "HOLD"
            reasons.append(f"Strong upward signal ({confidence:.1%} confidence)")
            reasons.append(f"But RSI shows overbought conditions ({rsi:.1f})")
            reasons.append("Waiting for pullback recommended")
        else:
            action = "BUY"
            reasons.append(f"Strong upward prediction ({confidence:.1%} confidence)")
            if rsi_status == "OVERSOLD":
                reasons.append(f"RSI oversold ({rsi:.1f}) - good entry point")
            if risk_level == "LOW":
                reasons.append("Low volatility environment")
    
    elif confidence >= threshold and direction == "DOWN":
        action = "AVOID"
        reasons.append(f"High confidence downward trend ({confidence:.1%})")
        if rsi_status == "OVERBOUGHT":
            reasons.append(f"RSI confirms overbought ({rsi:.1f})")
        if risk_level == "HIGH":
            reasons.append(f"High volatility increases risk")
    
    # Rule 2: Medium confidence
    elif 0.5 <= confidence < threshold:
        action = "HOLD"
        reasons.append(f"Moderate confidence ({confidence:.1%})")
        reasons.append(f"Below {threshold:.0%} threshold for {risk_tolerance.lower()} risk tolerance")
        reasons.append("Wait for stronger signal")
    
    # Rule 3: Low confidence or unclear
    else:
        action = "HOLD"
        reasons.append("Weak or unclear signal")
        reasons.append(f"Confidence only {confidence:.1%}")
        reasons.append("Insufficient edge to act")
    
    # Special override: Very high volatility + downtrend
    if risk_level == "HIGH" and direction == "DOWN" and risk_tolerance == "LOW":
        action = "AVOID"
        reasons = [
            "High risk environment detected",
            f"Volatility: {volatility:.2%}",
            "Downward trend prediction",
            "Conservative approach recommended"
        ]
    
    return {
        "action": action,
        "reasons": reasons,
        "risk_level": risk_level,
        "rsi_status": rsi_status
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------
@app.get("/")
def root():
    return {"status": "API is running"}


# --------------------------------------------------
# LATEST PREDICTION (AUTO DATA)
# --------------------------------------------------
@app.post("/predict/latest")
def predict_latest(symbol: str = "AAPL"):
    try:
        # 1. Download data
        df = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if df.empty:
            return {"error": "Invalid symbol or no data available"}

        # 2. Flatten columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df.reset_index()
        df = df[["Open", "High", "Low", "Close", "Volume"]]

        # 3. Feature engineering
        features_df = compute_features(df)

        if len(features_df) < 1:
            return {"error": "Not enough data to compute indicators"}

        # 4. Select latest row
        latest_features = features_df[FEATURE_COLUMNS].iloc[[-1]]

        # 5. Predict
        proba = model.predict_proba(
            latest_features,
            validate_features=False
        )[0][1]

        direction = "UP" if proba >= 0.5 else "DOWN"

        return {
            "symbol": symbol.upper(),
            "direction": direction,
            "confidence": round(float(proba), 4)
        }

    except Exception as e:
        return {"error": str(e)}


# --------------------------------------------------
# 🆕 TRADING SIGNAL ENDPOINT
# --------------------------------------------------
@app.post("/signal")
def get_trading_signal(payload: SignalRequest):
    """
    Generate actionable trading signal with risk assessment, position sizing, and exit levels
    
    Returns:
    - action: BUY / HOLD / AVOID
    - confidence: Model confidence (0-1)
    - risk_level: LOW / MEDIUM / HIGH
    - reasons: List of factors influencing decision
    - technical_data: RSI, volatility, etc.
    - position_sizing: Recommended allocation and Kelly Criterion
    - exit_levels: Stop-loss and take-profit prices
    """
    symbol = payload.symbol.upper()
    risk_tolerance = payload.risk_tolerance.upper()
    portfolio_size = payload.portfolio_size
    
    if risk_tolerance not in ["LOW", "MEDIUM", "HIGH"]:
        risk_tolerance = "MEDIUM"
    
    try:
        # 1. Download data
        df = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if df.empty:
            return {"error": "Invalid symbol or no data available"}

        # 2. Flatten columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df.reset_index()
        df = df[["Open", "High", "Low", "Close", "Volume"]]

        # 3. Feature engineering
        features_df = compute_features(df)

        if len(features_df) < 1:
            return {"error": "Not enough data to compute indicators"}

        # 4. Get latest features
        latest_row = features_df.iloc[-1]
        latest_features = features_df[FEATURE_COLUMNS].iloc[[-1]]

        # 5. Predict
        proba = model.predict_proba(
            latest_features,
            validate_features=False
        )[0][1]

        direction = "UP" if proba >= 0.5 else "DOWN"
        
        # 6. Extract technical indicators
        volatility = float(latest_row["Volatility_10"])
        rsi = float(latest_row["RSI_14"])
        current_price = float(latest_row["Close"])
        
        # 7. Generate trading signal
        signal = generate_trading_signal(
            direction=direction,
            confidence=float(proba),
            volatility=volatility,
            rsi=rsi,
            risk_tolerance=risk_tolerance
        )
        
        # 8. Calculate position sizing
        position_sizing = calculate_position_size(
            confidence=float(proba),
            risk_level=signal["risk_level"],
            portfolio_size=portfolio_size,
            risk_tolerance=risk_tolerance
        )
        
        # 9. Calculate stop-loss and take-profit
        exit_levels = calculate_stop_loss_take_profit(
            current_price=current_price,
            volatility=volatility,
            confidence=float(proba),
            direction=direction
        )
        
        return {
            "symbol": symbol,
            "action": signal["action"],
            "confidence": round(float(proba), 4),
            "direction": direction,
            "risk_level": signal["risk_level"],
            "reasons": signal["reasons"],
            "technical_data": {
                "rsi": round(rsi, 2),
                "rsi_status": signal["rsi_status"],
                "volatility": round(volatility, 4),
                "recent_close": round(current_price, 2)
            },
            "position_sizing": {
                "recommended_pct": position_sizing["position_pct"],
                "recommended_dollar": position_sizing["position_dollar"],
                "kelly_criterion_pct": position_sizing["kelly_pct"],
                "max_position_pct": position_sizing["max_position_pct"],
                "reasoning": position_sizing["reasoning"]
            },
            "exit_levels": exit_levels,
            "risk_tolerance": risk_tolerance,
            "portfolio_size": portfolio_size
        }

    except Exception as e:
        return {"error": str(e)}


# --------------------------------------------------
# BACKTEST API
# --------------------------------------------------
@app.post("/backtest")
def run_backtest(payload: BacktestRequest):
    symbol = payload.symbol.upper()
    lookback_days = payload.lookback_days

    # 1. Download historical data
    df = yf.download(
        symbol,
        period="6mo",
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        return {"error": "No data found for symbol"}

    # 2. Flatten columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.reset_index()
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # 3. Feature engineering
    features_df = compute_features(df)

    # CREATE TARGET (NEXT-DAY DIRECTION)
    features_df["Target"] = (
        features_df["Close"].shift(-1) > features_df["Close"]
    ).astype(int)

    features_df = features_df.dropna()

    if len(features_df) < lookback_days + 1:
        return {"error": "Not enough data for backtesting"}

    # 4. Backtest loop
    correct = 0
    total = 0

    for i in range(-lookback_days, -1):
        X_test = features_df.iloc[:i][FEATURE_COLUMNS].iloc[[-1]]
        actual = int(features_df.iloc[i]["Target"])

        proba = model.predict_proba(
            X_test,
            validate_features=False
        )[0][1]

        pred = 1 if proba >= 0.5 else 0

        if pred == actual:
            correct += 1

        total += 1

    accuracy = round(correct / total, 4)

    return {
        "symbol": symbol,
        "lookback_days": lookback_days,
        "accuracy": accuracy,
        "total_predictions": total,
        "correct_predictions": correct
    }


# --------------------------------------------------
# MULTI-DAY PREDICTION
# --------------------------------------------------
@app.post("/predict/multi")
def predict_multi(payload: MultiPredictRequest):
    symbol = payload.symbol.upper()
    days = min(payload.days, 5)  # safety cap

    df = yf.download(symbol, period="6mo", interval="1d", progress=False)

    if df.empty:
        return {"error": "No data for symbol"}

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.reset_index()
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    predictions = []

    for i in range(days):
        features_df = compute_features(df)

        if len(features_df) < 25:
            break

        latest = features_df[FEATURE_COLUMNS].iloc[[-1]]

        proba = model.predict_proba(
            latest,
            validate_features=False
        )[0][1]

        direction = "UP" if proba >= 0.5 else "DOWN"

        predictions.append({
            "day": i + 1,
            "direction": direction,
            "confidence": round(float(proba), 4)
        })

        # extend window with last candle (NO price hallucination)
        df = df.iloc[1:].reset_index(drop=True)

    ups = sum(p["direction"] == "UP" for p in predictions)
    overall = "UP" if ups >= len(predictions) / 2 else "DOWN"

    return {
        "symbol": symbol,
        "days": days,
        "predictions": predictions,
        "overall_trend": overall
    }
