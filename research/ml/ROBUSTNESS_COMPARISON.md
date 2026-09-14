# Robustness comparison — L2 vs L3 (2026-09-13)

Same two-gate test for both: **plateau** (does a broad range of settings beat baseline, not one
lucky cell?) and **out-of-sample** (tune/set on train 60% → does it hold on the unseen last 40%?).

| Lever | Plateau (in-sample) | Out-of-sample | Verdict |
|---|---|---|---|
| **L3 · ATR exits** | ❌ **50%** (8/16 — lucky cell 2/4, scattered) | ❌ lost to baseline on **3/4** coins | **rejected** |
| **L2 · vol-sizing** | ✅ **100%** (8/8 reduce drawdown) | ❌ drawdown **worse** OOS (−54.4% vs −48.2%) | **rejected (fails OOS)** |

## Read
- **L3** wasn't even consistent in-sample (only half the settings worked) — it was curve-fit.
- **L2** *was* consistent in-sample (every setting reduced drawdown — a reliable *direction*),
  **but it failed forward**: on unseen data it didn't cut drawdown, it slightly increased it.
  (Its OOS ret/DD was a touch better, but maxDD — L2's actual job — got worse. Not deployable
  as a drawdown-reducer we can trust.)
- So L2 is "better than L3" only in that its in-sample effect is consistent; **both fail the
  out-of-sample gate**, which is the one that matters.

## Overall ML-pivot conclusion (honest)
Across the whole effort — **direction (M1), exits (L3), and sizing (L2)** — **nothing beats the
simple fixed baseline out-of-sample.** The only clean keeper is:

- ✅ **L1 · calibration** — a *fairness* fix (comparable cross-asset ranking). It makes no
  performance claim, so there's nothing to fail OOS; it just lets options and crypto compete
  evenly for slots. Safe to adopt.

Everything else stays simple: **fixed exits, fixed sizing.** This is fully consistent with the
project's thesis — markets are hard, there's no durable edge here, and we found that out
rigorously instead of shipping curve-fit "improvements." That honesty is the deliverable.
