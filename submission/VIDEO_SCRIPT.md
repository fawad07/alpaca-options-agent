# Video Script — Risk Gate (aim: ~3 minutes)

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
server** — the core theme of this hackathon. It runs autonomously every
market-hours cycle and logs every single decision to a journal."

**[0:55 — Live dry-run · screen: `.venv/bin/python agent.py`]**
"Let me run it. For each stock it forms a view — buy a call in an uptrend, a put in
a downtrend — and here's the important part…"
[point at the SPY/QQQ lines]
"…it **refuses** to buy SPY and QQQ, because a single contract would risk more than
2% of the account. The risk gate is doing its job."

**[1:25 — MCP is real · screen: `mcp_test.py` then `test_select.py`]**
"This isn't a mock. It connects to Alpaca's real MCP server — 72 tools — and for
each signal it selects a real at-the-money contract and prices it live, through MCP."

**[1:50 — Live paper + the decision journal · screen: ACTIVITY.md]**
"In live paper mode it places orders via `place_option_order` and manages the exit —
take profit at +50%, stop at −50%. And every run writes to a public decision journal,
so there's an honest record of everything it did. Over the week it **refused 87 buy
signals** because it was already at its 5-position cap — discipline over greed."
[show ACTIVITY.md rows: "none opened — over cap"]

**[2:15 — Results · Slide 9 / Alpaca P&L]**
"The result on the paper account: up **1.8%** for the week. Two take-profits fired
automatically — **+54%** on an SPY call and **+74%** on NVDA — with **zero** stop-losses
and about a **1% max drawdown**. Small, controlled, every trade explainable."
[show the Alpaca equity curve + slide 9]

**[2:40 — The honesty check · Slide 8 / `backtest_signal.py`]**
"But here's what no one else will show you: I out-of-sample tested the signal, and it
did **not** beat buy-and-hold — zero of seven names. So I don't claim a magic edge.
Risk Gate competes on being disciplined, safe, and transparent. That's the whole point."

**[3:00 — Close · Slide 10]**
"Risk Gate: an autonomous options agent that's honest about risk. Code's open on
GitHub, MIT-licensed. Thanks to lablab.ai and Alpaca."
[show repo link + tags @lablabai @AlpacaHQ]

---
### Shot list to capture beforehand
- [ ] `.venv/bin/python agent.py` (dry-run — shows the risk gate blocking SPY/QQQ)
- [ ] `.venv/bin/python mcp_test.py` (72 tools connected)
- [ ] `.venv/bin/python test_select.py` (real contracts + live prices via MCP)
- [ ] `ACTIVITY.md` — the decision journal (scroll the "over cap" + take-profit rows)
- [ ] `.venv/bin/python results.py` and/or `./check.sh` (the +1.82% summary)
- [ ] `.venv/bin/python backtest_signal.py` (the honest OOS result)
- [ ] Final P&L + equity curve from Alpaca (account PA327FXF8G6D)

**Numbers to say out loud:** +1.82% · +54% SPY · +74% NVDA · 0 stops · 87 gate blocks · ~1% drawdown.
