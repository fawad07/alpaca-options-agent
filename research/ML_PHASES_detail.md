# ML Phases — detailed roadmap (design only)

Deep-dive on M0–M5 from `DESIGN_ml_phase.md`. Each phase has an **honesty checkpoint**: a
pre-declared bar it must clear, or we iterate (bounded) / pivot / stop. Offline until M3.
Aim = **meta-labeling** (ML decides *whether the rule-signal is worth taking*), crypto first.

**Cross-cutting rules (apply to every phase):**
- **Pre-register the metric** before looking at results (e.g., "OOS net P&L vs buy-hold across all
  folds") so we can't move the goalposts.
- **Bounded iteration:** in the search phases, cap the number of feature/target retries (e.g., ≤5)
  — more attempts = p-hacking a false edge into existence.
- **Leakage is the enemy:** every feature/label causal; purge + embargo in CV; audit before trusting.
- **Reproducible:** fixed seeds, versioned cached data, saved model artifacts.

---

## M0 — Foundation: data · labels · features · baselines  *(offline)*
**Objective:** build the scaffolding to even *ask* "is there edge?" — no model yet.

**Sub-steps**
- **M0.1 Data** — `research/ml/` pipeline. Reuse cached crypto bars; extend `backtest_fetch.py`
  for stock/ETF daily bars if stocks are in scope. Fix a **date-based train/test split** up front.
- **M0.2 Features** (`features.py`) — ~10–15 **causal** features (trend, mean-reversion, ATR/vol,
  volume, a regime bucket). Reuse `signals.add_features`, extend. Unit-test: feature at *t* uses
  only data ≤ *t*.
- **M0.3 Labels** (`labels.py`) — **triple-barrier**: from each rule-signal, look forward → did it
  hit **+TP** (1) or **−SL** (0) first (timeout → drop/neutral)? This is the meta-label.
- **M0.4 Baselines** (`baselines.py`) — buy-and-hold · EMA/RSI rule · coin-flip, each measured OOS
  net of fees+slippage. These are the bars M1 must beat.

**Deliverable:** a labeled feature table per asset + baseline metrics.
**✅ Checkpoint:** baselines **reproduce the known results** (≈0/7 stocks, 0/4 coins) → proves the
pipeline is sound. A quick **leakage smoke-test** (shuffle labels → model should score ≈random).
**Feeds:** the dataset + baseline bar into M1.

---

## M1 — First model + THE honesty test  *(offline — make-or-break)*
**Objective:** train one model and rigorously test it OOS. This phase decides if ML adds anything.

**Sub-steps**
- **M1.1 Train** (`train.py`) — LightGBM meta-label classifier under **purged, embargoed
  walk-forward CV**: train on a past window → predict the next unseen window → roll forward.
- **M1.2 Evaluate** (`evaluate.py`) — take only the trades the model says "take" → simulate P&L
  OOS vs the 3 baselines, net of costs. Report hit-rate, precision on the "take" class, P&L,
  max drawdown, and **stability across folds and assets**.
- **M1.3 Verdict** against the pre-registered metric.

**✅ Checkpoint (the big one):** model beats **all 3 baselines OOS**, on a **plateau** (a range of
hyperparameters works, not one lucky spike), consistently across folds/assets.
- **PASS →** M2.
- **FAIL →** iterate within the bounded budget (different horizon / features / TP-SL); if still no
  edge, **honestly conclude "no directional edge"** and either **pivot to regime/vol** (help sizing,
  not direction) or **stop and ship nothing**. Both are acceptable, honest outcomes.

**Deliverable:** walk-forward OOS report + a clear PASS/FAIL verdict.

---

## M2 — Ensemble + calibration  *(offline, only if M1 passed)*
**Objective:** make the edge robust and its probabilities trustworthy + comparable across assets.

**Sub-steps**
- **M2.1 Ensemble** — add a logistic-regression floor (sanity) and optionally RandomForest;
  blend/stack with the LightGBM.
- **M2.2 Calibrate** — Platt/isotonic so output is a **true probability**. This makes `confidence`
  comparable across BTC vs SPY etc. → fixes today's "crypto always ranks 1.00" unfairness.
- **M2.3 Re-validate** — ensemble must still beat baselines OOS (≥ M1, ideally steadier); check the
  **reliability curve** (predicted 60% should win ~60% of the time).

**✅ Checkpoint:** still beats OOS **and** calibration curve is sane.
**Deliverable:** calibrated ensemble + updated report + saved artifact.

---

## M3 — Shadow mode: live, log-only  *(LIVE data, no trades)*
**Objective:** prove it *forward* on data the model has never seen. Backtest edge ≠ live edge — this
is the honest forward test that catches overfitting the backtest missed.

**Sub-steps**
- **M3.1** `ml_signal.py` — loads the artifact, returns `{direction, confidence, reason}` per symbol
  at runtime (same interface as `signals.signal`).
- **M3.2 Shadow wiring** — account B computes BOTH the rule signal AND the ML prediction each run,
  **trades the rule as usual**, but **logs the ML's would-be decisions** to a shadow journal.
- **M3.3** Run for a real forward window (weeks) → compare ML's logged predictions to actual
  outcomes vs baselines. This is true, untouched OOS.

**✅ Checkpoint:** shadow-forward performance **holds up** (consistent with the backtest). If it
**collapses live** (very common) → do NOT deploy; back to M1 or conclude no-edge.
**Deliverable:** a forward shadow track record.

---

## M4 — Integrate: ML sizes real (paper) trades on account B  *(live)*
**Objective:** only if M1–M3 all passed, let ML drive sizing on account B (never account A).

**Sub-steps**
- **M4.1** Flip account B's **signal source** to the ML meta-label filter: rule sets `direction`,
  ML sets `confidence` + a **veto threshold** (below it → skip). Risk gates, broker stops, journal
  unchanged.
- **M4.2** Roll out gently — start with a tighter cap / subset, widen once stable.
- **M4.3** Keep the rule-based signal one config flip away (instant rollback).

**✅ Checkpoint:** live behaves like shadow; account A provably untouched.
**Deliverable:** ML live on account B.

---

## M5 — Monitor + retrain + fail-safe  *(ongoing)*
**Objective:** models decay — keep it honest over time.

**Sub-steps**
- **M5.1 Track** — extend the daily snapshot to log ML-account live performance **vs baselines**.
- **M5.2 Retrain** — scheduled walk-forward retrain (e.g., monthly) on new data; **versioned**
  artifacts; a retrained model is promoted only if it **re-passes the OOS gate**.
- **M5.3 Fail-safe** — if live performance drops below baseline for a set period, **auto-revert to
  the rule-based signal**. Edge decay shouldn't quietly bleed the account.

**Deliverable:** monitoring + retrain pipeline + auto-revert.

---

## Dependency / effort map
```
M0 (offline) ─► M1 (offline, GATE) ─► M2 (offline) ─► M3 (live shadow) ─► M4 (live) ─► M5 (ongoing)
                     │ FAIL
                     └► iterate (≤5) → pivot to regime/vol → or STOP (ship nothing)
```
- **M0–M2 are pure research** (no live risk) — most of the real work + the honesty gate live here.
- **M3 is the truth serum** (live but no trades).
- **M4–M5** only happen if the edge is real and survives forward.

## New files this phase will add (when we build)
`research/ml/{features,labels,baselines,train,evaluate}.py` · saved model artifacts ·
`ml_signal.py` (root, runtime) · `requirements-ml.txt` (scikit-learn, lightgbm) · a shadow journal.
