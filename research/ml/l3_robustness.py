"""
l3_robustness.py — is L3 (ATR-scaled exits) a real, robust improvement, or a fluke of 2/4?

Two tests:
  1. PLATEAU (full history): sweep SL×TP ATR-multiples → does a BROAD region beat the fixed
     baseline's reward-for-pain (ret/DD), or only one lucky cell?
  2. OUT-OF-SAMPLE: tune the best multiples on the first 60% of each coin, then measure on the
     last 40% (unseen). Does the improvement generalize forward?

Run:  .venv/bin/python research/ml/l3_robustness.py
"""
from __future__ import annotations
import os, sys, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(__file__); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from experiment import simulate, metrics, DATA

SLS = [1.5, 2.0, 2.5, 3.0]
TPS = [2, 3, 4, 5, 6]
FIXED = dict(exit="fixed", sizing="fixed")


def agg(coins, variant, lo=1, hi=None, key="calmar"):
    vals = []
    for df in coins.values():
        m = metrics(*simulate(df, variant, lo=lo, hi=hi))
        vals.append(m[key])
    return float(np.mean([v for v in vals if np.isfinite(v)]))


def main():
    coins = {os.path.basename(f).replace("-", "/").replace(".csv", ""):
             pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(os.path.join(DATA, "*.csv")))}

    base = agg(coins, FIXED, key="calmar")
    base_avg = agg(coins, FIXED, key="avg")
    print(f"Baseline (fixed 30/15): ret/DD {base:.2f} · avg/trade {base_avg:+.2f}%\n")

    # ---- 1. PLATEAU sweep (full history), metric = ret/DD ----
    print("PLATEAU — ret/DD across ATR multiples (SL rows × TP cols); >baseline in each cell:")
    header = "  SL\\TP  " + "".join(f"{tp:>7}" for tp in TPS)
    print(header)
    beat = tot = 0
    for sl in SLS:
        row = f"  {sl:>4}  "
        for tp in TPS:
            if tp <= sl:                      # target must exceed stop
                row += f"{'-':>7}"; continue
            v = agg(coins, dict(exit="atr", sl_mult=sl, tp_mult=tp, sizing="fixed"))
            tot += 1; beat += (v > base)
            mark = "*" if v > base else " "
            row += f"{v:>6.2f}{mark}"
        print(row)
    print(f"\n  cells beating baseline: {beat}/{tot}  ({beat/tot:.0%})   (* = beats baseline)")

    # ---- 2. OUT-OF-SAMPLE (tune on first 60%, test on last 40%) ----
    print("\nOUT-OF-SAMPLE — tune multiples on train(60%), measure on test(40%):")
    test_l3, test_base = [], []
    for coin, df in coins.items():
        n = len(df); split = int(0.6 * n)
        best, best_v = None, -1e9
        for sl in SLS:
            for tp in TPS:
                if tp <= sl:
                    continue
                v = metrics(*simulate(df, dict(exit="atr", sl_mult=sl, tp_mult=tp, sizing="fixed"),
                                      lo=1, hi=split))["calmar"]
                if np.isfinite(v) and v > best_v:
                    best_v, best = v, (sl, tp)
        l3_test = metrics(*simulate(df, dict(exit="atr", sl_mult=best[0], tp_mult=best[1], sizing="fixed"),
                                    lo=split))
        b_test = metrics(*simulate(df, FIXED, lo=split))
        test_l3.append(l3_test["calmar"]); test_base.append(b_test["calmar"])
        print(f"  {coin:9} train-best {best}  → TEST ret/DD  L3 {l3_test['calmar']:>6.2f}  vs  "
              f"baseline {b_test['calmar']:>6.2f}  ({'L3 wins' if l3_test['calmar']>b_test['calmar'] else 'baseline'})")
    ml3 = np.mean([v for v in test_l3 if np.isfinite(v)])
    mb = np.mean([v for v in test_base if np.isfinite(v)])
    print(f"\n  OOS avg ret/DD:  L3 {ml3:.2f}  vs  baseline {mb:.2f}")

    plateau_ok = beat / tot >= 0.7
    oos_ok = ml3 > mb
    print("\n=== VERDICT ===")
    print(f"  Plateau (broad region beats baseline): {'✅' if plateau_ok else '❌'}  ({beat/tot:.0%})")
    print(f"  Out-of-sample (tuned generalizes forward): {'✅' if oos_ok else '❌'}")
    print(f"  >>> {'✅ L3 is ROBUST — safe to adopt' if plateau_ok and oos_ok else '⚠️ mixed — treat with caution'} <<<")


if __name__ == "__main__":
    main()
