"""
backtest_crypto.py — honest crypto-spot backtester (WS1, steps 1.2–1.5).

Long-only spot. Entry = the live BULL signal (EMA20>50 + RSI<72, conf>=MIN_CONFIDENCE).
Exit = -stop% or +take%, whichever hits first (bar high/low), stop given priority.
Fees + slippage modeled. Sweeps stop×take, then WALK-FORWARD out-of-sample validation,
compares to buy-and-hold, and writes research/BACKTEST_crypto.md.

Run:  .venv/bin/python research/backtest_crypto.py
"""
from __future__ import annotations
import os, sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config as C
from signals import add_features

DATA = os.path.join(os.path.dirname(__file__), "data")
REPORT = os.path.join(os.path.dirname(__file__), "BACKTEST_crypto.md")
FEE = 0.0025          # 25 bps per side (Alpaca crypto taker ~ conservative)
SLIP = 0.0010         # 10 bps slippage per side
STOPS = [0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20]
TAKES = [0.08, 0.12, 0.16, 0.20, 0.25, 0.30, 0.40]


def load(path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = add_features(df)                      # EMA_fast/slow, RSI (causal)
    trend_up = df["EMA_fast"] > df["EMA_slow"]
    gap = (df["EMA_fast"] - df["EMA_slow"]).abs() / df["EMA_slow"]
    conf = np.minimum(1.0, 0.5 + gap * 8)
    df["bull"] = trend_up & (df["RSI"] < C.RSI_BULL_MAX) & (conf >= C.MIN_CONFIDENCE)
    return df.reset_index(drop=True)


def simulate(df: pd.DataFrame, stop: float, take: float, lo=None, hi=None) -> list[float]:
    """Return list of net per-trade returns over bars [lo,hi). Enter next open after a
    bull signal; exit on stop/take. Long-only, one position at a time."""
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    bull = df["bull"].values
    n = len(df)
    lo = 0 if lo is None else lo
    hi = n if hi is None else hi
    rets, i = [], lo
    while i < hi - 1:
        if not bull[i]:
            i += 1; continue
        entry = o[i + 1] * (1 + SLIP)          # fill next open, pay slippage
        sp, tp = entry * (1 - stop), entry * (1 + take)
        j = i + 1; exit_px = None
        while j < hi:
            if l[j] <= sp: exit_px = sp * (1 - SLIP); break      # stop first (conservative)
            if h[j] >= tp: exit_px = tp * (1 - SLIP); break
            j += 1
        if exit_px is None:
            exit_px = c[hi - 1] * (1 - SLIP)                     # close out at window end
            j = hi
        rets.append(exit_px / entry - 1 - 2 * FEE)              # fees both sides
        i = j + 1
    return rets


def metrics(rets: list[float]) -> dict:
    if not rets:
        return {"trades": 0, "win": 0, "avg": 0, "total": 0, "maxdd": 0, "pf": 0}
    r = np.array(rets)
    eq = np.cumprod(1 + r)
    peak = np.maximum.accumulate(eq)
    maxdd = ((eq - peak) / peak).min()
    wins, losses = r[r > 0], r[r <= 0]
    pf = (wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf")
    return {"trades": len(r), "win": (r > 0).mean() * 100, "avg": r.mean() * 100,
            "total": (eq[-1] - 1) * 100, "maxdd": maxdd * 100, "pf": pf}


def buy_hold(df, lo, hi):
    return (df["close"].values[hi - 1] / df["close"].values[lo] - 1) * 100


def walk_forward(df, train=548, test=183):
    """Rolling: optimize (stop,take) by profit factor on train, apply to next test window.
    Returns list of (test_total, bh_total, chosen)."""
    out, i, n = [], 0, len(df)
    while i + train + test <= n:
        tr_lo, tr_hi = i, i + train
        te_lo, te_hi = i + train, i + train + test
        best, best_pf = None, -1
        for st in STOPS:
            for tk in TAKES:
                m = metrics(simulate(df, st, tk, tr_lo, tr_hi))
                if m["trades"] >= 3 and m["pf"] > best_pf and np.isfinite(m["pf"]):
                    best_pf, best = m["pf"], (st, tk)
        if best:
            te = metrics(simulate(df, best[0], best[1], te_lo, te_hi))
            out.append((te["total"], buy_hold(df, te_lo, te_hi), best))
        i += test
    return out


def main():
    files = sorted(glob.glob(os.path.join(DATA, "*.csv")))
    coins = {os.path.basename(f).replace("-", "/").replace(".csv", ""): load(f) for f in files}

    # ---- full-history sweep (robustness plateau) ----
    plateau = {}   # (stop,take) -> list of per-coin total returns
    per_coin_best = {}
    for name, df in coins.items():
        best = None
        for st in STOPS:
            for tk in TAKES:
                m = metrics(simulate(df, st, tk))
                plateau.setdefault((st, tk), []).append(m["total"])
                if best is None or m["total"] > best[1]["total"]:
                    best = ((st, tk), m)
        per_coin_best[name] = best

    plateau_avg = {k: float(np.mean(v)) for k, v in plateau.items()}
    ranked = sorted(plateau_avg.items(), key=lambda kv: kv[1], reverse=True)

    # ---- walk-forward OOS ----
    wf = {name: walk_forward(df) for name, df in coins.items()}

    # ---- write report ----
    L = ["# Crypto backtest — honest results", "",
         f"Coins: {', '.join(coins)} · daily 2021→2026 · fees {FEE*100:.2f}%/side + slippage {SLIP*100:.2f}%/side.",
         "Long-only spot; entry = live bull signal (EMA20>50, RSI<72); exit = −stop% / +take%.", ""]

    L += ["## Buy-and-hold benchmark (the honest bar)"]
    L += ["| Coin | Buy-hold total | Best strategy (full history) | Best (stop/take) |",
          "|---|---|---|---|"]
    for name, df in coins.items():
        bh = buy_hold(df, 0, len(df))
        (st, tk), m = per_coin_best[name]
        L.append(f"| {name} | {bh:+.0f}% | {m['total']:+.0f}% (maxDD {m['maxdd']:.0f}%, {m['trades']} trades) | {st*100:.0f}%/{tk*100:.0f}% |")
    L += [""]

    L += ["## Robust plateau — combos ranked by AVG total return across all 4 coins",
          "(A broad good region matters more than the single top cell — a lone spike = overfit.)", "",
          "| stop / take | avg total across coins |", "|---|---|"]
    for (st, tk), v in ranked[:10]:
        L.append(f"| {st*100:.1f}% / {tk*100:.0f}% | {v:+.0f}% |")
    L += [""]

    L += ["## Walk-forward — OUT-OF-SAMPLE (optimize on train, measure on unseen test)"]
    L += ["| Coin | OOS windows | avg OOS return | avg buy-hold (same windows) | OOS beat B&H? |",
          "|---|---|---|---|---|"]
    oos_all, bh_all = [], []
    for name, rows in wf.items():
        if not rows:
            L.append(f"| {name} | 0 | – | – | – |"); continue
        te = np.mean([r[0] for r in rows]); bh = np.mean([r[1] for r in rows])
        oos_all += [r[0] for r in rows]; bh_all += [r[1] for r in rows]
        L.append(f"| {name} | {len(rows)} | {te:+.1f}% | {bh:+.1f}% | {'yes' if te>bh else 'no'} |")
    if oos_all:
        L.append(f"| **ALL** | {len(oos_all)} | **{np.mean(oos_all):+.1f}%** | **{np.mean(bh_all):+.1f}%** | **{'yes' if np.mean(oos_all)>np.mean(bh_all) else 'no'}** |")
    L += [""]

    # recommended robust range = the parameter box covering the top plateau cells
    top = [k for k, _ in ranked[:6]]
    sset = sorted({k[0] for k in top}); tset = sorted({k[1] for k in top})
    L += ["## Recommended ROBUST RANGES (from the plateau, to confirm live on paper)",
          f"- **Stop %:** {min(sset)*100:.0f}–{max(sset)*100:.0f}%",
          f"- **Take-profit %:** {min(tset)*100:.0f}–{max(tset)*100:.0f}%",
          f"- **Position size:** from the 2%-risk rule ÷ stop%, capped at a max-notional (start 15%). "
          "Size scales risk, not edge, so it's a risk choice, not an optimization target.",
          "",
          "## Honest verdict",
          "- These ranges are a **robust region**, not a magic number — pick from the middle of the plateau.",
          "- Read the buy-and-hold column carefully: in a multi-year crypto bull run, **beating buy-and-hold on "
          "total return is hard**; the strategy's value is **lower drawdown / defined risk**, not out-gunning a hold.",
          "- Nothing is decided until it also survives **live paper** on account B.", ""]

    open(REPORT, "w").write("\n".join(L) + "\n")
    print("\n".join(L[:4]))
    print(f"...\nWrote {os.path.relpath(REPORT)}")
    if oos_all:
        print(f"OOS (all): strategy {np.mean(oos_all):+.1f}% vs buy-hold {np.mean(bh_all):+.1f}% per window")


if __name__ == "__main__":
    main()
