# Design — ML Phase (design only, not built)

**Goal:** find a signal with a **real, out-of-sample edge**, because the simple EMA/RSI rule
has none (proved: **0/7** stocks, **0/4** coins OOS). **Honesty gate:** no model ships unless it
beats the baselines out-of-sample, net of costs, across folds — and if none does, we say so and
don't deploy. This phase is designed to *detect the absence of edge*, not to force one.

> Prior (be honest): short-horizon price direction is close to a coin flip; most retail ML
> "alpha" is overfitting. We assume the base rate is "no durable edge" and make the model earn
> its way past that. The value may end up being **risk/regime**, not return prediction — that's
> a legitimate, useful outcome, not a failure.

---

## 1. The three things ML could actually do (pick where to aim)
| Approach | What it predicts | Odds | Integration |
|---|---|---|---|
| **A. Meta-labeling** ⭐ | *"Will THIS rule-signal work?"* (take / skip / size) | best | filters the existing signal — cleanest fit |
| B. Direction (alpha) | up/down over horizon H | hardest (near-efficient) | replaces the rule's direction |
| C. Regime / volatility | trend-vs-chop, or next-period vol | moderate, useful | gates entries / sizes positions |

**Recommendation: start with A (meta-labeling), add C as features.** Meta-labeling (López de
Prado) keeps the rule for *direction* and uses ML only to decide *whether/how much* — a lower bar
than predicting direction from scratch, and it drops straight into our `confidence` slot (which
already drives ranking + sizing). Pure direction (B) is the seductive trap; we treat it as a
stretch goal that must clear a very high OOS bar.

## 2. Labels — what "correct" means (triple-barrier)
Use **triple-barrier labeling** matched to how we actually trade:
- From each entry signal, look forward: did price hit **+TP** (win=1), **−SL** (loss=0), or
  **time out** (neutral) first?
- For meta-labeling: label = 1 if the rule signal would have hit TP before SL, else 0.
- This labels *outcomes we care about* (our stop/TP structure), not arbitrary N-day returns.

## 3. Features (causal, no lookahead)
Reuse `signals.add_features` and extend — all computed only from data up to time *t*:
- **Trend/momentum:** EMA ratios, MACD, multi-window returns (5/10/20/60d), price vs highs/lows.
- **Mean-reversion:** RSI, Bollinger z-score, distance from moving averages.
- **Volatility/risk:** ATR, realized vol, vol-of-vol, drawdown.
- **Volume:** volume z-score, OBV.
- **Regime:** trend strength (ADX-like), vol regime bucket.
- **Cross-sectional (later):** a symbol's rank vs the universe.
Start **small (~10–15 features)** — more features = more overfitting on ~2k daily bars/coin.

## 4. Models — ensemble + calibration
- **Base learners:** gradient-boosted trees (LightGBM/XGBoost) — strong on tabular; plus a
  logistic-regression baseline (sanity floor) and optionally RandomForest.
- **Ensemble:** average/stack the base learners.
- **Calibration (important):** wrap output in Platt/isotonic calibration so it's a *true
  probability*, **comparable across assets** — this fixes today's "crypto always ranks 1.00"
  problem and makes the ranked competition fair.
- Output per symbol: a calibrated `P(signal works)` → becomes the `confidence` the agent ranks by.

## 5. Validation — the crux (where projects lie to themselves)
- **Purged, embargoed walk-forward CV** (López de Prado): train on past window → test on the next
  unseen window, roll forward; **purge** overlapping labels and add an **embargo** gap so the test
  set can't peek at training outcomes. Overlapping forward-looking labels are the #1 leakage source.
- **Baselines to beat (all OOS, net of fees+slippage):** buy-and-hold · the EMA/RSI rule ·
  a random/coin-flip signal. The model must beat *all three* to matter.
- **Robust plateau, not a spike:** accept a model only if a *range* of hyperparameters works OOS.
- **Metrics:** OOS hit-rate, precision on the "take" class, P&L vs baselines, max drawdown, and
  a stability check across folds/assets.

## 6. Integration (clean, reversible)
- Add a **signal-source abstraction**: `signals.py` (rule) and a new `ml_signal.py` (model) both
  return `{direction, confidence, reason}`. A config/env flag picks the source per account.
- **Meta-labeling wiring:** rule sets `direction`; ML sets `confidence` (and can veto: confidence
  below a threshold → skip). Risk gates + execution are unchanged.
- **Shadow mode first:** run the model live to *log* predictions to the journal WITHOUT trading on
  them, building a real forward track record before it ever sizes a trade.

## 7. Data & infra
- **Training data:** crypto bars already cached (`research/data/`, ~2k/coin). Need equity history
  too (extend `backtest_fetch.py` for stocks/ETFs via Alpaca stock bars or Yahoo).
- **Pipeline:** `research/ml/` — `labels.py`, `features.py`, `train.py` (walk-forward), `evaluate.py`
  (baselines + report), saved model artifacts, and `ml_signal.py` (load model → predict at runtime).
- **Retraining:** periodic walk-forward retrain (e.g., monthly) as new data accrues; versioned artifacts.
- **Deps:** add `scikit-learn` + `lightgbm` (pinned) to a separate `requirements-ml.txt` so the
  live agent stays lean.

## 8. Anti-overfitting safeguards (non-negotiable)
Purged/embargoed CV · small feature set · regularized models · beat 3 baselines OOS · plateau not
spike · costs modeled · **shadow-mode forward test before any live sizing** · willing to conclude
"no edge" and ship nothing.

## 9. Deployment gate
ML sizes real (paper) trades on **account B only**, and only after: (1) beats all baselines OOS in
walk-forward, (2) passes a **shadow-mode forward period**, (3) survives a review for leakage. Until
all three, the rule-based signal keeps running; ML runs in shadow. Account A never uses ML (stays V1).

## 10. Phased roadmap (each an honesty checkpoint)
| Phase | Deliverable | Gate |
|---|---|---|
| **M0** | data + labels (triple-barrier) + baselines coded | baselines reproduce known 0/7, 0/4 |
| **M1** | one LightGBM meta-label model, purged walk-forward eval | **does it beat baselines OOS?** if no → iterate or conclude no-edge |
| **M2** | ensemble + calibration (cross-asset comparable confidence) | calibration curves sane; still beats OOS |
| **M3** | `ml_signal.py` + **shadow mode** (log-only, no trades) | forward predictions logged for weeks |
| **M4** | integrate as account B's signal source (meta-label filter) | only if M1–M3 passed |
| **M5** | monitoring + scheduled retrain | live tracking vs baselines |

## 11. Open questions for you (decide before M0)
1. **Aim:** meta-labeling (recommended) vs pure direction vs regime/vol — or meta-labeling + regime features?
2. **Instruments:** train/deploy ML on crypto first (data cached), stocks, or both?
3. **Model family:** LightGBM as the workhorse (recommended) — OK to add that dependency?
4. **Deploy strictness:** confirm the gate (beat 3 baselines OOS **and** shadow-mode pass) before any live ML sizing.
5. **Willingness to ship nothing:** confirm we treat "no OOS edge found" as an acceptable, honest outcome.
