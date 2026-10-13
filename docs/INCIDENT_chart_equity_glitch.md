# Incident: chart equity glitch — Alpaca's hourly feed double-counts cash events

**This is a DISPLAY bug, not a money bug.** Real account equity is always correct (the
headline cards read it straight from the account endpoint). Only the equity *chart* was
affected, because the chart is built from Alpaca's **intraday/hourly** portfolio-history
feed, which miscalculates equity around large cash movements.

## The pattern

Alpaca's **hourly** portfolio history (`timeframe=1H`, both `continuous` and `market_hours`
reporting) **double-counts a large cashflow on the day it settles** — adding the cash amount
on top of real equity, which roughly inflates (or doubles) the line for that day. Alpaca's
**daily** feed (`timeframe=1D`) is NOT affected and stays correct.

## Seen twice

**1. Account B — funding-date glitch (first seen ~Oct 9, 2026)**
- B was funded with $100k ~28 days earlier. When the hourly window reached back to that
  initial deposit, Alpaca added the $100k again → B's line jumped to ~$207k (real ~$107k).
- Trigger: the query window straddling the **account's funding deposit**.

**2. Account A — option-exercise glitch (seen Oct 12–13, 2026)**
- On Oct 9 A's SPY $763 call auto-exercised, spending $76,300 to buy 100 shares (see
  `INCIDENT_option_exercise.md`). On the next trading day (Oct 12) the hourly feed
  double-counted that $76,300 → A's hourly equity read **~$179,000 all day**.
- Proof of the true value for Oct 12:

  | Alpaca feed | Oct 12 value | Correct? |
  |---|---|---|
  | Hourly — continuous | ~$179,000 | ❌ |
  | Hourly — market_hours | ~$179,000 | ❌ |
  | **Daily — 1D** | **$102,711** | ✅ |

- Trigger: a large **option exercise** cashflow.

## Guards

**Layer 1 — sanity band (in place since the B glitch).** Both the dashboard chart and the
collector drop any equity point outside [0.3×, 1.5× ACCOUNT_START] = [$30k, $150k]. This
caught both glitches and kept false numbers off the chart / out of the archive. Limits:
it only *rejects* bad points (leaving a gap), and a sub-$150k inflation could slip through.

**Layer 2 — daily truth-anchor + gap-fill (added for the A glitch, "Option 1").** The chart
now also fetches Alpaca's always-correct **daily (1D)** feed and uses it to (a) reject any
hourly point that deviates more than a tolerance from that day's true daily value — catching
glitches of *any* size, not just >$150k — and (b) fill the resulting gap with the correct
daily value. This makes the chart self-heal around any future deposit, exercise, or cash
event. See `dashboard.py` `build_chart`.

## Key takeaways

- Your money was never wrong — this is purely the chart's data source.
- Root enabler for glitch #2 was the Oct 9 auto-exercise; the preventive `CLOSE_BEFORE_EXPIRY`
  rule now stops future exercises, so this particular trigger shouldn't recur on A.
- The daily feed is the reliable source of truth; the hourly feed is for intraday/weekend
  detail only and must always be validated against it.
