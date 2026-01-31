API_URL = "https://ai-stock-trend-predictor-production.up.railway.app"  

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def confidence_signal(confidence: float):
    if confidence >= 0.75:
        return "🔥 STRONG"
    elif confidence >= 0.6:
        return "⚠️ MODERATE"
    else:
        return "❄️ WEAK"


def detect_asset_type(symbol: str):
    symbol = symbol.upper().strip()
    if symbol.endswith("-USD"):
        return "Crypto"
    elif symbol.endswith("=X"):
        return "Forex"
    elif symbol.startswith("^"):
        return "Index"
    elif symbol.endswith("=F"):
        return "Commodity"
    elif symbol.endswith(".NS") or symbol.endswith(".BO"):
        return "Indian Stock"
    else:
        return "Stock"


def action_color(action: str):
    """Return color and emoji for trading action"""
    colors = {
        "BUY": ("🟢", "#28a745", "success"),
        "HOLD": ("🟡", "#ffc107", "warning"),
        "AVOID": ("🔴", "#dc3545", "error")
    }
    return colors.get(action, ("⚪", "#6c757d", "info"))


def risk_badge(risk_level: str):
    """Return formatted risk badge"""
    badges = {
        "LOW": "🟢 LOW RISK",
        "MEDIUM": "🟡 MEDIUM RISK",
        "HIGH": "🔴 HIGH RISK"
    }
    return badges.get(risk_level, risk_level)


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Stock Trend Predictor", layout="wide")

st.title("📈 AI Stock Trend Predictor")
st.caption("Educational market analysis with actionable trading signals")

API_PREDICT = "http://127.0.0.1:8000/predict"
API_LATEST = "http://127.0.0.1:8000/predict/latest"
API_BACKTEST = "http://127.0.0.1:8000/backtest"
API_SIGNAL = "http://127.0.0.1:8000/signal"

# --------------------------------------------------
# 🎯 TRADING SIGNAL (PRIMARY FEATURE)
# --------------------------------------------------
st.header("🎯 Get Trading Signal")

col1, col2 = st.columns([2, 1])

with col1:
    symbol = st.text_input(
        "Enter market symbol",
        value="AAPL",
        help="Examples: AAPL, BTC-USD, EURUSD=X, ^NSEI, GC=F"
    )
    asset_type = detect_asset_type(symbol)
    st.caption(f"Detected Asset Type: **{asset_type}**")

with col2:
    risk_tolerance = st.selectbox(
        "Your Risk Tolerance",
        options=["LOW", "MEDIUM", "HIGH"],
        index=1,
        help="LOW: Conservative (75%+ confidence required)\nMEDIUM: Balanced (65%+)\nHIGH: Aggressive (55%+)"
    )

# Portfolio size input
portfolio_size = st.number_input(
    "💰 Total Portfolio Size (USD)",
    min_value=100.0,
    max_value=10000000.0,
    value=10000.0,
    step=1000.0,
    help="Enter your total portfolio value to calculate position sizing"
)

if st.button("🚀 Generate Trading Signal", key="get_signal", type="primary"):
    with st.spinner("Analyzing market data..."):
        response = requests.post(
            API_SIGNAL,
            json={
                "symbol": symbol,
                "risk_tolerance": risk_tolerance,
                "portfolio_size": portfolio_size
            }
        )

    if response.status_code != 200:
        st.error("API Error")
        st.code(response.text)
    else:
        result = response.json()
        
        if "error" in result:
            st.error(result["error"])
        else:
            action = result["action"]
            emoji, color, status = action_color(action)
            
            # Main signal display
            st.markdown("---")
            
            # Big action card
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown(
                    f"""
                    <div style='text-align: center; padding: 30px; 
                         background: linear-gradient(135deg, {color}22 0%, {color}11 100%); 
                         border-radius: 15px; border: 2px solid {color};'>
                        <h1 style='margin: 0; font-size: 4em;'>{emoji}</h1>
                        <h2 style='margin: 10px 0; color: {color};'>{action}</h2>
                        <p style='margin: 0; font-size: 1.2em; color: #666;'>{symbol.upper()}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("---")
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Confidence",
                    f"{result['confidence'] * 100:.1f}%",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Direction",
                    result['direction'],
                    delta=None
                )
            
            with col3:
                st.metric(
                    "Risk Level",
                    risk_badge(result['risk_level']),
                    delta=None
                )
            
            with col4:
                rsi = result['technical_data']['rsi']
                rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                st.metric(
                    "RSI",
                    f"{rsi:.1f}",
                    delta=rsi_status
                )
            
            # Reasoning section
            st.subheader("📋 Analysis & Reasoning")
            
            for i, reason in enumerate(result['reasons'], 1):
                st.markdown(f"**{i}.** {reason}")
            
            # Position Sizing Section
            st.markdown("---")
            st.subheader("💰 Position Sizing Recommendation")
            
            pos = result['position_sizing']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Recommended Position",
                    f"${pos['recommended_dollar']:,.2f}",
                    delta=f"{pos['recommended_pct']:.2%} of portfolio"
                )
            
            with col2:
                st.metric(
                    "Kelly Criterion",
                    f"{pos['kelly_criterion_pct']:.2%}",
                    delta="Scientific allocation"
                )
            
            with col3:
                st.metric(
                    "Max Position",
                    f"{pos['max_position_pct']:.1%}",
                    delta=f"{risk_tolerance} risk limit"
                )
            
            with st.expander("📊 Position Sizing Details"):
                st.write("**Calculation Reasoning:**")
                for reason in pos['reasoning']:
                    st.write(f"• {reason}")
            
            # Exit Levels Section (only show for BUY signals)
            if action == "BUY":
                st.markdown("---")
                st.subheader("🎯 Exit Levels & Risk Management")
                
                exits = result['exit_levels']
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Entry Price",
                        f"${exits['entry_price']:,.2f}",
                        delta="Current"
                    )
                
                with col2:
                    st.metric(
                        "Stop Loss",
                        f"${exits['stop_loss']:,.2f}",
                        delta=f"-{exits['stop_loss_pct']:.1f}%",
                        delta_color="inverse"
                    )
                
                with col3:
                    st.metric(
                        "Take Profit 1",
                        f"${exits['take_profit_1']:,.2f}",
                        delta=f"+{((exits['take_profit_1']/exits['entry_price']-1)*100):.1f}%"
                    )
                
                with col4:
                    st.metric(
                        "Take Profit 2",
                        f"${exits['take_profit_2']:,.2f}",
                        delta=f"+{((exits['take_profit_2']/exits['entry_price']-1)*100):.1f}%"
                    )
                
                # Risk/Reward ratio
                st.info(f"**Risk/Reward Ratio:** {exits['risk_reward_ratio']} (ATR-based)")
                
                # Trade Setup Summary
                with st.expander("📝 Complete Trade Setup"):
                    st.markdown(f"""
                    **Entry:** ${exits['entry_price']:,.2f}
                    
                    **Position Size:** ${pos['recommended_dollar']:,.2f} ({pos['recommended_pct']:.2%})
                    
                    **Stop Loss:** ${exits['stop_loss']:,.2f} ({exits['stop_loss_pct']:.1f}% risk)
                    
                    **Take Profit Targets:**
                    - TP1 (50% position): ${exits['take_profit_1']:,.2f}
                    - TP2 (remaining 50%): ${exits['take_profit_2']:,.2f}
                    
                    **Maximum Risk:** ${pos['recommended_dollar'] * exits['stop_loss_pct'] / 100:,.2f}
                    
                    **Risk/Reward:** {exits['risk_reward_ratio']}
                    """)
            
            # Technical details (collapsible)
            with st.expander("🔍 Technical Data"):
                tech = result['technical_data']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Recent Close:** ${tech['recent_close']:,.2f}")
                    st.write(f"**RSI (14):** {tech['rsi']:.2f} ({tech['rsi_status']})")
                
                with col2:
                    st.write(f"**Volatility:** {tech['volatility']:.2%}")
                    st.write(f"**Risk Tolerance:** {result['risk_tolerance']}")
            
            # Disclaimer
            st.info("⚠️ **Educational Purpose Only** - This is not financial advice. Always do your own research and consult with a financial advisor.")

st.markdown("---")

# --------------------------------------------------
# 🌍 QUICK PREDICTION (LIGHTWEIGHT)
# --------------------------------------------------
with st.expander("🌍 Quick Direction Prediction (No Signal)"):
    st.caption("Get raw model prediction without trading signal logic")
    
    if st.button("🔮 Predict Direction Only", key="auto_predict"):
        with st.spinner("Fetching market data..."):
            response = requests.post(API_LATEST, params={"symbol": symbol})

        if response.status_code != 200:
            st.error("API Error")
            st.code(response.text)
        else:
            result = response.json()
            confidence = float(result["confidence"])
            signal = confidence_signal(confidence)

            st.success(f"Prediction for **{symbol.upper()}**")
            st.markdown(f"### Direction: **{result['direction']}**")
            st.progress(confidence)

            col1, col2 = st.columns(2)
            col1.metric("Confidence %", f"{confidence * 100:.2f}%")
            col2.metric("Signal", signal)

# --------------------------------------------------
# 📊 BACKTESTING & ACCURACY
# --------------------------------------------------
st.header("📊 Model Performance & Backtesting")

col1, col2 = st.columns([3, 1])

with col1:
    lookback_days = st.slider(
        "Backtest last N days",
        min_value=10,
        max_value=120,
        value=30,
        step=5
    )

with col2:
    st.write("")
    st.write("")
    run_backtest = st.button("🧪 Run Backtest", key="run_backtest")

if run_backtest:
    with st.spinner("Running backtest..."):
        response = requests.post(
            API_BACKTEST,
            json={
                "symbol": symbol,
                "lookback_days": lookback_days
            }
        )

    if response.status_code != 200:
        st.error("Backtest API error")
        st.code(response.text)
    else:
        result = response.json()

        if "error" in result:
            st.error(result["error"])
        else:
            accuracy = result["accuracy"]
            correct = result["correct_predictions"]
            total = result["total_predictions"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Accuracy", f"{accuracy * 100:.2f}%")
            col2.metric("Correct", correct)
            col3.metric("Total", total)

            st.progress(min(accuracy, 1.0))

            if accuracy >= 0.6:
                st.success("✅ Model performs better than random.")
            elif accuracy >= 0.5:
                st.warning("⚠️ Slight edge over random.")
            else:
                st.error("❌ Underperforms random guessing.")

# --------------------------------------------------
# 📅 MULTI-DAY FORECAST
# --------------------------------------------------
st.header("📅 Multi-Day Trend Forecast")

col1, col2 = st.columns([3, 1])

with col1:
    forecast_days = st.slider("Forecast next N days", 2, 5, 3)

with col2:
    st.write("")
    st.write("")
    run_forecast = st.button("🔮 Forecast Trend", key="forecast")

if run_forecast:
    with st.spinner("Running multi-day forecast..."):
        response = requests.post(
            "http://127.0.0.1:8000/predict/multi",
            json={
                "symbol": symbol,
                "days": forecast_days
            }
        )

    if response.status_code != 200:
        st.error("API Error")
    else:
        result = response.json()

        st.subheader(f"Overall Trend: **{result['overall_trend']}**")

        for p in result["predictions"]:
            direction_emoji = "🟢" if p['direction'] == "UP" else "🔴"
            st.write(
                f"{direction_emoji} **Day +{p['day']}** → "
                f"{p['direction']} "
                f"(confidence: {p['confidence']:.2%})"
            )

# --------------------------------------------------
# 📂 ADVANCED: CSV UPLOAD & MANUAL INPUT
# --------------------------------------------------
with st.expander("📂 Advanced: Upload CSV or Manual Input"):
    
    # LOAD BASE DATA
    @st.cache_data
    def load_base_data(sym):
        df = yf.download(sym, period="3mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.reset_index()
        return df[["Open", "High", "Low", "Close", "Volume"]]

    if "df" not in st.session_state:
        st.session_state.df = load_base_data(symbol)

    df = st.session_state.df

    # CSV UPLOAD
    st.subheader("📂 Upload OHLCV CSV")

    uploaded_file = st.file_uploader(
        "Upload CSV with columns: Open, High, Low, Close, Volume",
        type=["csv"]
    )

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
        st.success("CSV loaded successfully")

    # MANUAL INPUT
    st.subheader("✏️ Manual Input (Latest Candle)")

    with st.form("manual_input"):
        open_p = st.number_input("Open", value=150.0)
        high_p = st.number_input("High", value=152.0)
        low_p = st.number_input("Low", value=149.0)
        close_p = st.number_input("Close", value=151.0)
        volume = st.number_input("Volume", value=50_000_000, step=100_000)

        submitted = st.form_submit_button("Add Candle")

        if submitted:
            new_row = {
                "Open": open_p,
                "High": high_p,
                "Low": low_p,
                "Close": close_p,
                "Volume": volume,
            }
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            df = st.session_state.df
            st.success("Candle added")

    # MANUAL / CSV PREDICTION
    if df is not None and len(df) >= 25:
        st.subheader("🔮 Model Prediction (CSV / Manual)")

        if st.button("Predict Next Day Direction", key="manual_predict"):
            payload = {
                "data": df[["Open", "High", "Low", "Close", "Volume"]]
                .tail(60)
                .to_dict(orient="records")
            }

            with st.spinner("Running model prediction..."):
                response = requests.post(API_PREDICT, json=payload)

            if response.status_code != 200:
                st.error("API Error")
                st.code(response.text)
            else:
                result = response.json()
                confidence = float(result["probability_up"])
                signal = confidence_signal(confidence)

                st.markdown(f"### Direction: **{result['prediction']}**")
                st.progress(confidence)

                col1, col2 = st.columns(2)
                col1.metric("Confidence %", f"{confidence * 100:.2f}%")
                col2.metric("Signal", signal)

    else:
        st.info("Upload or enter at least **25 rows** to enable prediction.")

    # PRICE CHART
    st.subheader("📊 Recent Close Price")
    fig, ax = plt.subplots()
    ax.plot(df["Close"].tail(60))
    ax.set_xlabel("Time")
    ax.set_ylabel("Close Price")
    st.pyplot(fig)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption("Built with XGBoost • FastAPI • Streamlit | Educational purposes only")
