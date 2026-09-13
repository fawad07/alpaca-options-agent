"""
features.py — causal feature engineering for the ML phase (M0).

Every feature at bar t uses ONLY data up to t (rolling/ewm/pct_change are causal),
so there's no lookahead. Kept deliberately small (~13 features) — on ~2k daily bars
per coin, more features = more overfitting.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

FEATURES = [
    "ema_ratio", "rsi", "bb_z", "atr_pct", "ret_5", "ret_10", "ret_20",
    "mom_60", "vol_20", "dist_hi_20", "dist_lo_20", "vol_z", "trend_strength",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
    ema_f, ema_s = c.ewm(span=20).mean(), c.ewm(span=50).mean()
    d = c.diff()
    gain = d.clip(lower=0).rolling(14).mean()
    loss = (-d.clip(upper=0)).rolling(14).mean()
    rsi = 100 - 100 / (1 + gain / (loss + 1e-9))
    sma20, std20 = c.rolling(20).mean(), c.rolling(20).std()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    ret1 = c.pct_change()

    f = pd.DataFrame(index=df.index)
    f["ema_ratio"]     = ema_f / ema_s - 1                 # trend direction/strength
    f["rsi"]           = rsi / 100                         # momentum (0..1)
    f["bb_z"]          = (c - sma20) / (std20 + 1e-9)      # mean-reversion
    f["atr_pct"]       = atr / c                           # volatility
    f["ret_5"]         = c.pct_change(5)
    f["ret_10"]        = c.pct_change(10)
    f["ret_20"]        = c.pct_change(20)
    f["mom_60"]        = c.pct_change(60)                  # longer momentum
    f["vol_20"]        = ret1.rolling(20).std()            # realized vol
    f["dist_hi_20"]    = c / c.rolling(20).max() - 1       # how far below recent high
    f["dist_lo_20"]    = c / c.rolling(20).min() - 1       # how far above recent low
    f["vol_z"]         = (v - v.rolling(20).mean()) / (v.rolling(20).std() + 1e-9)
    f["trend_strength"] = (ema_f / ema_s - 1).abs()        # regime: trend vs chop
    return f[FEATURES]
