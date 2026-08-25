# One-Page Write-Up — Risk Gate (Honest Options AI)  *(FILL THIS LAST)*

> Skeleton only. Complete it on Day 7 once you have real paper results.
> Keep it to ONE page. The email asks specifically for: AI logic · risk gates ·
> Alpaca infrastructure. A screenshot of the paper account P&L helps.

## What it is
An autonomous options-trading agent on an Alpaca paper account. It reads daily
price action, forms a directional view, and expresses it with **defined-risk long
options** (calls for bullish, puts for bearish), under strict risk gates.

## AI logic (how it decides)
- Signal: trend (EMA[20] vs EMA[50]) filtered by momentum (RSI[14]).
  - Uptrend + RSI not overbought → **bullish → buy a call**
  - Downtrend + RSI not oversold → **bearish → buy a put**
  - Otherwise → **no trade**
- Confidence scales with trend strength; weak signals are skipped.
- *Honesty note (our differentiator):* the signal is out-of-sample tested
  (`backtest_signal.py`). Result: [paste — e.g., "beat buy-and-hold on X/7 names"].
  The agent's edge is **discipline + risk control**, not a claimed magic edge.

## Risk gates (how it protects the account)
- Max **2%** of equity risked per trade (position sized to the option premium).
- At most **5** concurrent positions.
- **5% daily-loss halt** — stops opening new trades after a bad day.
- **Defined-risk only** — buys options; never sells naked.
- Expiry window **14–60 DTE**; take-profit **+50%**, stop **−50%** on premium.

## Alpaca infrastructure (how it's built)
- **Alpaca Trading API** via `alpaca-py` on a dedicated **paper** account ($100k).
- [MCP Server / CLI]: [describe which you used and how].
- Underlying price data: [Alpaca market data / free daily bars].
- Autonomous loop runs during market hours ([--loop / cron/launchd]).

## Results
- Period: Aug 28 – Sep 4 · Final equity: [$___] · P&L: [±__%]
- Trades taken: [__] · Win rate: [__%] · Biggest risk-gate save: [___]
- [Screenshot of the Alpaca paper P&L]

## Honest takeaway
One week of options P&L is dominated by luck; this agent is built to be
**transparent, disciplined, and safe** — every trade is explainable, every risk
is capped, and the signal's real (limited) edge is measured, not oversold.
