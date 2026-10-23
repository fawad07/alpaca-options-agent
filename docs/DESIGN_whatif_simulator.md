# Design: "What-If" simulator (dashboard panel)

**Status: DESIGNED, not built.** A standalone dashboard tool with two modes — a
*contribution simulator* (real past returns) and a *forward scenario / range* (a cone of
outcomes, never a prediction). Fully independent of the trading agent: it only reads
recorded numbers, places no trades, changes no account. The agent never knows it exists.

## Guiding principle
> **It shows the RANGE of what could happen. It never predicts the one thing that will.**
> No "in X days you'll have $Y." The ML phase already proved this strategy has no
> predictive edge (M1 OOS precision 15.8% vs 33.3% breakeven), so a return-*predictor* is
> both dishonest and empirically wrong here. A simulator/range is the honest alternative.

---

## Mode 1 — History (contribution simulator)

Applies the chosen account's **real past returns** to a regular-deposit schedule.

- **Logic:** the live accounts take no deposits, so every move in their equity is pure
  investment return. Read the account's real equity series → period returns → run a
  parallel balance that (a) grows by those real returns and (b) adds a contribution on
  schedule. Track *Contributed* (your money in) vs *Value* (what it grew to) separately;
  the gap = investment gain.
- **Controls:** Returns from [A|B] · Start $ (defaults to the selected account's **last
  recorded equity** — A ≈ $102k, B ≈ $108k today — editable) · Add $ · Every [2wk / 1mo /
  2mo / 3mo].
- **Output:** two-line chart (Value vs Contributions over the real time window) +
  summary cards (Contributed / Value / Investment gain $ and %).

## Mode 2 — Forward scenarios (range / cone)

Projects the contribution curve **into the future** as a spread of outcomes — NOT a line.

- **The honest split (key design decision):**
  - **Drift (average return) = a user-set assumption, default conservative (0% or a number
    you type).** We do NOT estimate average return from the real history — the sample is
    tiny (~weeks) and the project's whole finding is that there is *no proven edge*, so
    claiming an average return would be dishonest. The user owns that assumption.
  - **Spread (volatility) = from the account's REAL return history.** Volatility is the one
    thing we *can* legitimately estimate from real data. So the cone's width reflects how
    bumpy this account actually is.
  - Net: "Even assuming a modest/zero average return, here's how widely outcomes swing —
    including losing ones."
- **Engines — build BOTH, shown side by side for comparison:**
  1. **Formula (±band):** an analytic ±σ√t band around the drift — a smooth, symmetric
     funnel. Simple, fast, idealized.
  2. **Monte Carlo (1,000 runs):** simulate many future paths (each day: drift + a random
     shock sized by real volatility; add contributions on schedule), then take percentiles
     (e.g. 10th / 50th / 90th) at each future point — realistic, captures contribution
     timing and uneven streaks.
  The two cones render in two charts side by side (stack on mobile), plus a comparison
  table of each method's bad / middle / good value at the horizon. Showing both is more
  honest and educational — where they agree builds confidence, where they diverge is itself
  informative. The Monte Carlo part is the real work; the formula band is cheap to add once
  its plumbing exists.
- **Controls:** Volatility from [A|B] · Start $ (defaults to that account's **last recorded
  equity**, editable) · Add $ · Every · Horizon [1/3/5/10 yr] · Assumed avg return [default 0%].
- **Output:** a **cone** — median line + shaded band between a good case and a **losing**
  case — plus a range summary ("in 5 yr: typically ~$X, range $A (bad) to $B (good)").
  The downside band is shown prominently, never hidden.

---

## How it's incorporated in the dashboard

One new panel near the bottom (below the real account numbers, so it's never confused
with them), with a mode toggle **[ History | Forward ]**. Shared contribution controls;
Forward adds horizon + assumed-return. Chart.js (already loaded) draws the lines / cone.
Every view is labelled **"Model — not a prediction. Outcomes include losses. This
strategy has no proven edge."**

```
┌─ What-If  (model — not a prediction) ───────────────────────────┐
│  [ History | Forward ]   Account [B ▾]  Start [$100,000]         │
│  Add [$2,000]  Every [1 mo ▾]   (Forward: Horizon [5 yr ▾]       │
│                                  Assumed avg return [0 %])       │
│                                              [ Run ]             │
│   (History: Value vs Contributions lines)                       │
│   (Forward: median line + shaded good→bad cone)                 │
│   Summary cards + downside clearly shown                        │
└─────────────────────────────────────────────────────────────────┘
```

## Pieces (all isolated)

| Piece | Job |
|---|---|
| `simulator.py` | Pure functions `simulate_history(...)` and `simulate_forward(...)`. Read only recorded equity history. No trades, no account mutation. |
| `/api/simulate` route | Takes mode + control values, returns the computed series/cone + summary JSON. |
| Dashboard panel | Mode toggle + controls + Chart.js chart + summary + honesty labels. |

**Independence:** standalone module + route + panel, reads only saved numbers, never calls
the agent or places a trade. Built on its own branch; `main` and the live autonomy
untouched — same isolation as the explainer assistant.

## Honest caveats (surfaced in the UI)
- **Short history** — History mode spans only as much as the real track record exists
  (~weeks today); it enriches automatically as the record grows.
- **Returns-scale assumption** — assumes similar % returns at a different size (fair for
  modest sums).
- **Forward = assumption + real volatility, not a forecast** — the average return is a
  number the user chooses; only the spread comes from real data. Losses are always in view.

## Open decisions before build
1. ~~Default Start amount~~ — **DECIDED:** defaults to each account's **last recorded
   equity** (A and B start from their own current value; still editable).
2. ~~Forward engine~~ — **DECIDED:** build **BOTH** (formula ±band + Monte Carlo), shown
   side by side with a comparison table, so the two methods can be compared directly.

**Build status: HELD** — recorded as a design; not building yet (user, 2026-10-22).
Spec is now complete (start = last recorded equity; both forward engines side by side).
