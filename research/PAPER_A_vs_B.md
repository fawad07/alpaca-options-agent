# No Demonstrable Edge, Honestly Measured
### A 79-day paper-trading comparison of an options-only and a multi-asset autonomous trading agent

**Risk Gate Project — Working Paper RG-2026-01 · v1**
F. Aleem · built for the Alpaca × lablab.ai agents hackathon
Preprint, not peer-reviewed · compiled 27 November 2026 · **paper (simulated) capital only**

> Interactive version (hover-able equity figure): published artifact `risk_gate_paper.html`.
> This Markdown copy is the version-controlled record; every number is drawn from the project's
> own logs (`stats_history*.csv`, `activity*.csv`).

---

## Abstract

Two autonomous trading agents share one codebase, one rule-based signal, and one risk-gate layer, and differ only in instrument mandate. **Account A** trades long U.S. equity options only (5 concurrent slots); **Account B** trades the same options plus long spot crypto (6 slots). Both began at a nominal $100,000 of Alpaca paper capital and ran unattended on a cloud scheduler from mid-September to 27 November 2026.

Over the 79-day window, Account A returned **+9.56%** and Account B **+5.10%**. The headline gap reverses under scrutiny: B closed trades at a **60.7%** win rate versus A's **42.5%**, banked more realized profit ($8,281 vs $5,448), and was far less volatile (22% vs 32% annualized). A paired *t*-test on daily returns finds the A−B difference indistinguishable from zero (*t* = 0.45), and neither account's return is significantly different from zero. Of 31 positions B opened, **exactly one** was crypto — options saturated its 6 slots on 91% of runs, starving the asset class the account existed to test. We conclude that over this horizon the system shows **no measurable edge**, that A vs B is a quasi-experiment confounded by five simultaneous design differences, and that the crypto strategy remains essentially untested. The contribution is the method and the discipline of reporting a null result honestly, not a profitable strategy.

**Keywords:** autonomous trading agents · options · cryptocurrency · risk management · A/B evaluation · null result · algorithmic trading

---

## 1. Introduction

Most public write-ups of algorithmic trading report the runs that worked. This paper does the opposite on purpose: it documents a system built around a single premise — that it has *no proven edge* — and measures two deployments of it with enough rigor to say so quantitatively. The project ("Risk Gate") reads daily price history, forms a rule-based directional view, passes every intended trade through explicit risk gates, and places orders through a broker API on paper capital.

Two accounts ran side by side as a natural A/B test. Account A is the pure research arm: options only, unchanged from v1, so its record stays clean. Account B is the experimental arm: the same agent with cryptocurrency added, to ask whether a second 24/7 asset class improves results. Both trade real market data and place real (paper) orders; only the capital is simulated.

We ask three questions. **(Q1)** Does either account produce returns distinguishable from chance? **(Q2)** Does adding crypto (B) beat options alone (A)? **(Q3)** If they differ, can the difference be attributed to the crypto mandate? The short answers — no, no, and no — are developed below.

## 2. System and methods

**2.1 Signal.** For each symbol the agent fetches daily OHLC bars and computes EMA(20), EMA(50), RSI(14), and ATR. Rule: uptrend (EMA20 > EMA50) with RSI < 72 → `bull`; downtrend with RSI > 28 → `bear`; else `neutral`. Confidence scales with the EMA gap, gated at ≥ 0.55. Options map bull → long call, bear → long put; crypto is long-only spot (bull signals only).

**2.2 Risk gates.** Every candidate clears all gates before placement: 2%-of-equity per-trade risk cap; concurrent-position cap (5 for A, 6 for B); 5%-per-day loss limit; defined-risk only (buy options, never sell naked); days-to-expiry window 14–60 with forced close inside 2 days. Crypto carries a broker-held −15% stop and an agent-managed +30% take-profit.

**2.3 Sizing and execution.** Options are sized so premium paid (a long option's max loss) stays within the 2% cap. Crypto notional is min(2%-risk/stop, 15% of equity). Sizing uses *working equity* (actual minus simulated withdrawals). Orders route through the Alpaca MCP server; the deployment is hard-wired to the paper endpoint.

**Honesty constraint (by design).** The system shows facts and does arithmetic; it never emits a recommendation, a safe/unsafe verdict, a price prediction, or a claim of edge. This paper inherits that stance.

## 3. Experimental design

The arms share the signal, gates, sizing, broker, and scheduler, and differ in five respects. Because more than one variable changes, A vs B is a **quasi-experiment**, not a clean single-variable test (§7).

**Table 1. Controlled vs. differing factors.**

| Factor | Account A | Account B | Same? |
|---|---|---|---|
| Signal & indicators | EMA/RSI rule | EMA/RSI rule | ✓ same |
| Risk gates | full set | full set | ✓ same |
| Starting capital | $100,000 | $100,000 | ✓ same |
| Asset classes | options only | options + crypto | ✗ differs |
| Concurrent slots | 5 | 6 | ✗ differs |
| Symbol universe | 7 equities | 8 equities + 4 coins | ✗ differs |
| Fill ordering | watchlist order | strongest-signal-first | ✗ differs |
| Run schedule | market hours | every ~20 min, 24/7 | ✗ differs |

Window: 2026-09-09 (A) / 2026-09-12 (B) → 2026-11-27, 79 calendar days. The window closed when B was repurposed to crypto-only, formally ending the comparison.

## 4. Results

**4.1 Performance and risk.** Account A wins on total return and Sharpe, but with a *minority* win rate and higher volatility — the signature of long-option convexity (many small losses paid for by a few large wins). Account B was calmer and hit more often, yet trailed on total return and holds its open positions at a loss.

**Table 2. Performance and risk (full window).** Daily stats from end-of-day equity; annualization ×√252; Sharpe at rf = 0.

| Metric | Account A | Account B | Edge |
|---|---:|---:|---|
| Ending equity | $109,563 | $105,102 | A |
| Total return | **+9.56%** | +5.10% | A |
| Realized P&L | $5,448 | **$8,281** | B |
| Unrealized (open) | +$4,115 | −$3,179 | A |
| Mean daily return | +0.217% | +0.088% | A |
| Daily volatility | 2.01% | 1.38% | B |
| Annualized volatility | 32.0% | 22.0% | B |
| Annualized Sharpe | **1.71** | 1.00 | A |
| Max drawdown | −10.26% | −9.27% | B |
| Best / worst day | +7.46% / −5.54% | +4.07% / −4.13% | — |

**4.2 Trade statistics.** B's higher hit rate sits against A's higher payoff per winner — two routes to a similar place.

**Table 3. Activity and trade statistics.**

| Statistic | Account A | Account B |
|---|---:|---:|
| Agent runs logged | 152 | 395 |
| Positions opened | 48 | 31 |
| Positions closed | 40 | 28 |
| Win / loss (closed) | 17 / 23 | 17 / 11 |
| Win rate | 42.5% | **60.7%** |
| Runs blocked by gates | 240 | 1,182 |
| Runs at full capacity | 97% | 91% |
| **Crypto positions opened** | 0 | **1** |

**4.3 The crowding-out finding.** The last row of Table 3 is the study's most consequential number. Account B existed to test crypto. Over 395 runs it opened **one** crypto position (a single LTC buy on 13 October, since closed); the other 30 were options. Options signals filled all six slots on 91% of runs, so crypto almost never had a slot. **B's +5.10% is, in practice, an options result** — the second asset class it was built to evaluate was starved.

**Table 4. Option contracts bought, by underlying and type.**

| Underlying | A — calls | A — puts | B — calls | B — puts |
|---|---:|---:|---:|---:|
| AAPL | 18 | — | 15 | — |
| SPY | 14 | — | — | 2 |
| NVDA | 3 | 3 | 7 | 1 |
| MSFT | 7 | — | 4 | — |
| QQQ | 2 | 4 | — | 3 |
| AMZN | 2 | 2 | — | — |
| GOOGL | — | — | — | 4 |
| TSLA | 1 | 1 | 1 | — |

**Equity path (context).** B peaked near $110.7k in early October and gave most of it back; A fell to $92.1k on 4 November before rallying to a $110.2k high on 21 November. They end within $4.5k of each other. (See the artifact for the hover-able daily equity figure.)

## 5. Statistical analysis

- **A − B difference (paired, 50 common trading days):** mean daily difference +0.107%, *t* = 0.45 (*p* ≈ 0.66). **Not significant.**
- **Is A's mean daily return > 0?** *t* = 0.81 (*p* ≈ 0.42). Not significant.
- **Is B's mean daily return > 0?** *t* = 0.58 (*p* ≈ 0.56). Not significant.
- **A–B daily-return correlation:** 0.60 — both run the same options engine; they are not independent bets.

Across 79 days neither account earned a return distinguishable from zero, and the +4.46-point spread between them is within noise. The equity curves look like skill; the statistics say we cannot yet tell skill from luck. This is the central result, consistent with the system's founding premise of no proven edge.

## 6. Discussion

**Convexity vs. consistency.** A and B reached a similar place by opposite routes. A loses more often than it wins (42.5%) yet earns more, because a long option's loss is capped at its premium while its gain is open-ended. B wins more often (60.7%) and banks more realized cash, but with smaller swings and open positions currently underwater. Neither pattern is "better"; the sample is too small to prefer one.

**The crypto question is unanswered, not answered.** B could not test crypto because options monopolized its slots. The right reading is not "crypto didn't help" but "crypto was never given the chance to." Any future test must remove the competition for slots — the motivation for the follow-on work (§8).

**Why report a null.** A +9.56% headline is publishable colloquially and meaningless scientifically. Reporting it without the significance test would overstate the system by exactly the amount the test removes. The value here is a reusable, honest evaluation harness and a documented null.

## 7. Limitations and threats to validity

- **Quasi-experiment, not controlled.** Five factors change between arms at once (Table 1); even a significant gap couldn't be attributed to crypto alone.
- **Small sample.** 28–40 closed trades and ~79 days are far too few for statistical power; confidence intervals are wide.
- **Single regime.** One stretch of market history; untested through a sustained bear market, a volatility shock, or a crypto drawdown.
- **Paper fills.** Simulated execution understates slippage, spread, partial fills, and market impact; transaction costs are not modeled.
- **Open-position marks.** Total-return figures include unrealized marks (A +$4,115, B −$3,179); realized results differ and will move as positions close.
- **Window end not pre-registered.** The window closed for an operational reason (B's repurposing), not by a pre-set stopping rule.

## 8. Conclusion and future work

Two agents sharing one engine and differing in instrument mandate returned +9.56% (options only) and +5.10% (options + crypto) over 79 days of paper trading. The difference is not statistically significant, neither return is distinguishable from zero, and the crypto arm's defining asset class traded only once. Honest summary: **no demonstrable edge**, and the crypto hypothesis remains untested.

The follow-on work addresses the crowding-out directly. Account B has been repurposed to **crypto-only** with the same six slots, so the crypto strategy finally runs without options competing for capacity — a continuously-updating paper record intended to characterize the strategy before any real-money deployment (Account C). A signal-frequency probe over two years of history estimates at least one of the four coins carries a buy signal on ~43% of days, so the crypto arm should, for the first time, be active enough to measure. Whether it has an edge is an open empirical question.

## 9. Data and reproducibility

Every number is drawn from the project's append-only logs: per-account daily statistics (`research/stats_history*.csv`), decision journals written on every run (`activity*.csv`), and hourly equity snapshots (`research/equity_hourly*.csv`). The agent, gates, and signal are rule-based and open in the repository. No figure is hypothetical; estimates and marks are labeled as such.

**References / data sources**
1. Risk Gate Project — autonomous options & crypto agent, risk-gate layer, A/B deployment. Project repository, 2026.
2. Decision journals and daily statistics, Accounts A and B, 2026-09-09 → 2026-11-27.
3. Crypto-signal frequency probe, 2-year daily history of BTC/ETH/SOL/LTC (`research/probe_crypto_signals.py`).
4. Alpaca Markets paper-trading API and MCP server (execution venue; simulated capital).

---

*Preprint, not peer-reviewed. All capital is simulated (paper). Nothing herein is investment, financial, or tax advice, a recommendation, or a claim of edge. Past simulated performance does not indicate future results. Prepared with AI assistance; the author is responsible for all content.*
