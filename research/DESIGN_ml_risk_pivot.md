# Design — ML pivot: smarter RISK & EXECUTION (not alpha)

**Premise (honest):** direction can't be predicted from price (M1 failed OOS, like options 0/7
and crypto 0/4). So we stop chasing alpha and instead make the agent **trade the same signal
more intelligently** — fairer ranking, safer sizing, and a better-fitted finish line. Everything
here is validated on **risk metrics (drawdown, expectancy, risk-adjusted return) out-of-sample**,
never on "beating buy-and-hold." "ML" is an *optional enhancement*; the core is sound quant risk.

Three levers:

---

## Lever 1 — Calibration: fair cross-asset ranking
**Problem:** confidence = `min(1, 0.5 + gap×8)` → crypto's big EMA gaps push it to ~1.00 always,
so crypto **crowds options out** of the 6 slots.
**Fix:** rescale confidence to be **comparable across assets** — convert each signal to its
**percentile within that asset's own recent confidence distribution** (rolling). "How strong is
this signal *for this asset*", not raw magnitude. Options and crypto then compete fairly.
- This is **statistics, not prediction** — no edge claim, just fairness.
**Validate:** the fill mix is balanced across assets; no asset structurally dominates; sanity A/B.
**Effort:** small (a transform in the ranking step).

## Lever 2 — Regime / volatility sizing: smaller drawdowns
**Idea:** size **inversely to volatility** — calm markets → normal size; choppy/high-vol → size
down (or skip). Volatility **clusters** (it *is* predictable, unlike direction), so this is achievable.
**Start:** inverse-vol / vol-target sizing (a proven quant rule) using ATR / realized vol we already
compute. **ML optional later:** a small vol-forecast model — but only kept if it beats "just use
recent realized vol."
**Validate:** OOS **max drawdown** + **risk-adjusted return (Sharpe/Calmar)** vs fixed sizing, via
the backtester. Win = **smaller drawdowns** for similar return.

## Lever 3 — Smarter finish line: adaptive exits  ⭐ (most promising)
**Problem:** fixed **+30% / −15%** is poorly matched — only **16%** of signals reach +30% before
−15%. The targets don't fit each asset's actual movement.
**Fix:** scale TP/SL to the asset's **volatility (ATR)**: `SL = k × ATR`, `TP = m × ATR` — tight
stops on calm assets, wide on wild ones, so the finish line fits the instrument's noise. Options:
- **ATR-scaled barriers** (primary)
- **trailing stop** (ratchet the stop up as price rises → lock gains)
- **regime-dependent** (wider in trends, tighter in chop)
**Validate:** OOS **expectancy + hit rate + drawdown** vs the fixed 30%/15%, via the backtester —
sweep `k, m` with **walk-forward** and require a **robust plateau** (not one lucky combo).
**Why it's most promising:** it directly fixes the mismatch the data already exposed; a better-fitted
finish line can lift expectancy without predicting anything.

---

## Honest framing
None of these predict the market. They make the agent trade an edgeless signal **fairer, safer, and
better-fitted.** We keep only what improves risk metrics **out-of-sample**, and drop what doesn't —
same discipline as the alpha hunt, applied to risk. Realistic outcome: **smaller drawdowns and less
churn**, maybe better expectancy from Lever 3 — not a money machine.

## Build order (recommended)
1. **Lever 3 (adaptive exits)** — most testable, addresses the M0 finding, reuses the backtester.
2. **Lever 2 (vol sizing)** — layer on once exits are set.
3. **Lever 1 (calibration)** — a small, clean change to the ranking step.

Each lever: **design → backtest OOS (walk-forward) → keep only if it beats the fixed baseline →
integrate on account B → observe in shadow/live.** Account A stays untouched V1.

## Open questions
1. Start with **Lever 3 (adaptive exits)** — recommended — or Lever 1 (quick fairness win)?
2. Exits: ATR-scaled barriers first, add **trailing stop** as a variant to test?
3. Confirm: **rule-based first**, add ML forecasts only where they *beat* the rule OOS?
