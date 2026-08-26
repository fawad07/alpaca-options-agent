# Risk Gate — Honest Options AI
*One-page write-up · Alpaca AI Trading Agents Hackathon 2026*
*Team: Risk Gate · Paper account: PA327FXF8G6D · Repo: github.com/fawad07/alpaca-options-agent*

## What it is
Risk Gate is an **autonomous options-trading agent** that runs on an Alpaca **paper**
account and executes **entirely through the Alpaca MCP server**. Its guiding idea is
honesty: instead of claiming a magic profit signal, its real edge is **discipline —
hard risk gates and out-of-sample validation** — with every decision explainable.

## AI logic (how it decides)
For each name in a liquid universe (SPY, QQQ, AAPL, MSFT, NVDA, AMZN, TSLA) the agent
forms a transparent, rule-based view from daily price action:
- **Trend:** 20-day EMA vs 50-day EMA. **Momentum filter:** 14-day RSI.
- **Uptrend + RSI not overbought → buy a CALL.**
- **Downtrend + RSI not oversold → buy a PUT.**
- **Otherwise → no trade.** Confidence scales with trend strength; weak setups are skipped.
It always expresses its view with **defined-risk long options** (a bought call or put),
selecting the tradable contract nearest at-the-money at ~30 days to expiry.

## Risk gates (how it protects the account)
Every candidate trade must clear all of these before it can be placed:
- **≤ 2%** of equity risked per trade (a long option's max loss is its premium, so the
  agent sizes contracts so premium ≤ 2% of equity).
- **≤ 5** concurrent positions.
- **5% daily-loss halt** — no new trades after a bad day.
- **Defined-risk only** — the agent *buys* options; it never sells naked.
- **Expiry window 14–60 DTE**; **take-profit +50%**, **stop −50%** on premium.
In dry-run testing the gates correctly *refused* SPY and QQQ trades whose single-contract
cost exceeded the 2% cap — protection working as intended.

## Alpaca infrastructure (how it's built)
- **MCP-native.** The agent is an MCP client to Alpaca's official `alpaca-mcp-server`
  (72 tools). It calls `get_account_info`, `get_option_contracts`, `get_option_snapshot`,
  `place_option_order`, `get_all_positions`, and `close_position` as MCP tools — the
  AI-drives-the-broker pattern, run autonomously on a 15-minute market-hours loop.
- **Trading API** underpins it all (also used directly for the connection check).
- **Paper environment**, $100,000 starting balance. A **live dashboard** reads account
  equity, positions, and orders through MCP for real-time monitoring.
- Fully autonomous scheduling via a market-hours-gated runner.

## Honesty check (our differentiator)
We out-of-sample tested the directional signal (settings locked on 2016–2022, tested on
2023–now): it beat buy-and-hold on **0 of 7** names. We **report this openly** rather than
hiding it. Risk Gate therefore competes on discipline, safety, and transparency — not on
a pretended edge. That candor, plus rigorous risk control, is the whole point.

## Results  *(fill in at the end)*
- Period: **Aug 28 – Sep 4, 2026** · Final equity: **[$____]** · P&L: **[±__%]**
- Trades taken: **[__]** · Take-profits / stops: **[__ / __]** · Risk-gate blocks: **[__]**
- **[Screenshot: Alpaca paper P&L + the live dashboard]**

## Honest takeaway
One week of options P&L is dominated by luck. Risk Gate is built to be **transparent,
disciplined, and safe**: every trade is explainable, every risk is capped, and the
signal's real (limited) edge is measured, not oversold.
