"""
labels.py — triple-barrier labeling for the ML phase (M0).

For a long entry at bar t (fill at close[t]), look forward up to `horizon` bars:
  • +tp hit first  → label 1 (the trade would have won / reached take-profit)
  • −sl hit first  → label 0
  • neither in horizon (timeout) → label 0 (didn't reach TP)
Bars without a full `horizon` ahead get NaN (incomplete → excluded from training).

This labels the exact outcome we trade (our TP/SL structure), which is what
meta-labeling needs: "given the rule fired, would the trade have hit TP first?"
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def triple_barrier(df: pd.DataFrame, tp: float, sl: float, horizon: int) -> np.ndarray:
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    y = np.full(n, np.nan)
    for i in range(n):
        if i + horizon > n - 1:            # not enough forward data → leave NaN
            continue
        entry = c[i]
        up, dn = entry * (1 + tp), entry * (1 - sl)
        label = 0                          # default: timeout = didn't reach TP
        for j in range(i + 1, i + horizon + 1):
            if l[j] <= dn:
                label = 0; break           # stop hit first
            if h[j] >= up:
                label = 1; break           # take-profit hit first
        y[i] = label
    return y
