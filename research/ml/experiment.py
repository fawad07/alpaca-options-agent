"""
experiment.py — build + test Levers 1/2/3 and compare (honest, risk-metric based).

Backtests the SAME rule-bull entries on the cached crypto data under different
exit/sizing variants, and reports risk metrics. No parameter tuning on the test data
(fixed sensible params) so no variant gets an overfitting advantage.

  Baseline        fixed +30%/−15%, fixed size          (what we trade today)
  L3-ATR          ATR-scaled SL=2·ATR / TP=4·ATR        (smarter finish line)
  L3-ATR+trail    ATR exits + trailing stop (3·ATR)     (lock gains)
  L2-volsize      fixed exits + inverse-vol sizing      (smaller drawdowns)
  L2+L3           ATR exits + inverse-vol sizing         (both)

Lever 1 (calibration) is a cross-asset ranking transform — demonstrated separately at
the bottom (its benefit is options-vs-crypto fairness, tested at integration).

Run:  .venv/bin/python research/ml/experiment.py
"""
from __future__ import annotations
import os, sys, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import config as C

DATA = os.path.join(ROOT, "research", "data")
ROUNDTRIP = 0.006          # fees + slippage per round trip
HORIZON = 60               # max bars to hold before force-exit


def indicators(df):
    c, h, l = df["close"], df["high"], df["low"]
    ema_f, ema_s = c.ewm(span=C.EMA_FAST).mean(), c.ewm(span=C.EMA_SLOW).mean()
    d = c.diff()
    gain = d.clip(lower=0).rolling(C.RSI_PERIOD).mean()
    loss = (-d.clip(upper=0)).rolling(C.RSI_PERIOD).mean()
    rsi = 100 - 100 / (1 + gain / (loss + 1e-9))
    gap = (ema_f - ema_s).abs() / ema_s
    conf = np.minimum(1.0, 0.5 + gap * 8)
    bull = (ema_f > ema_s) & (rsi < C.RSI_BULL_MAX) & (conf >= C.MIN_CONFIDENCE)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    rvol = c.pct_change().rolling(20).std()
    return bull.values, atr.values, rvol.values


def simulate(df, variant):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    bull, atr, rvol = indicators(df)
    n = len(df)
    tgt_vol = np.nanmedian(rvol)
    rets, sizes, i = [], [], 1
    while i < n - 1:
        if not bull[i] or np.isnan(atr[i]) or atr[i] <= 0:
            i += 1; continue
        entry = o[i + 1]
        # barriers
        if variant["exit"] == "atr":
            sl = entry - variant["sl_mult"] * atr[i]
            tp = entry + variant["tp_mult"] * atr[i]
        else:
            sl = entry * (1 - C.CRYPTO_STOP_PCT)
            tp = entry * (1 + C.CRYPTO_TP_PCT)
        trail_on = variant.get("trail")
        run_high = entry
        j, exit_px = i + 1, None
        while j < min(i + 1 + HORIZON, n):
            run_high = max(run_high, h[j])
            stop = sl
            if trail_on:
                stop = max(stop, run_high - variant["trail_mult"] * atr[i])
            if l[j] <= stop:
                exit_px = stop; break
            if h[j] >= tp:
                exit_px = tp; break
            j += 1
        if exit_px is None:
            exit_px = c[min(i + HORIZON, n - 1)]; j = min(i + HORIZON, n - 1)
        r = exit_px / entry - 1 - ROUNDTRIP
        # sizing
        if variant["sizing"] == "invvol" and rvol[i] and not np.isnan(rvol[i]):
            size = float(np.clip(tgt_vol / rvol[i], 0.25, 2.0))
        else:
            size = 1.0
        rets.append(r); sizes.append(size)
        i = j + 1
    return np.array(rets), np.array(sizes)


def metrics(rets, sizes):
    if len(rets) == 0:
        return dict(trades=0, hit=0, avg=0, total=0, maxdd=0, calmar=0)
    eq = np.cumprod(1 + sizes * rets)
    peak = np.maximum.accumulate(eq)
    maxdd = ((eq - peak) / peak).min()
    total = eq[-1] - 1
    return dict(trades=len(rets), hit=(rets > 0).mean() * 100, avg=rets.mean() * 100,
                total=total * 100, maxdd=maxdd * 100,
                calmar=(total / abs(maxdd)) if maxdd < 0 else float("inf"))


VARIANTS = {
    "Baseline (fixed 30/15)": dict(exit="fixed", sizing="fixed"),
    "L3 ATR (2/4)":           dict(exit="atr", sl_mult=2, tp_mult=4, sizing="fixed"),
    "L3 ATR+trail":           dict(exit="atr", sl_mult=2, tp_mult=4, trail=True, trail_mult=3, sizing="fixed"),
    "L2 vol-size":            dict(exit="fixed", sizing="invvol"),
    "L2+L3":                  dict(exit="atr", sl_mult=2, tp_mult=4, sizing="invvol"),
}


def main():
    coins = {os.path.basename(f).replace("-", "/").replace(".csv", ""):
             pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(os.path.join(DATA, "*.csv")))}
    print(f"Lever experiment — {len(coins)} coins, fixed params (no tuning), cost {ROUNDTRIP:.1%}/trade\n")
    agg = {}
    for name, v in VARIANTS.items():
        per = [metrics(*simulate(df, v)) for df in coins.values()]
        agg[name] = {
            "trades": sum(p["trades"] for p in per),
            "hit": np.mean([p["hit"] for p in per]),
            "avg": np.mean([p["avg"] for p in per]),
            "total": np.mean([p["total"] for p in per]),      # avg per-coin total return
            "maxdd": np.mean([p["maxdd"] for p in per]),
            "calmar": np.mean([p["calmar"] for p in per if np.isfinite(p["calmar"])]),
        }
    print(f"{'variant':24} {'trades':>7} {'hit%':>6} {'avg/trade':>10} {'avg total':>10} {'avg maxDD':>10} {'ret/DD':>7}")
    for name, m in agg.items():
        print(f"{name:24} {m['trades']:>7} {m['hit']:>5.1f} {m['avg']:>+9.2f}% {m['total']:>+9.0f}% "
              f"{m['maxdd']:>+9.1f}% {m['calmar']:>6.2f}")

    # ---- Lever 1: calibration transform demo (cross-asset comparability) ----
    print("\n--- Lever 1 (calibration): raw vs percentile-normalized confidence range per coin ---")
    for coin, df in coins.items():
        c = df["close"]
        ema_f, ema_s = c.ewm(span=C.EMA_FAST).mean(), c.ewm(span=C.EMA_SLOW).mean()
        gap = (ema_f - ema_s).abs() / ema_s
        raw = np.minimum(1.0, 0.5 + gap * 8)
        pct = raw.rank(pct=True)               # percentile within this asset (rolling in prod)
        print(f"  {coin:9} raw mean {raw.mean():.2f} (max {raw.max():.2f})  →  calibrated mean {pct.mean():.2f} (0..1, comparable)")
    print("  (raw pins high-vol assets near 1.00 → they crowd the ranking; calibrated is comparable across assets.)")


if __name__ == "__main__":
    main()
