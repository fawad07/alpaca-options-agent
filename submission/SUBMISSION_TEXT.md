# Submission text (copy-paste into the lablab.ai form)

## Title
Risk Gate — Honest Options AI

## Short description
An autonomous options-trading agent built on Alpaca's MCP server. Its edge isn't a
magic signal — it's hard risk gates and out-of-sample honesty. Paper-only, every
trade explainable. Finished the week at +1.82%.

## Long description
Risk Gate is an autonomous options-trading agent that runs on an Alpaca paper account
and executes entirely through Alpaca's official MCP server (the "AI drives the broker"
pattern). Most "AI trading bots" promise easy money; a backtest that dazzles you has
usually just memorized the past. So we built the opposite of a hype bot — one whose
edge is discipline and transparency, not a secret signal.

How it decides: for a liquid universe (SPY, QQQ, AAPL, MSFT, NVDA, AMZN, TSLA) the
agent forms a simple, explainable view from daily price action — a 20/50-day EMA trend
with a 14-day RSI filter. Uptrend → buy a call; downtrend → buy a put; otherwise no
trade. It always expresses its view with defined-risk long options, picking the
tradable contract nearest at-the-money at ~30 days to expiry.

How it protects the account (the heart of it): every candidate trade must clear hard
risk gates before it can be placed — ≤2% of equity risked per trade, ≤5 concurrent
positions, a 5% daily-loss halt, defined-risk (long options only, never naked), a
14–60 DTE window, and automatic exits at +50% take-profit / −50% stop.

How it's built: the agent is an MCP client to Alpaca's official alpaca-mcp-server
(72 tools) — get_account_info, get_option_contracts, get_option_snapshot,
place_option_order, get_all_positions, close_position. It runs autonomously on a
market-hours schedule (GitHub Actions, no server needed) and writes every decision —
traded, no-signal, risk-blocked, or market-closed — to a public decision journal, so
there is an honest, timestamped record of everything it did.

The honesty check (our differentiator): we out-of-sample tested the directional signal
(parameters locked on older data, tested on unseen data). It beat buy-and-hold on 0 of
7 names. We report this openly instead of hiding it. Risk Gate competes on discipline,
safety, and transparency — not a pretended edge.

Results (paper account PA327FXF8G6D, Sep 1–3, 2026): finished at $101,823 — +$1,823
(+1.82%) from the $100,000 start. Two take-profits fired automatically (+54% on an SPY
call, +74% on NVDA), with zero stop-losses, ~1% max drawdown, and 87 buy signals
correctly refused at the 5-position cap. One week of options P&L is mostly luck — the
point is an AI agent that is transparent, disciplined, and safe: every trade
explainable, every risk capped, and the signal's real (limited) edge measured, not
oversold.

Open source (MIT): github.com/fawad07/alpaca-options-agent

## Tags / technologies
Alpaca, MCP Server, Options, AI Agent, Autonomous Trading, Python, Risk Management, Trading API
