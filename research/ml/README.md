# ML phase — index & honest conclusion

Goal: find something ML could add to the agent. We tested it **rigorously** (out-of-sample,
walk-forward, robustness) and reported the truth — including when the truth was "no edge."

## Bottom line
> Across **direction, exits, and sizing**, nothing beat the simple fixed baseline out-of-sample.
> The **only** thing adopted is **L1 (calibration)** — a *fairness* fix (no performance claim).
> The agent stays otherwise simple: fixed exits, fixed sizing. That rigor is the deliverable.

## What was tried, and the verdict
| Idea | What it hoped to do | Test | Verdict |
|---|---|---|---|
| **M1 · meta-label model** (LightGBM) | predict which rule-signals win | purged walk-forward | ❌ no OOS edge (15.8% vs 33% breakeven) |
| **L3 · ATR-scaled exits** | fit the finish line to each asset | plateau + OOS | ❌ not robust (lucky cell; lost OOS 3/4) |
| **L2 · vol-sizing** | shrink bets in storms → smaller drawdowns | plateau + OOS | ❌ consistent in-sample, failed OOS |
| **L1 · calibration** | fair cross-asset ranking (comparable confidence) | fairness (no edge claim) | ✅ **ADOPTED on account B** |

## Files
- `features.py` · `labels.py` — causal features + triple-barrier meta-labels (M0)
- `m0.py` — builds the dataset (base rate: 16% of rule-signals hit +30% before −15%)
- `m1.py` + `M1_RESULT.md` — the walk-forward meta-label test (FAIL)
- `experiment.py` + `LEVERS_RESULT.md` — L1/L2/L3 head-to-head
- `l3_robustness.py` · `l2_robustness.py` + `ROBUSTNESS_COMPARISON.md` — the robustness gates (both fail OOS)
- `datasets/` — generated (git-ignored); rebuild with `m0.py`
- design docs live one level up: `../DESIGN_ml_phase.md`, `../ML_PHASES_detail.md`, `../DESIGN_ml_risk_pivot.md`

## What shipped
**L1 only** — `signals.calibrated_confidence()` + ranking in `agent._ranked_signals` (account B,
confidence-order). It re-scores each signal as its **percentile within that asset's own recent
history**, so options and crypto compete evenly for the 6 slots. Account A is untouched (V1).

## To reproduce
```bash
.venv/bin/pip install -r requirements-ml.txt   # scikit-learn, lightgbm (offline research only)
.venv/bin/python research/ml/m0.py             # build dataset
.venv/bin/python research/ml/m1.py             # meta-label walk-forward (FAIL)
.venv/bin/python research/ml/experiment.py     # L1/L2/L3 comparison
.venv/bin/python research/ml/l3_robustness.py  # L3 robustness (FAIL)
.venv/bin/python research/ml/l2_robustness.py  # L2 robustness (FAIL OOS)
```
