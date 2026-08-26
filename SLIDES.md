# Slide Deck — Risk Gate (Honest Options AI)

Drop each block onto a slide (Google Slides / Canva / PowerPoint). Keep it visual:
big words, one idea per slide, a screenshot where noted. ~10 slides, ~3–4 min.

---

### Slide 1 — Title
**Risk Gate**
*Honest Options AI*
An autonomous options agent on Alpaca — built on discipline, not hype.
Team: Risk Gate · Alpaca AI Trading Agents Hackathon 2026
*(visual: the 🛡️ logo / a clean dark title card)*

### Slide 2 — The problem
Every "AI trading bot" promises easy money.
Almost all of them **lose** — because a backtest that dazzles you has usually just *memorized the past*.
**The market punishes overconfidence.**

### Slide 3 — Our thesis
We didn't build a "get-rich" bot. We built an **honest** one.
> Its edge isn't a magic signal — it's **discipline, risk gates, and honest validation.**
Every trade is explainable. Every risk is capped.

### Slide 4 — How it works  *(architecture diagram)*
`Price data → Signal → Risk Gates → Alpaca MCP Server → Paper account`
- Rule-based signal decides direction
- Risk gates decide *if* and *how big*
- Orders execute **through Alpaca's MCP server**
*(visual: 5-box left-to-right flow; highlight the MCP box)*

### Slide 5 — The AI logic (transparent on purpose)
- Trend: EMA(20) vs EMA(50), filtered by RSI(14)
- **Uptrend → buy a CALL · Downtrend → buy a PUT · else → no trade**
- Confidence scales with trend strength; weak setups are skipped
*(visual: a chart with the EMAs + a marked entry)*

### Slide 6 — Risk gates (the heart of it)
- Max **2%** of equity risked per trade
- ≤ **5** concurrent positions
- **5% daily-loss halt** — stops after a bad day
- **Defined-risk only** — buys options, never sells naked
- Expiry **14–60 DTE** · take-profit **+50%** · stop **−50%**
*(visual: screenshot of the agent BLOCKING a trade that exceeds the cap)*

### Slide 7 — Built on MCP  *(the hackathon theme)*
The agent trades **through Alpaca's official MCP server** (72 tools).
It calls `get_option_contracts`, `get_option_snapshot`, `place_option_order` as MCP tools —
the AI-drives-the-broker pattern, done autonomously.
*(visual: screenshot of `mcp_test.py` — "Connected via MCP — 72 tools")*

### Slide 8 — The honesty check (our differentiator)
We out-of-sample tested the signal: it beat buy-and-hold on **0 of 7** names.
**So we don't pretend it has a magic edge.** We compete on discipline, safety, and transparency.
> Most teams hide this. We put it on a slide.

### Slide 9 — Demo  *(screenshot / short clip)*
- The agent runs → picks a real ATM contract → risk-gates it → places it via MCP
- Live paper positions + P&L
*(visual: agent run output + Alpaca positions screen)*

### Slide 10 — Results & why Risk Gate
- Paper P&L over the week: **[fill in]**  · Trades: **[fill in]** · Risk-gate saves: **[fill in]**
- **Honest. Disciplined. Safe. Explainable.**
- Repo: github.com/fawad07/alpaca-options-agent · Account #: PA327FXF8G6D
*Thank you — @lablabai · @AlpacaHQ*
