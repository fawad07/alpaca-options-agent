"""
backtest_signal.py — honesty check on the underlying directional signal.
Reused from ai-trading-pipeline's out-of-sample discipline.

Options P&L is more complex than the underlying, but the agent's edge (if any)
comes entirely from the DIRECTIONAL call. So we sanity-check that call as a
long/short position on the underlying, out-of-sample: settings-free rules,
tested on data since 2023, vs buy-and-hold and vs random timing.

This gives the write-up an honest "does the signal actually work?" section —
the thing that separates a credible agent from a curve-fit demo.

Run:  python3 backtest_signal.py
"""
from __future__ import annotations
import numpy as np, pandas as pd
import config as C, data as D
from signals import add_features

SPLIT = pd.Timestamp('2023-01-01')
FEE = 0.0005          # small per-flip cost proxy for the underlying
SEEDS = 30


def positions(df: pd.DataFrame) -> pd.Series:
    f = add_features(df)
    up = f['EMA_fast'] > f['EMA_slow']
    bull = up & (f['RSI'] < C.RSI_BULL_MAX)
    bear = (~up) & (f['RSI'] > C.RSI_BEAR_MIN)
    pos = pd.Series(0.0, index=df.index)
    pos[bull] = 1.0
    pos[bear] = -1.0          # bear = puts = short exposure
    return pos.shift(1).fillna(0)


def equity(close, pos):
    ret = close.pct_change().fillna(0)
    net = pos * ret - (pos.diff().abs() > 0) * FEE
    return float((1 + net).prod()) - 1


def shuffled(close, pos):
    ret = close.pct_change().fillna(0).values
    base = pos.values.copy()
    out = []
    for s in range(SEEDS):
        rng = np.random.default_rng(s)
        sh = rng.permutation(base)
        net = sh * ret - (np.abs(np.diff(sh, prepend=0)) > 0) * FEE
        out.append(float(np.prod(1 + net)) - 1)
    return float(np.median(out))


if __name__ == '__main__':
    print("=" * 66)
    print("  SIGNAL HONESTY CHECK — out-of-sample (2023 → now)")
    print("=" * 66)
    print(f"  {'Sym':6}{'Signal':>10}{'BuyHold':>10}{'Random':>10}   Verdict")
    beat = 0; total = 0
    for sym in C.UNIVERSE:
        df = D.fetch_daily(sym, rng='5y')
        if df.empty or len(df) < 300:
            print(f"  {sym:6} not enough data"); continue
        exam = df[df.index >= SPLIT]
        pos = positions(df).loc[exam.index]
        s = equity(exam['close'], pos)
        bh = float(exam['close'].iloc[-1] / exam['close'].iloc[0] - 1)
        rnd = shuffled(exam['close'], pos)
        ok = s > 0 and s > rnd and s > bh
        beat += 1 if ok else 0; total += 1
        print(f"  {sym:6}{s*100:>9.0f}%{bh*100:>9.0f}%{rnd*100:>9.0f}%   "
              f"{'BEATS hold ✅' if ok else 'lags hold ❌'}")
    print("=" * 66)
    print(f"  Beat buy-and-hold on {beat}/{total} names out-of-sample.")
    print("  (Honest expectation: few or none. The agent's value is disciplined")
    print("   execution + risk gates, not a magic edge — and the write-up says so.)")
