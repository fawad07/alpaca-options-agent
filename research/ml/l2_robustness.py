"""
l2_robustness.py — is L2 (vol-sizing) a robust RISK improvement?

L2's job is reducing DRAWDOWN (not boosting return), so we judge it on that:
  1. PLATEAU (full history): across a range of sizing caps, does it consistently REDUCE
     max drawdown vs fixed sizing (without wrecking risk-adjusted return)?
  2. OUT-OF-SAMPLE: on the unseen last 40%, does the standard setting still cut drawdown?

All on the FIXED baseline exits (L3 was rejected).

Run:  .venv/bin/python research/ml/l2_robustness.py
"""
from __future__ import annotations
import os, sys, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(__file__); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
from experiment import simulate, metrics, DATA

FIXED = dict(exit="fixed", sizing="fixed")
HIS = [1.25, 1.5, 2.0, 2.5]      # how much you can UP-size in calm markets
LOS = [0.25, 0.5]                # how much you DOWN-size in storms


def agg(coins, variant, key, lo=1, hi=None):
    vals = [metrics(*simulate(df, variant, lo=lo, hi=hi))[key] for df in coins.values()]
    return float(np.mean([v for v in vals if np.isfinite(v)]))


def main():
    coins = {os.path.basename(f).replace("-", "/").replace(".csv", ""):
             pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(os.path.join(DATA, "*.csv")))}

    base_dd = agg(coins, FIXED, "maxdd")
    base_cal = agg(coins, FIXED, "calmar")
    print(f"Baseline (fixed sizing): maxDD {base_dd:.1f}% · ret/DD {base_cal:.2f}\n")

    # ---- 1. PLATEAU: does L2 reduce drawdown across sizing caps? ----
    print("PLATEAU — max drawdown across sizing caps (less-negative = better); * = better than baseline:")
    print("  down\\up  " + "".join(f"{u:>8}" for u in HIS))
    beat = tot = 0
    for lo in LOS:
        row = f"  {lo:>5}  "
        for hi in HIS:
            v = agg(coins, dict(exit="fixed", sizing="invvol", size_lo=lo, size_hi=hi), "maxdd")
            tot += 1; beat += (v > base_dd)          # v > base_dd means smaller drop (both negative)
            row += f"{v:>7.1f}{'*' if v > base_dd else ' '}"
        print(row)
    print(f"\n  cells reducing drawdown: {beat}/{tot}  ({beat/tot:.0%})")

    # ---- 2. OUT-OF-SAMPLE (standard L2 on unseen last 40%) ----
    print("\nOUT-OF-SAMPLE — standard L2 (0.25–2.0) vs baseline on test(40%):")
    L2 = dict(exit="fixed", sizing="invvol", size_lo=0.25, size_hi=2.0)
    dd_l2, dd_b, cal_l2, cal_b = [], [], [], []
    for coin, df in coins.items():
        split = int(0.6 * len(df))
        m2 = metrics(*simulate(df, L2, lo=split)); mb = metrics(*simulate(df, FIXED, lo=split))
        dd_l2.append(m2["maxdd"]); dd_b.append(mb["maxdd"])
        cal_l2.append(m2["calmar"]); cal_b.append(mb["calmar"])
        print(f"  {coin:9} TEST maxDD  L2 {m2['maxdd']:>7.1f}%  vs baseline {mb['maxdd']:>7.1f}%  "
              f"({'L2 safer' if m2['maxdd'] > mb['maxdd'] else 'baseline'})")
    mdd2, mddb = np.mean(dd_l2), np.mean(dd_b)
    print(f"\n  OOS avg maxDD:  L2 {mdd2:.1f}%  vs baseline {mddb:.1f}%   "
          f"(ret/DD  L2 {np.nanmean(cal_l2):.2f} vs {np.nanmean(cal_b):.2f})")

    plateau_ok = beat / tot >= 0.7
    oos_ok = mdd2 > mddb
    print("\n=== VERDICT ===")
    print(f"  Plateau (broadly reduces drawdown): {'✅' if plateau_ok else '❌'}  ({beat/tot:.0%})")
    print(f"  Out-of-sample (cuts drawdown forward): {'✅' if oos_ok else '❌'}")
    print(f"  >>> {'✅ L2 is a ROBUST risk-dampener' if plateau_ok and oos_ok else '⚠️ mixed — weak/uncertain'} <<<")


if __name__ == "__main__":
    main()
