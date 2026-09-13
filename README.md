# 🛡️ Risk Gate — Honest Autonomous Trading Agent

An autonomous agent that trades a **paper** Alpaca account **through the Alpaca MCP server**.
Its edge isn't a magic signal — it's **discipline, risk gates, and honesty**. Every decision is
logged; the strategy is openly reported to have no proven edge out-of-sample. **Paper money only.**

- **Account A** — the original **options-only** agent (the hackathon entry). Kept pure.
- **Account B** — the evolved **options + crypto** agent (24/7), the experiment going forward.

> Not financial advice. Educational project. Paper trading only — never real money.

---

## 📁 Directory map

```
alpaca-options-agent/
│
├── CORE AGENT (flat modules — imported by name; keep at root)
│   ├── config.py          central settings + risk params (reads keys from .env)
│   ├── accounts.py        per-account profiles (A = options-only; B = options+crypto)
│   ├── agent.py           the brain: rank signals → risk gates → place trades → journal
│   ├── signals.py         the "AI logic" (EMA/RSI → bull/bear/neutral)
│   ├── data.py            daily price bars (stocks + crypto) via Yahoo
│   ├── risk.py            the risk gates (sizing, caps, daily-loss halt)
│   ├── journal.py         per-account decision journal (activity*.csv / ACTIVITY*.md)
│   ├── mcp_client.py      talks to Alpaca THROUGH the MCP server (orders, positions)
│   └── mcp_test.py        launches the MCP server; verifies the connection
│
├── instruments/          how each asset class is traded (the swappable handlers)
│   ├── base.py            the InstrumentHandler interface
│   ├── options.py         OptionsHandler (ATM contract, premium, defined risk)
│   └── crypto.py          CryptoSpotHandler (long-only, broker stop_limit, agent TP)
│
├── ENTRYPOINTS & SCRIPTS (run these)
│   ├── cron_once.py       one market-gated pass — used by the cloud workflows
│   ├── check.sh           daily status: cloud runs + journal + P&L
│   ├── trade-now.sh       force one cloud trade pass now
│   ├── autopilot.sh       local hourly backstop (fires a pass during market hours)
│   ├── run_agent.sh       local market-gated wrapper
│   └── market_open.py     prints OPEN/CLOSED (used by run_agent.sh)
│
├── APPS
│   ├── dashboard.py       live status web dashboard (→ localhost:8095)
│   ├── results.py         one-command P&L numbers
│   └── templates/         dashboard HTML
│
├── ACCOUNT JOURNALS (auto-written each run)
│   ├── activity.csv / ACTIVITY.md        account A decision journal
│   └── activity-B.csv / ACTIVITY-B.md    account B decision journal
│
├── tools/                standalone dev/verification scripts
│   ├── test_connection.py   check account connects
│   └── test_select.py       pick + price an ATM option per symbol via MCP
│
├── research/             offline analysis (never touches live trading)
│   ├── backtest_crypto.py / backtest_fetch.py   crypto backtester (walk-forward OOS)
│   ├── backtest_signal.py                       v1 options OOS honesty check
│   ├── refresh_stats.py                         account-aware track-record snapshot
│   ├── stats_history*.csv / stats_snapshot*.md  the growing track record (A and B)
│   ├── build_paper_pdf.py + RESEARCH_PAPER.*    the research paper
│   ├── data/                                    cached historical crypto bars
│   └── *.md                                     v2 design, plan, backtest, Step 0 docs
│
├── submission/           hackathon deliverables (deck, write-up, video script, cover, social)
├── docs/                 guides (automation, deploy, monitoring, plan, tracker, checklist)
├── .github/workflows/    cloud autonomy (see below)
│
└── config: .env.example · requirements.txt · render.yaml · LICENSE · build_deck.js · .gitignore
```

---

## 👥 The two accounts (deployments)

Same codebase, selected by the `DEPLOY_ACCOUNT` env var (default `A`):

| | **Account A** | **Account B** |
|---|---|---|
| Trades | options only | options **+ crypto spot** |
| Position cap | 5 | 6 |
| Fill order | universe (V1) | confidence-ranked |
| Schedule | market hours | **24/7** (options still gated to hours) |
| Keys (`.env`) | `ALPACA_API_KEY` | `ALPACA_B_API_KEY` |
| Journal | `activity.csv` | `activity-B.csv` |

---

## ⚙️ Setup (once)
```bash
cd ~/Desktop/alpaca-options-agent
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then paste your PAPER keys into .env
```

## ▶️ Run
```bash
# Dry run (no orders — prints intended trades). Try either account:
AGENT_MODE=DRY_RUN .venv/bin/python agent.py                 # account A (options)
AGENT_MODE=DRY_RUN DEPLOY_ACCOUNT=B .venv/bin/python agent.py # account B (options+crypto)

# Live status dashboard
.venv/bin/python dashboard.py            # → http://localhost:8095

# Daily monitoring
./check.sh                               # runs + journal + P&L
./trade-now.sh                           # force a cloud pass

# Verify plumbing
.venv/bin/python tools/test_connection.py
.venv/bin/python research/backtest_signal.py   # options OOS honesty check
```

## ☁️ Cloud autonomy (`.github/workflows/`)
| Workflow | What | Cadence |
|---|---|---|
| `trade.yml` | account A agent | market hours |
| `trade-b.yml` | account B combined agent | 24/7 |
| `snapshot.yml` | account A daily track-record snapshot | daily |
| `snapshot-b.yml` | account B daily track-record snapshot | daily |

## 🚦 Risk gates (the heart of it)
Per account: **≤2%** risked/trade · **≤ cap** open positions · **5%** daily-loss halt ·
defined-risk (long only) · options 14–60 DTE, TP+50%/SL−50% · crypto stop 15% / TP 30% /
≤15% notional per coin, with a broker `stop_limit` on every position.

## 🎯 The honest thesis
Out-of-sample, the EMA/RSI signal beat buy-and-hold on **0 of 7** stocks and **0 of 4** coins.
We report that openly. Risk Gate competes on **discipline, safety, and transparency** — not a
pretended edge. Every trade is explainable; every risk is capped; every decision is journaled.
