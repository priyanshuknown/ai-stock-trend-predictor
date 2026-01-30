# 📈 AI Stock Trend Predictor

> An end-to-end AI-powered financial market analysis platform that predicts **next-day market direction (UP / DOWN)** with confidence scoring and historical backtesting.

Built for **education, experimentation, and portfolio demonstration** — not for live trading.

---

## 🚀 Live Demo

- **Frontend (Streamlit):** https://<your-streamlit-app-url>
- **Backend API (FastAPI):** https://<your-backend-url>
- **API Docs (Swagger):** https://<your-backend-url>/docs

---

## 🧠 What This Project Does

This project answers a simple but powerful question:

> *“Given recent market data, is tomorrow more likely to go UP or DOWN?”*

It goes beyond raw prediction by adding:
- Confidence scores
- Signal strength interpretation
- Historical backtesting accuracy
- Global market support (stocks, crypto, forex, indices)

---

## ✨ Key Features

### 🌍 Global Market Prediction
- Supports **stocks, crypto, forex, indices, commodities**
- Example symbols:
  - `AAPL` – US stock
  - `BTC-USD` – Cryptocurrency
  - `EURUSD=X` – Forex
  - `^NSEI` – Index
  - `GC=F` – Commodity

### ⚡ One-Click Prediction
- Predicts **next trading day direction**
- Outputs:
  - Direction: **UP / DOWN**
  - Confidence %
  - Signal strength: **STRONG / MODERATE / WEAK**

### 📊 Backtesting & Accuracy Dashboard
- Backtest predictions over last **N days**
- Metrics:
  - Accuracy %
  - Correct predictions
  - Total predictions
- Interpretation:
  - *Outperforms random guessing*
  - *Underperforms random guessing*

### 🧠 ML-Driven (Not Rule-Based)
- Trained **XGBoost classifier**
- Uses engineered technical indicators:
  - Moving Averages (SMA)
  - RSI
  - Volatility
  - Volume dynamics
  - Daily returns

---

## 🏗️ System Architecture

FastAPI (Backend)
├── /predict/latest → Auto market prediction
├── /predict → CSV / manual OHLCV prediction
└── /backtest → Historical accuracy evaluation

Streamlit (Frontend)
├── Global symbol input
├── Prediction dashboard
├── Backtesting UI
└── Charts & confidence visualization

ML Layer
├── Feature engineering
├── XGBoost model
└── Confidence-based signals


---

## 🧪 Machine Learning Details

### Model
- **Algorithm:** XGBoost Classifier
- **Task:** Binary classification (UP / DOWN)
- **Evaluation:** Time-based backtesting

### Feature Engineering
- OHLCV-based indicators:
  - SMA 5 / 10 / 20
  - RSI (14)
  - Volatility (rolling)
  - Volume change
  - Volume moving average
  - Daily returns

### Why Direction Instead of Price?
- Direction is more stable than price regression
- Easier to evaluate and backtest
- More suitable for risk-based decision systems

---

## 🧩 Tech Stack

| Layer | Technology |
|------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Machine Learning | XGBoost |
| Market Data | Yahoo Finance |
| Visualization | Matplotlib |
| Deployment | Railway, Streamlit Cloud |
| Language | Python |

---

## 📦 Project Structure
ai-stock-trend-predictor/
│
├── app.py # FastAPI backend
├── streamlit_app.py # Streamlit frontend
├── model/
│ └── xgb_model.json # Trained ML model
├── utils/
│ └── feature_engineering.py # Feature engineering logic
│
├── API_DOCUMENTATION.md
├── IMPLEMENTATION_GUIDE.md
├── POSITION_SIZING_DOCS.md
├── BEFORE_AFTER_COMPARISON.md
│
├── requirements.txt
├── requirements_streamlit.txt
└── Quick_start.md


---

## ▶️ Run Locally

### 1️⃣ Clone Repository
```bash
git clone https://github.com/priyanshuknown/ai-stock-trend-predictor.git
cd ai-stock-trend-predictor


python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements_streamlit.txt

uvicorn app:app --reload
streamlit run streamlit_app.py

⚠️ Disclaimer

This project is for educational and research purposes only.
It is NOT financial advice and should NOT be used for live trading.

Financial markets are risky. This project focuses on learning ML systems, not profit guarantees.

🚀 Planned Enhancements

📐 Position sizing recommendations

🛑 Stop-loss & take-profit calculation

📬 Alerts & watchlists

📊 Confidence calibration analysis

🗳️ Model ensemble (XGBoost + RF + LightGBM)

💼 Portfolio simulation

simulation

👤 Author

Priyansh Chaudhary
Aspiring ML / Data Engineer
Focused on building real-world, end-to-end AI systems

🔗 GitHub: https://github.com/priyanshuknown

⭐ Why This Project Matters

This is not just a model.

It demonstrates:

Machine learning understanding

Feature engineering

API design

Frontend integration

Backtesting & evaluation

Deployment & product thinking

If you like this project, ⭐ star the repository!



---

If you want next, I can:
- Create a **landing page prompt for Lovable**
- Write a **LinkedIn launch post**
- Prepare **interview explanation notes**
- Add **architecture diagram**

Just tell me 🚀




