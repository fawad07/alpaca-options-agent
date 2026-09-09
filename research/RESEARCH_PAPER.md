# Risk Gate: Discipline over Edge — An Honest, Risk-Gated Autonomous Options-Trading Agent

**Author:** Muhammad Fawad Aleem
**Context:** Alpaca × lablab.ai — AI Trading Agents Hackathon, 2026
**Artifact:** `github.com/fawad07/alpaca-options-agent` (MIT)
**Paper account:** PA327FXF8G6D · **Live paper window analyzed:** 2026-09-01 → 2026-09-09
**Status of numbers:** every figure in this paper is taken from the agent's own decision journal (`activity.csv`) and the Alpaca account order history, not from estimates.

---

## Abstract

We present **Risk Gate**, an autonomous options-trading agent that executes on a live (paper) Alpaca brokerage account entirely through the Model Context Protocol (MCP). The central claim of this work is **not** that the agent possesses a profitable predictive edge — we demonstrate, and openly report, that it does not. In out-of-sample testing the directional signal beat a naive buy-and-hold benchmark on **0 of 7** instruments. Instead, the contribution is a **falsifiable engineering thesis**: that a retail trading agent can be made *disciplined, transparent, and safe* independent of whether its signal is profitable, and that this discipline is measurable in live trading. Over a nine-day live paper deployment the agent placed **13 option orders** (9 entries, 4 exits) across **27 market-hours evaluation cycles**, and its risk layer **refused 117 otherwise-actionable buy signals** to stay within a hard 5-position cap. At the moment of hackathon submission (2026-09-03) the account stood at **+1.82%** ($101,823.43). Six trading days later it stood at **−1.30%** ($98,704.15). This reversal — same agent, same rules, opposite outcome — is the paper's most important empirical result: it is a live, unplanned demonstration of the very thesis the agent was built to argue, namely that a one-week options P&L is dominated by luck, and that the durable, reportable value of such a system lies in its **risk control and honesty**, not in its returns.

---

## 1. Introduction

### 1.1 Motivation
Retail interest in "AI trading bots" is enormous, and the marketing around them is almost uniformly dishonest: a backtest is shown, a steep equity curve is displayed, and profitability is implied. The failure mode is well known to practitioners but invisible to newcomers — a strategy tuned until it looks good on historical data has usually *memorized* that data rather than learned anything generalizable. When deployed forward, the edge evaporates.

This project began from a personal history of exactly that failure. Earlier prototypes (a crypto scalping strategy; a signal-production pipeline; an ML trading pipeline) each produced attractive in-sample results and each failed to generalize. Rather than treat this as an embarrassment to hide, Risk Gate treats it as the **premise of the design**.

### 1.2 The problem statement
Can a trading agent be **worth building and worth trusting** even when it has *no proven predictive edge*? We argue yes, provided success is redefined away from returns and toward three measurable properties:

1. **Transparency** — every decision is a simple, explainable rule and is logged.
2. **Risk control** — hard, pre-trade limits make catastrophic loss structurally impossible within the paper account.
3. **Honesty** — the system's real (limited) edge is *measured out-of-sample and reported*, never oversold.

### 1.3 Contributions
- **C1.** A fully autonomous options agent that trades a live brokerage (paper) account *through MCP*, with no human in the loop during market hours.
- **C2.** A **pre-trade risk-gate architecture** whose refusals are logged and quantifiable (117 signal-level blocks over 9 days).
- **C3.** A **decision journal** that records *every* evaluation cycle — trades, no-signal passes, risk-blocked passes, and errors — producing a complete audit trail.
- **C4.** An **out-of-sample honesty protocol** that measures the signal against buy-and-hold and publishes the negative result (0/7).
- **C5.** An **unintended natural experiment**: continued live operation past submission produced a +1.82% → −1.30% swing that empirically supports the "luck dominates short-horizon P&L" thesis.

---

## 2. Background and Related Work

### 2.1 Market efficiency and the difficulty of edge
The Efficient Market Hypothesis (Fama, 1970) holds that prices already incorporate available information, so consistently beating a passive benchmark net of costs is difficult. One need not accept EMH in its strong form to accept its practical corollary for a solo retail developer: a simple momentum rule on daily bars of mega-cap equities is extraordinarily unlikely to contain a durable, exploitable edge.

### 2.2 Backtest overfitting
The gap between in-sample and out-of-sample performance is the central hazard of quantitative strategy design. Bailey, Borwein, López de Prado, and Zhu formalized the *probability of backtest overfitting* — the likelihood that a strategy selected for its in-sample performance underperforms out-of-sample. López de Prado (*Advances in Financial Machine Learning*, 2018) catalogues the mechanisms: multiple testing, selection bias, and leakage. Risk Gate's honesty protocol (§5.1) is a deliberate, minimal instantiation of the recommended remedy: **hold out data the strategy never saw, then report whatever that data says.**

### 2.3 Options as defined-risk instruments
A long option (a bought call or put) has a maximum loss equal to the premium paid. This property is load-bearing for Risk Gate's risk model: because downside is bounded and known at entry, position sizing reduces to *"buy a quantity whose total premium ≤ 2% of equity,"* and the agent can guarantee — structurally, not probabilistically — that no single trade can lose more than 2% of the account. The signal logic (EMA/RSI) derives from classical technical analysis; the RSI indicator is due to Wilder (*New Concepts in Technical Trading Systems*, 1978).

### 2.4 Agentic execution and MCP
The Model Context Protocol (MCP) exposes tools to an AI agent through a standard interface. Alpaca's official `alpaca-mcp-server` publishes 72 such tools over the brokerage API. Risk Gate is an MCP *client*: it drives the broker by calling tools (`get_account_info`, `get_option_contracts`, `get_option_snapshot`, `place_option_order`, `get_all_positions`, `close_position`, `get_orders`). This is the "AI drives the broker" pattern, and it is what makes the system an *agent* rather than a script with hard-wired API calls.

---

## 3. Hypothesis

We state two falsifiable hypotheses.

- **H1 (null-edge).** The agent's directional signal does **not** produce risk-adjusted returns superior to a naive buy-and-hold benchmark out-of-sample.
- **H2 (buildable discipline).** Independent of H1, the agent can be constructed so that, in live trading, it (a) never exceeds its stated risk limits, (b) logs a complete and honest record of every decision, and (c) contains losses via mechanical exits.

The scientific posture is unusual but deliberate: **we predict our own signal will fail (H1), and we design the system so that this failure does not compromise its value (H2).** The paper tests both.

---

## 4. System Design

### 4.1 Architecture overview
The pipeline for a single evaluation cycle is:

```
market data → feature engineering → directional signal → [RISK GATES] → contract selection
    → premium quote → position sizing → order placement (MCP) → exit management → journal
```

Every arrow is instrumented; the bracketed **risk gates** are the component that can veto a trade at any point.

### 4.2 Data layer (`data.py`)
Daily OHLC bars for each universe symbol are retrieved and passed to the feature stage. Options chains, live quotes, positions, and account state are read at run time through MCP.

### 4.3 Signal engine (`signals.py`)
For each symbol the agent computes:
- **Trend:** the 20-period EMA versus the 50-period EMA. EMA₂₀ > EMA₅₀ ⇒ bullish; EMA₂₀ < EMA₅₀ ⇒ bearish.
- **Momentum filter:** the 14-period RSI (Wilder). Overbought/oversold extremes suppress entries in the direction of exhaustion.
- **Confidence:** a scalar in [0,1] scaling with trend strength; a trade requires confidence ≥ **0.55**.
- **Mapping:** bullish ⇒ buy a **CALL**; bearish ⇒ buy a **PUT**; otherwise **no trade**.

### 4.4 Risk gates (`risk.py`) — the heart of the system
Every candidate trade must clear **all** of the following *before* an order is sent:

| Gate | Rule | Value used |
|---|---|---|
| Per-trade risk | premium ≤ X% of equity | **2%** |
| Concurrency | open positions ≤ N | **5** |
| Daily-loss halt | stop new entries after a −X% day | **5%** |
| Defined-risk only | long options only; never sell naked | enforced |
| Expiry window | X ≤ DTE ≤ Y | **14–60 days** |
| Exit rules | take-profit / stop on premium | **+50% / −50%** |

Because max loss on a long option is its premium, the per-trade gate is exact: the agent sizes contracts so that `premium × 100 × qty ≤ 0.02 × equity`.

### 4.5 Contract selection (`mcp_client.find_atm_contract`)
Given a direction and the underlying's price, the agent queries the option chain for contracts within a strike band around at-the-money, filters to *tradable* contracts, chooses the expiration nearest to a ~30-day target within the 14–60-day window, and selects the strike closest to the money.

### 4.6 Execution via MCP (`mcp_client.py`)
Orders are placed with `place_option_order` (`buy_to_open`, market, day). Positions and orders are read with `get_all_positions` and `get_orders`. A subtlety discovered and fixed during the deployment: the MCP server returns list payloads wrapped as `{"data":{"result":[…]}}`; a naive parser reads zero positions, which would have caused the agent to believe it held nothing and over-buy past its cap. The fix (`_rows()` helper) is documented in §9.

### 4.7 Exit management
On each cycle, before scanning for new entries, the agent inspects each open position's unrealized return. If ≥ +50% it closes for **take-profit**; if ≤ −50% it closes for a **stop-loss**. Closing frees a slot, after which the agent may open a replacement in the same cycle.

### 4.8 Autonomy (`cron_once.py`, `.github/workflows/trade.yml`)
A market-hours-gated runner executes one full cycle when the US market is open and exits quietly otherwise. It runs in the cloud via GitHub Actions (free for public repositories), so no personal computer is required. A local hourly backstop (`autopilot.sh`) was added after observing that GitHub's scheduler fires unreliably (see §9).

### 4.9 Decision journal (`journal.py` → `activity.csv`, `ACTIVITY.md`)
This is the transparency instrument. **Every** cycle appends one row: timestamp, market state, equity, open positions, new trades, exits, and a plain-language summary (e.g., *"5 signal(s) fired but none opened (over cap): SPY, MSFT, NVDA, AMZN, TSLA"*). The journal is committed back to the repository automatically, producing a tamper-evident, timestamped audit trail. It is the primary data source for this paper.

### 4.10 Monitoring (`dashboard.py`, `results.py`)
A read-only Flask dashboard renders equity, P&L, positions, and recent orders through MCP; `results.py` prints slide-ready aggregate figures. Neither can place trades.

---

## 5. Methodology

### 5.1 Out-of-sample validation protocol (`backtest_signal.py`)
Signal parameters were fixed on an in-sample period and then evaluated, unchanged, on a disjoint out-of-sample period, for each of the 7 universe symbols. The comparison benchmark is **buy-and-hold** of the underlying over the same out-of-sample window. The reported statistic is the count of symbols on which the signal beat buy-and-hold.

### 5.2 Live deployment protocol
The agent was run on a **fresh, dedicated** paper account (created 2026-08-25, funded to $100,000, options level 3) so that no prior activity could contaminate results. `AGENT_MODE=LIVE_PAPER` routes real (paper) orders through MCP. Evaluation cycles ran during US market hours from 2026-09-01 to 2026-09-09.

### 5.3 Metrics
- **Total return** = (equity − 100,000) / 100,000.
- **Realized P&L** = sum over closed round-trips of (sell − buy) × 100 × qty.
- **Unrealized P&L** = equity − 100,000 − realized.
- **Per-trade return** = (sell − buy) / buy.
- **Win rate** = winning closed trades / total closed trades.
- **Profit factor** = gross wins / gross losses.
- **Gate-block count** = number of individual buy signals refused by the risk layer.
- **Peak-to-trough drawdown** = (peak equity − trough equity) / peak equity over the window.

---

## 6. Experimental Setup

| Parameter | Value |
|---|---|
| Universe | SPY, QQQ, AAPL, MSFT, NVDA, AMZN, TSLA (7) |
| Starting capital | $100,000 (paper) |
| Account | PA327FXF8G6D, options level 3 |
| Signal | EMA 20/50 trend + RSI-14 filter; min confidence 0.55 |
| Risk | 2%/trade · ≤5 open · 5% daily-loss halt · long-only · 14–60 DTE · +50%/−50% exits |
| Instrument | Single-leg long options (calls/puts), ~30 DTE, ATM |
| Execution | Alpaca `alpaca-mcp-server` (72 tools) via MCP client |
| Autonomy | GitHub Actions (cloud) + local hourly backstop |
| Live window | 2026-09-01 → 2026-09-09 |
| Cycles logged | 38 total; 27 during market hours |

---

## 7. Results

### 7.1 Out-of-sample backtest (H1)
The directional signal beat buy-and-hold on **0 of 7** symbols out-of-sample. **H1 is not rejected** — the signal has no demonstrable edge. This negative result is reported prominently in the agent's own materials rather than suppressed.

### 7.2 Live trade ledger (complete)
Over the window the agent executed **13 filled option orders**: 5 initial entries (all on 2026-09-01) and, subsequently, 4 exit-and-replace cycles. The **4 closed round-trips**, with exact fill prices, were:

| # | Contract | Buy | Sell | Return | P&L | Reason |
|---|---|---|---|---|---|---|
| 1 | SPY 260930 C 763 | $11.03 | $17.01 | **+54.2%** | **+$598** | take-profit |
| 2 | NVDA 261002 C 220 (×2) | $7.30 | $12.70 | **+74.0%** | **+$1,080** | take-profit |
| 3 | MSFT 261002 C 505 | $15.65 | $7.80 | **−50.2%** | **−$785** | stop-loss |
| 4 | SPY 261002 C 774 | $10.58 | $4.48 | **−57.7%** | **−$610** | stop-loss |

**Realized P&L = +$598 + $1,080 − $785 − $610 = +$283.**
- Gross wins = **+$1,678**; gross losses = **−$1,395**.
- **Win rate = 2/4 = 50%.**
- **Profit factor = 1,678 / 1,395 = 1.20.**
- Average win = $839; average loss = $697.50; win/loss size ratio = 1.20.

### 7.3 Position sizing verification
Initial premiums deployed on 2026-09-01: SPY $1,103 (1.10% of equity), MSFT $1,565 (1.57%), NVDA $1,460 (1.46%), AMZN $1,750 (1.75%), TSLA $1,750 (1.75%). **Every position's maximum loss was ≤ the 2% ($2,000) cap** — the sizing gate performed exactly as specified. Total capital at risk at peak exposure was $7,628, or **7.6% of the account**, spread across the maximum 5 positions.

### 7.4 Risk-gate behavior
- Market-hours evaluation cycles: **27**.
- Cycles in which the risk layer blocked at least one signal: **22**.
- **Total individual buy signals refused: 117.** These are signals the momentum logic generated that the agent declined to act on — overwhelmingly because the 5-position concurrency cap was full.
- Open positions **never exceeded 5** at any observed cycle. The concurrency gate held for the entire window.

The interpretation is direct: the agent spent most of its life *saying no*. For every trade it placed, it refused roughly a dozen. This is the behavioral signature the system was designed to produce.

### 7.5 Equity trajectory and the submission "natural experiment"
Key equity waypoints from the journal:

| Date/time (ET) | Equity | Note |
|---|---|---|
| 2026-09-01 10:20 | $100,000 | first cycle / baseline |
| 2026-09-01 (Day-1 dip) | ≈ $99,588 | −0.41% intraday trough, contained |
| 2026-09-03 14:06 | **$102,200.48** | **peak equity** |
| **2026-09-03 (submission)** | **$101,823.43** | **+1.82% — the reported result** |
| 2026-09-09 15:52 | **$98,685.15** | **trough; −1.32%** |
| 2026-09-09 (latest) | $98,704.15 | −1.30% |

The hackathon result was captured honestly at **+1.82%**. The agent then continued to run, unchanged, for six more trading days and **gave the gains back to −1.30%**. Two of those days produced the stop-losses in §7.2 (MSFT −50.2% on 09-08; SPY −57.7% on 09-09). **Peak-to-trough drawdown over the full window was (102,200 − 98,685) / 102,200 = 3.44%.**

### 7.6 Realized vs. unrealized decomposition (latest)
At the latest reading: equity $98,704.15; **realized P&L +$283** (§7.2); therefore **unrealized P&L ≈ −$1,579** across the 5 still-open positions. The account's negativity is entirely an *open-position mark*, not a booked loss — consistent with the observation that short-horizon marks are noise.

### 7.7 Summary of results against hypotheses
- **H1 (null-edge):** supported. 0/7 out-of-sample; the +1.82%→−1.30% live swing is consistent with a zero-edge process buffeted by luck.
- **H2 (buildable discipline):** supported. Risk limits were never violated (≤5 positions; every entry ≤2%); losses were mechanically contained by stops; and every one of the 38 cycles is logged.

---

## 8. Discussion

### 8.1 The swing is the finding
The most valuable data point in this study arrived *after* the deliverable was submitted. A system that reports +1.82% and stops there invites the reader to infer skill. By continuing to run and honestly recording the reversal to −1.30%, Risk Gate converted its own P&L into evidence for its thesis: **over a one-to-two-week horizon, a zero-edge options strategy's return is a coin flip, and the sign of that flip should not be mistaken for competence.** Had the agent been stopped at submission, the project would have looked like a modest winner; the truth is that it is a *disciplined participant in a random process*, which is exactly what it claimed to be.

### 8.2 Discipline is separable from edge
The two hypotheses are empirically independent in our data. The signal failed (H1) while the risk architecture succeeded (H2). This separation is the paper's conceptual core: **you do not need a profitable signal to build a trustworthy agent.** The 117 refusals, the 2%-capped sizing, and the two stop-losses that fired at roughly their thresholds are all evidence that the *machinery of prudence* worked regardless of the *quality of prediction*.

### 8.3 Losses were contained, not avoided
Risk Gate did not avoid losses — it *bounded* them. The two losing trades hit −50.2% and −57.7% of premium, on positions sized to ≤2% of equity, so each cost the account well under 1%. No single decision could threaten the account, by construction. This is the practical payoff of defined-risk instruments plus a hard sizing gate.

### 8.4 Honesty as an engineering requirement
Transparency here is not a slogan but a mechanism: the decision journal makes dishonesty *expensive*, because every claim in this paper is checkable against a committed, timestamped log. A project cannot quietly overstate its record when the record writes itself.

---

## 9. Limitations and Threats to Validity

1. **Sample size.** Four closed round-trips and 27 cycles is far too small for statistical inference about returns. All return figures are anecdotal, not significant.
2. **Horizon and regime.** Nine calendar days in a single market regime; no bear market, no volatility shock, no earnings-gap stress test.
3. **Hourly gating delays exits.** Exits are only checked when a cycle runs. The SPY stop filled at **−57.7%**, not −50%, because the position had already moved past the threshold by the time the next hourly cycle executed. Finer cadence (or event-driven exits) would tighten this.
4. **Paper fills.** Paper trading assumes fills that a live market might not grant; slippage, partial fills, and liquidity are not fully modeled.
5. **Scheduler reliability.** GitHub's cron fired unreliably, motivating a local backstop; coverage gaps mean some intended cycles did not execute, and the true set of "missed" signals is unmeasured.
6. **Parsing defect (fixed).** An MCP payload-parsing bug initially caused the agent to read zero positions; had it gone undetected it would have breached the concurrency cap. It was caught via the monitoring workflow and fixed (`_rows()`), but its existence shows that risk guarantees depend on correct plumbing, not just correct rules.
7. **Backtest simplicity.** The OOS test compares against buy-and-hold on the underlying, not against a risk-matched options benchmark; it establishes "no edge," not a precise effect size.
8. **Survivorship / universe choice.** The 7 mega-caps are liquid, trending names during the window; results may not transfer to broader or less liquid universes.

---

## 10. Ethical and Responsible-AI Considerations

- **Not financial advice.** The system is an educational/engineering artifact on a paper account. It makes no personalized recommendation and should not be construed as one.
- **No overclaiming.** The design's headline property is that it refuses to imply skill it cannot demonstrate; the 0/7 result is foregrounded.
- **Auditability.** The decision journal exists precisely so that outside parties can verify claims rather than trust them.
- **Real-money caution.** Any transition to real capital is explicitly gated (see §11) behind a genuine, extended, out-of-sample track record; the present results would *not* justify it.

---

## 11. Future Work — toward Risk Gate v2

The next version keeps the proven skeleton (data → signal → risk → MCP execution → exits → autonomy → journal) and adds four capabilities, each of which must pass the same honesty bar before it is trusted:

1. **Explainability layer.** Emit a natural-language rationale per decision — *"I am buying X because trend/RSI/model say Y, keeping in mind these risk parameters"* — delivered to a messaging channel and the journal.
2. **Machine-learning confidence.** Replace the scalar heuristic confidence with calibrated model outputs (e.g., gradient-boosted trees), *validated out-of-sample*, feeding the same risk gates.
3. **Backtest-gated strategy selection.** Only strategies that pass an OOS test are permitted to trade live; failing strategies are logged but muted.
4. **Real-money readiness gate.** Kill-switch, secret management, capital caps, failure alerts, reconciliation, and — the binding constraint — a long live paper track record that beats buy-and-hold out-of-sample *before any real capital is deployed*, and even then, at minimal size.

The −1.30% post-submission week is the strongest possible argument for gate (4): it is a live reminder that a pretty short-run number is not permission to risk real money.

---

## 12. Conclusion

Risk Gate set out to prove an uncomfortable but useful proposition: that an autonomous trading agent can be **honest, disciplined, and safe even without a profitable edge**, and that these properties are *measurable*. The evidence supports it. The signal failed out-of-sample (0/7). The risk architecture nonetheless never let open positions exceed five, sized every one of the nine entries to ≤2% of equity, refused 117 signals to stay within limits, and contained both losing trades to sub-1% account impact. And in the clearest result of all, the account's own P&L swung from +1.82% at submission to −1.30% six days later — the agent narrating, in live money, the exact thesis it was built to argue. The right lesson is not "the agent made or lost money." It is that **a system can be trustworthy independent of whether it is lucky**, and that building for honesty and risk control is both possible and worthwhile. That is the foundation the next version will build on.

---

## References
- Fama, E. F. (1970). *Efficient Capital Markets: A Review of Theory and Empirical Work.* Journal of Finance, 25(2).
- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems.* (Origin of the RSI indicator.)
- Bailey, D. H., Borwein, J., López de Prado, M., Zhu, Q. J. (2014). *The Probability of Backtest Overfitting.* Journal of Computational Finance.
- López de Prado, M. (2018). *Advances in Financial Machine Learning.* Wiley.
- Anthropic (2024). *Model Context Protocol (MCP)* specification.
- Alpaca Markets. *Trading API & alpaca-mcp-server documentation.*

---

## Appendix A — Full parameter table
See §6. All values are the literal constants in `config.py`: `UNIVERSE`, `MAX_RISK_PER_TRADE_PCT=0.02`, `MAX_CONCURRENT=5`, `DAILY_LOSS_LIMIT_PCT=0.05`, `MIN_DTE=14`, `MAX_DTE=60`, `TAKE_PROFIT_PCT=0.50`, `STOP_LOSS_PCT=0.50`, `EMA_FAST=20`, `EMA_SLOW=50`, `RSI_PERIOD=14`, `MIN_CONFIDENCE=0.55`, `ACCOUNT_START=100000`.

## Appendix B — Complete order ledger (13 fills)
```
2026-09-01 14:20  BUY  1x SPY  260930 C 763  @ $11.03
2026-09-01 14:20  BUY  1x MSFT 261002 C 505  @ $15.65
2026-09-01 14:20  BUY  2x NVDA 261002 C 220  @ $7.30
2026-09-01 14:20  BUY  2x AMZN 261002 C 255  @ $8.75
2026-09-01 14:20  BUY  1x TSLA 261002 P 360  @ $17.50
2026-09-02 16:42  SELL 2x NVDA 261002 C 220  @ $12.70   (+74.0% take-profit)
2026-09-02 16:42  BUY  1x SPY  261002 C 765  @ $11.26
2026-09-03 18:06  SELL 1x SPY  260930 C 763  @ $17.01   (+54.2% take-profit)
2026-09-03 18:06  BUY  1x SPY  261002 C 774  @ $10.58
2026-09-08 17:14  SELL 1x MSFT 261002 C 505  @ $7.80    (−50.2% stop)
2026-09-08 17:14  BUY  1x SPY  261009 C 768  @ $11.34
2026-09-09 17:08  SELL 1x SPY  261002 C 774  @ $4.48    (−57.7% stop)
2026-09-09 17:08  BUY  1x SPY  261009 C 763  @ $11.76
```

## Appendix C — Journal aggregate statistics
- Total journal rows: **38**; market-hours cycles: **27**.
- Entries (buys): **9**; exits (sells): **4**; cycles with ≥1 gate block: **22**.
- Signal-level gate blocks (sum): **117**.
- Equity: first $100,000.00 · peak $102,200.48 · trough $98,685.15 · latest $98,704.15.
- First cycle 2026-09-01 10:20 ET; last cycle analyzed 2026-09-09 15:52 ET.

## Appendix D — Glossary
- **Premium:** price paid for an option; the maximum loss on a long option.
- **DTE:** days to expiration.
- **ATM:** at-the-money (strike ≈ underlying price).
- **Take-profit / Stop:** mechanical exits at +50% / −50% of premium.
- **Realized vs unrealized P&L:** booked (closed) vs marked-to-market (open) profit/loss.
- **Gate block:** a generated buy signal the risk layer declined to act on.
- **OOS:** out-of-sample — data the strategy was not tuned on.
