# Analysis: What A & B actually tell us about Account C (crypto-only)

**Date:** 2026-11-22. **Purpose:** Flag 2 — pull the real A/B track record and the agent's
buy/sell history, and form an honest, testable hypothesis for the live crypto Account C.

**Sources (honest note):** the Discord pings are one-way (agent → Discord), so they can't be
read back. The *same* buy/sell records that generated each ping are in the decision journals
(`activity.csv` = A, `activity-B.csv` = B), plus the live account positions and `compare.py`.
That's what this uses. Data as of the dates shown; both accounts keep running.

---

## 1. Headline numbers (both started $100,000)
| | A (options only) | B (options + crypto) |
|---|---|---|
| Equity | $110,189 | $107,427 |
| Return | **+10.19%** | **+7.43%** |
| Open now | 5 options | 5 options + **dust** |

A (pure options) is *ahead* of B. Hold that thought.

## 2. THE finding: B barely traded crypto at all
Over **382 runs across ~2.5 months (Sep 12 → Nov 22)**, Account B — the "options + crypto"
account — opened:
- **~30 option trades** (AAPL 15, NVDA 7+1, MSFT 4, GOOGL put 4, QQQ 3, SPY 2, TSLA 1 contracts), and
- **1 crypto trade** — a single LTC buy on 2026-10-13, since closed.

Its *current* "1 open crypto position" is **dust**: SOL `qty 0.00000001`, market value **$0.000001**.
Effectively zero. The trade log (`logs/trades.jsonl`) shows **0** crypto entries. So:

> **B's +7.43% is an _options_ result. The crypto strategy contributed essentially nothing,
> because it almost never traded.**

## 3. Why crypto never traded — options crowded it out
B shares **6 slots** between options and crypto, filled strongest-signal-first. The data:
- B was at **full capacity (6/6 slots) in 347 of 382 runs — 91%.**
- In **278 runs**, signals were ranked but **none opened, every time citing "cap full."**
- The slots were full of **options**. The one crypto entry (LTC) slipped in on a run that had
  just *"closed 2 positions,"* i.e. only when options momentarily freed a slot.

> Options signals were frequent/strong enough to occupy all 6 slots almost always, so the
> crypto logic was starved — it rarely got a slot to act on, win or lose.

## 4. What this means for Account C (the important part)
**Account C is _not_ "Account B's crypto, scaled up."** It's the opposite situation:
- C has **no options** competing, so crypto gets **all 6 slots to itself** — for the first time.
- C will therefore exercise the crypto strategy **far more than B ever did** (B ran it ≈once).
- That strategy is **almost entirely untested.** The A/B experiment, for all its data, has
  barely any crypto evidence in it.

So the honest status is worse than "Flag 2: the record is just short." It's: **the specific
strategy Account C would run has essentially no track record at all.** The part of the system
that's clearly working (options) is *not* the part C uses.

## 5. Hypothesis for Account C (to test on PAPER first)
A hypothesis is a claim we can check, not a prediction we trust. For C's paper dress rehearsal:

**H1 — Activity.** With options gone, C's crypto signal (long-only; EMA20>EMA50 + RSI in band,
on BTC/ETH/SOL/LTC) will fire and fill slots *much* more often than B's ≈1 trade — likely
several open positions at a time. *Measure:* avg slots used, trades/week.
> **First data point (`research/probe_crypto_signals.py`, 2y):** each coin would fire a BUY on
> ~26–32% of days; on **~43% of days at least one coin has a BUY** (avg 1.1 of 4). So C would
> trade *meaningfully more than B* (whose slots were full of options) — but it's not a constant
> stream, and right now all four are neutral/bear (nothing to buy). Partly supports H1, and the
> idle current state previews H2.

**H2 — Regime-dependence.** Because the strategy is long-only trend-following, C will tend to
**make money when the coins trend up and bleed in chop/downtrends** (buying strength, stopped
out repeatedly when there's no trend). *Measure:* P&L split by up vs sideways/down periods.

**H3 — Protection works.** The broker `stop_limit` (−15%) and agent take-profit (+30%) behave
on real crypto fills with no OCO. *Measure:* every open position has a resting stop; exits hit
near the intended levels.

**H4 — Caps hold.** The new live caps (≤$100/buy, ≤$300/day — now enforced, `test_live_c_caps.py`)
clamp real sizing end-to-end. *Measure:* no buy > cap, daily buys halt at the cap.

**Decision rule (honest):** go live **only if** paper-C, over a meaningful number of *crypto*
trades across at least one up and one down stretch, shows the strategy does something
sensible (positive or at least controlled-loss expectancy, protection working). If paper-C
mostly chops and bleeds, that's the answer — don't fund it.

## 6. Bottom line
- A and B prove the **options** gates and plumbing work. They **do not** validate crypto.
- Account C would run the **least-tested** component of the whole system.
- Therefore the **paper dress rehearsal of C is not a formality — it is the first real test**
  of C's actual strategy, and it must come before any real money.
- **Reminder: Account C is not safe to run live yet.** Caps are enforced (Flag 1 done), but
  the crypto strategy itself is unproven (this analysis) and the end-to-end paper rehearsal
  (go-live step 3) hasn't happened.
