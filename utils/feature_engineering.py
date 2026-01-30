import pandas as pd
import numpy as np

def compute_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    df must contain:
    ['Open', 'High', 'Low', 'Close', 'Volume']
    ordered by time ASC
    """

    df = df.copy()

    # Moving averages
    df["SMA_5"] = df["Close"].rolling(5).mean()
    df["SMA_10"] = df["Close"].rolling(10).mean()
    df["SMA_20"] = df["Close"].rolling(20).mean()

    # Daily return
    df["Daily_Return"] = df["Close"].pct_change()

    # RSI
    df["RSI_14"] = compute_rsi(df["Close"], 14)

    # Volatility
    df["Volatility_10"] = df["Daily_Return"].rolling(10).std()

    # Volume features
    df["Volume_Change"] = df["Volume"].pct_change()
    df["Volume_SMA_10"] = df["Volume"].rolling(10).mean()

    df = df.dropna()

    return df
