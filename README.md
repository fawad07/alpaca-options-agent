# 🛡️ Risk Gate — Honest Options AI

**Team:** Risk Gate · **Tagline:** Honest options AI

An autonomous options-trading agent for the Alpaca AI Trading Agents Hackathon
(Aug 28 – Sep 4, 2026). Its edge isn't a magic signal — it's **discipline and risk
gates**, with every decision explainable and honestly validated. **Paper account
only. Never real money.**

Start here → **PLAN.md** (the week plan) and **TRACKER.md** (the checklist).
Write-up goes in **WRITEUP.md** — filled in LAST.

## Setup (once)
```
cd ~/Desktop/alpaca-options-agent
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then paste your PAPER keys into .env
```
> Uses a Python 3.11 virtualenv (the MCP tooling needs 3.10+). Run everything
> with `.venv/bin/python …`.

## Dry-run (no orders — prints what it WOULD do)
```
.venv/bin/python agent.py
```
Applies every risk gate and prints the option trades it would place. Places nothing.

## Verify the plumbing
```
.venv/bin/python test_connection.py    # account balance via Alpaca API
.venv/bin/python mcp_test.py           # connect to Alpaca MCP server, list tools
.venv/bin/python test_select.py        # pick + price an ATM option per symbol via MCP
.venv/bin/python backtest_signal.py    # out-of-sample honesty check on the signal
```

## Live status dashboard (also your demo URL)
```
.venv/bin/python dashboard.py     # → http://localhost:8095
```
Shows account equity + P&L, open option positions, recent orders, and the agent's
decisions — all read through the Alpaca MCP server. Auto-refreshes. Read-only.

## Go live on the PAPER account (during US market hours)
1. In `.env` set `AGENT_MODE=LIVE_PAPER`
2. `.venv/bin/python agent.py`            (one pass — places/manages via MCP)
   or `.venv/bin/python agent.py --loop 900`   (every 15 min)

**Architecture:** `agent.py` (signal + risk gates) → `mcp_client.py` → Alpaca **MCP server**
→ Alpaca paper account. Options only, defined-risk (long calls/puts), paper money only.

## Files
| File | Role | Reused from |
|---|---|---|
| `agent.py` | Autonomous loop: signal → option → risk gates → order | new |
| `signals.py` | AI logic (EMA/RSI features → bull/bear/neutral) | ai-trading-pipeline |
| `risk.py` | Risk gates (sizing, limits, defined-risk) | Trading_signal_production discipline |
| `data.py` | Free daily bars for underlyings | crypto-companion |
| `backtest_signal.py` | Out-of-sample honesty check | ai-trading-pipeline |
| `config.py` | Central settings + .env keys | Trading_signal_production pattern |

## Guardrails (built in)
- Paper only · defined-risk only (buys options, never sells naked)
- 2% max risk/trade · ≤5 open · 5% daily-loss halt · DTE 14–60
- You do all account/key setup and submission; the code never touches real money.

*Not financial advice. Educational hackathon project.*
