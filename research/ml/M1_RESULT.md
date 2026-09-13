# M1 result — no out-of-sample directional edge (2026-09-13)

**Verdict: ❌ FAIL.** The LightGBM meta-label model cannot reliably pick which rule-bull
signals will win, out-of-sample. We do NOT proceed to deploy it for direction/alpha.

## Numbers (purged walk-forward, 5 folds, 2539 samples)
| | value |
|---|---|
| Base rate (rule win rate) | 16.1% |
| **Breakeven precision needed** (TP 30% / SL 15%) | **33.3%** |
| **Model precision on its OOS picks (pooled)** | **15.8%** (57 trades) |
| Take-all rule precision (same OOS) | 12.9% |
| Model expectancy / trade | **−7.89%** (take-all −9.21%) |

Per fold: fold 1 looked promising (25.7% on 35 picks) then folds 2–5 **collapsed to ~0%**
with very few picks — the classic signature of a pattern that fit the early data and did
**not generalize forward.** Pooled, the model barely edges take-all and is nowhere near the
33.3% needed to be profitable.

## Honest interpretation
The EMA/RSI **price-only signal has no edge**, and ML **cannot manufacture alpha that isn't
there.** This matches everything else we've found (options 0/7 OOS, crypto 0/4 OOS). Trying
harder (more features/tuning) would most likely just overfit a false edge — which the whole
project is built to avoid.

## What we do instead (per the M1 checkpoint)
Don't chase direction. Pivot ML to where the value is actually achievable and doesn't require
predicting returns:
- **Calibration** — turn the confidence into a true, cross-asset-comparable probability (fixes
  "crypto always ranks 1.00"; makes options vs crypto compete fairly). Reliable win, no alpha needed.
- **Regime / volatility** — predict *how choppy/volatile* it is (easier than direction) to **size
  down in bad regimes** → smoother equity, smaller drawdowns. A risk win, not a return claim.

These improve v2's *fairness and safety* regardless of edge — and stay honest.
