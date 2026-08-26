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
- [x] Submission account balance set to **$100,000** ✅
- [x] Paper API keys pasted into `.env` (git-ignored) ✅
- [x] Options trading enabled (Level 3) ✅
- [x] Recorded the **Alpaca paper account ID**: `PA327FXF8G6D` (submit this)
- [x] Connection verified with `test_connection.py` ✅

## 🧱 Build
- [x] Project scaffold + dry-run agent runs on real data
- [x] Signal engine (`signals.py`) — bull→call / bear→put
- [x] Risk gates (`risk.py`) — 2%/trade, ≤5 open, 5% daily-loss halt, long-only, DTE 14–60
- [x] Out-of-sample honesty check (`backtest_signal.py`)
- [x] Decided **MCP** — official `alpaca-mcp-server` (72 tools); connection verified via `mcp_test.py` ✅
- [x] Fresh dedicated account confirmed (created 2026-08-25) ✅
- [x] Wire agent to MCP: account/equity, positions ✅
- [x] Wire option chain selection (ATM, ~30 DTE) — verified via `test_select.py` ✅
- [x] Wire order placement (buy-to-open) + exits (TP +50% / SL −50%) ✅ (code-complete)
- [ ] **Place first real paper option order** (must be during US market hours, 9:30–16:00 ET)
- [x] Autonomous scheduler built (`run_agent.sh` + `market_open.py`, cron-ready) — start at market open
- [ ] Flip `AGENT_MODE=LIVE_PAPER` on the **submission** account; run the week

## 📦 Deliverables (required for submission)
- [x] **Public GitHub repo, MIT-licensed** — https://github.com/fawad07/alpaca-options-agent
- [ ] Cover image — draft ready (`cover.html` → open in browser, export/screenshot to PNG)
- [ ] **Video presentation** — script ready (`VIDEO_SCRIPT.md`); record during a live run
- [ ] **Slide presentation** — deck drafted (`SLIDES.md`); finalize with results
- [x] Demo app built — live dashboard (`dashboard.py` → localhost:8095); show in video, or deploy for a public URL
- [ ] **Alpaca paper account ID** (for P&L judging)
- [ ] Project title, short + long description, tech/category tags

## 📣 Social engagement (Build in Public — up to 5 posts, tag @lablabai + @AlpacaHQ)
> All 5 posts are drafted in `SOCIAL.md` — just add a screenshot and post.
- [ ] Post 1 — the build begins / the honest angle
- [ ] Post 2–4 — progress, a setback, a risk-gate save
- [ ] Post 5 — final results
- [ ] Submit up to 5 post links

## ⚖️ Judging = 5 criteria (all matter; P&L is only 1/5)
P&L · Technology Implementation · Creativity & Originality · Presentation & Execution · Social Engagement
→ Our edge: creativity + presentation + engagement + a clean, honest, well-documented agent.

## 📝 Write-up — DO THIS LAST
- [x] Write-up pre-filled (`WRITEUP.md`) — only final P&L numbers + screenshot remain
- [ ] Drop in final P&L numbers + screenshot; submit before Sep 4 10:00 AM CDT
- [ ] (optional) Deploy dashboard to Render for a public demo URL — see `DEPLOY.md`
