"""
m0.py — ML Phase M0: build the meta-label dataset + report base rates/baselines.

For each coin: features (causal) + triple-barrier labels, filtered to bars where the
RULE fires a bull signal (that's the meta-labeling question: "given the rule said buy,
did the trade reach TP before SL?"). Saves per-coin + combined datasets for M1, and
reports the base rate (what M1's model must beat with precision) vs buy-and-hold.

Run:  .venv/bin/python research/ml/m0.py
"""
from __future__ import annotations
import os, sys, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import config as C
from features import build_features, FEATURES
from labels import triple_barrier

HORIZON = 20                       # ~1 month of daily bars to hit TP/SL
TP, SL = C.CRYPTO_TP_PCT, C.CRYPTO_STOP_PCT
DATA = os.path.join(ROOT, "research", "data")
OUT = os.path.join(HERE, "datasets")


def rule_bull(df: pd.DataFrame) -> pd.Series:
    c = df["close"]
    ema_f, ema_s = c.ewm(span=C.EMA_FAST).mean(), c.ewm(span=C.EMA_SLOW).mean()
    d = c.diff()
    gain = d.clip(lower=0).rolling(C.RSI_PERIOD).mean()
    loss = (-d.clip(upper=0)).rolling(C.RSI_PERIOD).mean()
    rsi = 100 - 100 / (1 + gain / (loss + 1e-9))
    gap = (ema_f - ema_s).abs() / ema_s
    conf = np.minimum(1.0, 0.5 + gap * 8)
    return (ema_f > ema_s) & (rsi < C.RSI_BULL_MAX) & (conf >= C.MIN_CONFIDENCE)


def main():
    os.makedirs(OUT, exist_ok=True)
    combined = []
    print(f"M0 dataset — triple-barrier TP {TP:.0%} / SL {SL:.0%} / horizon {HORIZON}d\n")
    print(f"{'coin':10} {'rule-bull samples':>18} {'base rate (TP-first)':>22} {'buy-hold':>10}")
    for path in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        coin = os.path.basename(path).replace("-", "/").replace(".csv", "")
        df = pd.read_csv(path, parse_dates=["date"])
        feats = build_features(df)
        y = triple_barrier(df, TP, SL, HORIZON)
        bull = rule_bull(df)
        mask = bull.values & feats.notna().all(axis=1).values & ~np.isnan(y)
        X = feats[mask].copy()
        X["label"] = y[mask].astype(int)
        X["date"] = df["date"][mask].values
        X["coin"] = coin
        base = X["label"].mean() if len(X) else float("nan")
        bh = df["close"].iloc[-1] / df["close"].iloc[0] - 1
        print(f"{coin:10} {len(X):>18} {base:>21.1%} {bh:>+9.0%}")
        X.to_csv(os.path.join(OUT, os.path.basename(path)), index=False)
        combined.append(X)

    allX = pd.concat(combined, ignore_index=True)
    allX.to_csv(os.path.join(OUT, "ALL.csv"), index=False)
    print(f"\nCOMBINED: {len(allX)} samples · base rate {allX['label'].mean():.1%}")
    print(f"  → M1's model must beat ~{allX['label'].mean():.0%} precision OUT-OF-SAMPLE to add value.")

    # leakage/sanity: final features must have no NaN, and label must be 0/1 only
    assert allX[FEATURES].isna().sum().sum() == 0, "NaN in features!"
    assert set(allX["label"].unique()) <= {0, 1}, "labels must be binary"
    print("  ✅ sanity: no NaN features, binary labels. Datasets saved to research/ml/datasets/")


if __name__ == "__main__":
    main()
