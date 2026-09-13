"""
m1.py — ML Phase M1: the make-or-break out-of-sample test.

Trains a LightGBM meta-label model with PURGED, EMBARGOED walk-forward CV and asks:
can it pick which rule-bull signals actually win, well enough to be profitable on data
it never saw? Compares to baselines. Willing to say NO.

Honesty rules baked in:
  • time-ordered walk-forward (train on past → test on unseen future)
  • embargo gap = label horizon (no train/test overlap through the 20-day labels)
  • decision threshold tuned on TRAIN only, applied to TEST
  • baselines: take-all rule + coin-flip
  • payoff model: win=+TP, loss=-SL → breakeven precision = SL/(TP+SL)

Run:  .venv/bin/python research/ml/m1.py
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
from lightgbm import LGBMClassifier

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import config as C
from features import FEATURES

TP, SL = C.CRYPTO_TP_PCT, C.CRYPTO_STOP_PCT
HORIZON = 20                        # must match m0 (embargo = horizon)
N_FOLDS = 5
BREAKEVEN = SL / (TP + SL)          # precision needed to break even (win=+TP, loss=-SL)


def expectancy(win_rate: float) -> float:
    """Avg return per trade given a win rate, payoff win=+TP / loss=-SL."""
    return win_rate * TP - (1 - win_rate) * SL


def best_threshold(proba, y):
    """Pick the probability cutoff that maximizes expectancy on TRAIN (needs >=20 picks)."""
    best_t, best_e = 0.5, -1e9
    for t in np.quantile(proba, np.linspace(0.5, 0.95, 19)):
        take = proba >= t
        if take.sum() < 20:
            continue
        e = expectancy(y[take].mean())
        if e > best_e:
            best_e, best_t = e, t
    return best_t


def main():
    df = pd.read_csv(os.path.join(HERE, "datasets", "ALL.csv"), parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    X_all, y_all = df[FEATURES].values, df["label"].values
    n = len(df)
    base = y_all.mean()
    print(f"M1 walk-forward — {n} samples · base rate {base:.1%} · "
          f"breakeven precision {BREAKEVEN:.1%} (TP {TP:.0%}/SL {SL:.0%})\n")

    # time-ordered folds: expanding train → next block is test, with an embargo gap
    bounds = np.linspace(0, n, N_FOLDS + 2, dtype=int)
    rows = []
    for k in range(1, N_FOLDS + 1):
        tr_end = bounds[k]
        te_lo, te_hi = bounds[k + 1] if False else bounds[k], bounds[k + 1]
        # train = [0, tr_end - embargo) ; test = [te_lo, te_hi)
        tr_hi = max(0, te_lo - HORIZON)          # embargo: drop last HORIZON before test
        if tr_hi < 100 or te_hi - te_lo < 30:
            continue
        Xtr, ytr = X_all[:tr_hi], y_all[:tr_hi]
        Xte, yte = X_all[te_lo:te_hi], y_all[te_lo:te_hi]
        pos = ytr.sum()
        if pos < 10:
            continue
        model = LGBMClassifier(
            n_estimators=200, learning_rate=0.03, num_leaves=15, max_depth=4,
            min_child_samples=30, subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=(len(ytr) - pos) / pos, random_state=42, verbose=-1)
        model.fit(Xtr, ytr)
        ptr, pte = model.predict_proba(Xtr)[:, 1], model.predict_proba(Xte)[:, 1]
        thr = best_threshold(ptr, ytr)
        take = pte >= thr
        m_prec = yte[take].mean() if take.sum() else float("nan")
        rows.append({
            "fold": k, "train_n": tr_hi, "test_n": len(yte),
            "model_takes": int(take.sum()), "model_precision": m_prec,
            "model_exp": expectancy(m_prec) if take.sum() else float("nan"),
            "takeall_precision": yte.mean(), "takeall_exp": expectancy(yte.mean()),
        })

    R = pd.DataFrame(rows)
    print(f"{'fold':>4} {'train':>7} {'test':>6} {'picks':>6} {'MODEL prec':>11} {'model exp':>10} "
          f"{'take-all prec':>14} {'take-all exp':>13}")
    for _, r in R.iterrows():
        print(f"{int(r.fold):>4} {int(r.train_n):>7} {int(r.test_n):>6} {int(r.model_takes):>6} "
              f"{r.model_precision:>10.1%} {r.model_exp:>+9.2%} {r.takeall_precision:>13.1%} {r.takeall_exp:>+12.2%}")

    # aggregate OOS: pool all model picks across folds
    tot_picks = R["model_takes"].sum()
    w = R["model_takes"]
    oos_prec = (R["model_precision"] * w).sum() / w.sum() if w.sum() else float("nan")
    oos_takeall = R["takeall_precision"].mean()
    print("\n=== VERDICT (out-of-sample, pooled) ===")
    print(f"  Model precision on its picks : {oos_prec:.1%}  ({int(tot_picks)} trades taken)")
    print(f"  Take-all rule precision      : {oos_takeall:.1%}")
    print(f"  Breakeven needed             : {BREAKEVEN:.1%}")
    print(f"  Model expectancy/trade       : {expectancy(oos_prec):+.2%}   "
          f"(take-all: {expectancy(oos_takeall):+.2%})")
    beats = oos_prec > BREAKEVEN and oos_prec > oos_takeall + 0.03
    print(f"\n  >>> {'✅ PASS — beats breakeven AND take-all OOS' if beats else '❌ FAIL — no real OOS edge'} <<<")
    if not beats:
        print("  Honest read: this is the expected outcome for a simple price-only signal.")


if __name__ == "__main__":
    main()
