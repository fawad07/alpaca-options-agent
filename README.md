# 🛡️ Risk Gate — Honest Options AI

**Team:** Risk Gate · **Tagline:** Honest options AI

An autonomous options-trading agent for the Alpaca AI Trading Agents Hackathon
(Aug 28 – Sep 4, 2026). Its edge isn't a magic signal — it's **discipline and risk
gates**, with every decision explainable and honestly validated. **Paper account
only. Never real money.**

Start here → **PLAN.md** (the week plan) and **TRACKER.md** (the checklist).
Write-up goes in **WRITEUP.md** — filled in LAST.

## Run the dry-run (works right now, no Alpaca account needed)
```
cd ~/Desktop/alpaca-options-agent
pip3 install pandas numpy requests
python3 agent.py
```
It fetches real prices, computes signals, and prints the exact option trades it
*would* place — with every risk gate applied. Places nothing.

Honesty check on the signal:
```
python3 backtest_signal.py
```

## Go live on your Alpaca PAPER account (later, after setup)
1. `pip3 install -r requirements.txt`
2. `cp .env.example .env` and paste your **paper** API keys
3. Set `AGENT_MODE=LIVE_PAPER` in `.env`
4. Fill the `# TODO(alpaca)` hooks in `agent.py` (Day 1–2 of the plan)
5. `python3 agent.py --loop 900`  (runs every 15 min)

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
