# ✅ Hackathon Tracker — Alpaca AI Trading Agents ($6,000 pool)

Source of truth: the official lablab.ai rules (scraped Aug 2026).
Dates: **Kickoff Aug 28 10:00 AM CDT → Submissions close Sep 4 10:00 AM CDT.**
Work top-to-bottom. **The write-up is intentionally the LAST item.**

## 📋 Rules / eligibility (must all be true)
- [ ] 18+, not an Alpaca employee, not in a sanctioned country
- [x] Registered on **lablab.ai** for the hackathon
- [x] Joined the **lablab.ai Discord** (both are required)
- [ ] Agent is **autonomous** via **Alpaca Trading API**
- [ ] Uses **Alpaca MCP server OR CLI** (they emphasize **MCP**)
- [ ] **All strategies incorporate options** ✅ (agent buys calls/puts)
- [ ] Runs only in the **paper** environment (no real money)

## 🔌 Accounts & keys (you — needs your login)
- [ ] Dev paper account (any) for building — you already have one ✅
- [ ] **NEW, dedicated** paper account created **just for the final submission**
      (reused/existing accounts are NOT eligible for judging)
- [ ] Submission account balance set to **$100,000**
- [ ] Paper API keys for the submission account → pasted into `.env`
- [ ] Recorded the **Alpaca paper account ID** (required in the submission)

## 🧱 Build
- [x] Project scaffold + dry-run agent runs on real data
- [x] Signal engine (`signals.py`) — bull→call / bear→put
- [x] Risk gates (`risk.py`) — 2%/trade, ≤5 open, 5% daily-loss halt, long-only, DTE 14–60
- [x] Out-of-sample honesty check (`backtest_signal.py`)
- [ ] Decide **MCP vs CLI** (leaning MCP — it's the hackathon's core theme)
- [ ] Wire Alpaca: account/equity, positions  *(agent.py TODOs)*
- [ ] Wire option chain selection (ATM, DTE 14–60, liquid)
- [ ] Wire order placement (buy-to-open) + exits (TP +50% / SL −50% / near-expiry)
- [ ] Test paper stock order fills, then paper option order fills
- [ ] Autonomous schedule during market hours (`--loop` / cron)
- [ ] Flip `AGENT_MODE=LIVE_PAPER` on the **submission** account; run the week

## 📦 Deliverables (required for submission)
- [x] **Public GitHub repo, MIT-licensed** — https://github.com/fawad07/alpaca-options-agent
- [ ] Cover image
- [ ] **Video presentation** (demo the agent in action)
- [ ] **Slide presentation**
- [ ] Demo app platform + application URL
- [ ] **Alpaca paper account ID** (for P&L judging)
- [ ] Project title, short + long description, tech/category tags

## 📣 Social engagement (Build in Public — up to 5 posts, tag @lablabai + @AlpacaHQ)
- [ ] Post 1 — the build begins / the honest angle
- [ ] Post 2–4 — progress, a setback, a risk-gate save
- [ ] Post 5 — final results
- [ ] Submit up to 5 post links

## ⚖️ Judging = 5 criteria (all matter; P&L is only 1/5)
P&L · Technology Implementation · Creativity & Originality · Presentation & Execution · Social Engagement
→ Our edge: creativity + presentation + engagement + a clean, honest, well-documented agent.

## 📝 Write-up — DO THIS LAST
- [ ] One page: **AI logic · risk gates · Alpaca infrastructure** (`WRITEUP.md`)
- [ ] Attach final P&L screenshot; submit before Sep 4 10:00 AM CDT
