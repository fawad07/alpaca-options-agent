# Incident: Account A option auto-exercised into stock (Oct 9, 2026)

## What happened — in plain terms

Account A is meant to be an **options-only** account. On **Oct 9, 2026** one of its call
options expired while it was "in the money" (the stock had risen above the option's strike
price). When that happens, the broker **automatically exercises** the option — it uses the
account's cash to buy 100 real shares of the stock, per contract. The agent never *chose*
to buy that stock; it was handed to the account because the option was left to expire.

**The exact event (from Alpaca account activities):**
- `SPY261009C00763000` — a SPY **$763 call expiring Oct 9** — expired in-the-money.
- It was auto-exercised → the account **bought 100 shares of SPY at the $763 strike**.
- Cash out: **−$76,300**. The 100 shares landed in the account as a `us_equity` position.

## Before vs after

| | Before (≈ Oct 9, pre-exercise) | After (Oct 11) |
|---|---|---|
| **Equity** | ~$102,340 | $102,601 |
| **Cash (deployable)** | ~$92,945 | **$16,645** |
| **Holdings** | options only (pure) ✅ | 100 SPY shares ($77,857) + 4 options ($8,099) ❌ |
| **Cash as % of equity** | ~91% | **~16%** |

**Key point:** this was **not a loss** — equity was essentially unchanged. The damage was to
**flexibility**: ~$76,300 of freely-deployable cash got **locked into a single stock
position** the agent doesn't manage. Deployable cash fell ~82% (from ~$93k to ~$17k), so the
agent can open far fewer new option trades, and Account A is no longer a "pure" options
account — which muddies the A-vs-B research.

## Root cause

The options exit logic only closed a position on **take-profit (+50%)** or **stop-loss
(−50%)**. There was **no time-based exit** — so an option that drifted sideways and never hit
either threshold sat untouched until expiration. If it expired in-the-money, auto-exercise
followed. Standard options practice is to *never* let options expire; you close them a few
days early.

## Fix applied — Tweak #1: close before expiry

Added a **time-based exit** to the options handler: any option within
`CLOSE_BEFORE_EXPIRY_DAYS` (default **2**) of expiration is closed (sold) regardless of
profit/loss. This captures whatever value is left **and** sidesteps auto-exercise entirely,
for both Account A and Account B. See `config.py` (`CLOSE_BEFORE_EXPIRY_DAYS`) and
`instruments/options.py` (`manage_exits`).

## Not done (deliberate)

The 100 SPY shares already sitting in Account A were **left in place** — not sold — per the
decision to only add the preventive rule for now. A future "sell any unexpected stock"
cleanup rule (Tweak #2) remains an option if we want to un-stick that cash and restore A's
purity; see the discussion that produced this doc.
