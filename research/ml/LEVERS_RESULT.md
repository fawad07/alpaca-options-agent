# Levers experiment — results (2026-09-13)

Same rule-bull entries on the 4 coins, fixed sensible params (no tuning), cost 0.6%/trade,
full history. Comparison is *relative* (which lever helps), not a safety claim — per-coin
drawdowns are huge because it's always-long a single coin through crypto crashes.

| Variant | trades | hit% | avg/trade | avg total | avg maxDD | ret/DD |
|---|---|---|---|---|---|---|
| Baseline (fixed 30/15) | 182 | 40.1 | +1.03% | +27% | −75.8% | 0.42 |
| **L3 ATR (2/4)** ⭐ | 174 | 37.6 | **+2.39%** | **+94%** | −76.9% | **1.26** |
| L3 ATR + trailing | 210 | 33.9 | +1.94% | +6% | −76.3% | 0.09 |
| L2 vol-size | 182 | 40.1 | +1.03% | −3% | −74.1% | 0.03 |
| **L2 + L3** | 174 | 37.6 | +2.39% | +44% | **−65.7%** | 0.64 |

## Read
- **L3 (ATR-scaled exits) is the clear winner:** ~2× expectancy (+2.39 vs +1.03), ~3.5× total
  return, ~3× return/drawdown vs the fixed 30/15. Fitting exits to each asset's volatility works —
  exactly what the 16%-mismatch predicted.
- **Trailing stop hurts** (cuts winners early) → drop it.
- **Vol-sizing (L2) alone barely moves returns**, but **L2+L3 cuts max drawdown** (−66% vs −77%)
  at the cost of some return → a useful risk dampener if we prioritize smoother equity.
- **L1 calibration** confirmed: raw confidence pins every asset near 1.00 (0.79–0.87 mean); the
  percentile transform makes them comparable (mean 0.50) → fair options-vs-crypto ranking.

## Verdict / what to keep
- ✅ **Adopt L3 (ATR exits)** — but first **confirm robustness** (walk-forward sweep of the
  multiples; require a plateau, not just the 2/4 point) before deploying. One fixed setting isn't
  enough to trust.
- ✅ **Adopt L1 (calibration)** — low-risk fairness fix, deploy at ranking.
- 🟡 **L2 (vol-sizing)** — optional; keep if smaller drawdown > max return for you (L2+L3 best DD).
- ❌ **Drop trailing.**

## Honest caveats
- Params were fixed, not walk-forward-validated → L3's edge must survive a robustness check.
- Drawdowns are per-coin and severe; real safety comes from the portfolio (cap, 5% daily halt,
  diversification), tested at integration on account B.
