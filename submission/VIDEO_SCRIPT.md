# Video Script — Risk Gate (aim: ~2.5–3 minutes)

Record your screen (QuickTime → New Screen Recording) and talk over it. Keep it
calm and honest — that tone IS the pitch. On-screen cues in [brackets].

---

**[0:00 — Hook · your face or the title slide]**
"Most AI trading bots promise to make you rich. This one is honest about what
actually works. I'm [name], and this is **Risk Gate** — an autonomous options
agent I built on Alpaca."

**[0:15 — The problem · Slide 2]**
"The dirty secret of AI trading: a backtest can look amazing and still lose real
money, because it just memorized the past. So I built the opposite of a hype bot —
one whose edge is **discipline and risk control**, not a magic signal."

**[0:35 — Architecture · Slide 4 / diagram]**
"Here's how it works. It reads price data, forms a simple, explainable view, runs
it through hard risk gates, and then places the trade **through Alpaca's MCP
server** — which is the core theme of this hackathon."

**[0:55 — Live dry-run · screen: `.venv/bin/python agent.py`]**
"Let me run it. For each stock it forms a view — buy a call in an uptrend, a put in
a downtrend — and here's the important part…"
[point at the SPY/QQQ lines]
"…it **refuses** to buy SPY and QQQ, because a single contract would risk more than
2% of the account. The risk gate is doing its job."

**[1:25 — MCP is real · screen: `mcp_test.py` then `test_select.py`]**
"This isn't a mock. It connects to Alpaca's real MCP server — 72 tools — and for
each signal it selects a real at-the-money contract and prices it live, through MCP."

**[1:50 — Placing a trade · screen: LIVE_PAPER run / Alpaca positions]**
"In live paper mode it places the order via `place_option_order` and manages the
exit — take profit at +50%, stop at −50%. All paper money, zero real risk."
[show the Alpaca positions/orders screen]

**[2:10 — The honesty check · Slide 8 / `backtest_signal.py`]**
"And here's what no one else will show you: I out-of-sample tested the signal. It
did **not** beat buy-and-hold. So I don't claim a magic edge — Risk Gate competes
on being disciplined, safe, and transparent. That honesty is the whole point."

**[2:35 — Close · Slide 10]**
"Risk Gate: an autonomous options agent that's honest about risk. Code's open on
GitHub, MIT-licensed. Thanks to lablab.ai and Alpaca."
[show repo link + tags @lablabai @AlpacaHQ]

---
### Shot list to capture beforehand
- [ ] `.venv/bin/python agent.py` (dry-run — shows the risk gate blocking SPY/QQQ)
- [ ] `.venv/bin/python mcp_test.py` (72 tools connected)
- [ ] `.venv/bin/python test_select.py` (real contracts + live prices via MCP)
- [ ] A LIVE_PAPER run during market hours + the Alpaca positions/orders screen
- [ ] `.venv/bin/python backtest_signal.py` (the honest OOS result)
- [ ] Final P&L screen from Alpaca
