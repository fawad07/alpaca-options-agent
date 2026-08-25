# 🗓️ Week Plan — Alpaca AI Trading Agents Hackathon (Aug 28 – Sep 4)

**Goal:** an autonomous AI **options** agent on an Alpaca **paper** ($100k) account,
with clear risk gates and a one-page write-up. Judged on P&L + creativity/engagement.

**Honest strategy:** P&L is only **1 of 5** judging criteria (the others: Technology,
Creativity, Presentation & Execution, Social Engagement). One week of P&L is mostly luck,
so we compete on **creativity + presentation + engagement + a clean, honest, documented
agent** — that's where we can actually win. Zero real money at risk (paper only).

**Prize pool $6,000:** 🥇$2,500 · 🥈$1,500 · 🥉$1,000 · plus 2 Social Engagement teams
($500 + 1-month Algo Trader Plus each).

**Rules that shape the build (from the official page):**
- Must use **Alpaca MCP server OR CLI** (they call MCP "the core of the hackathon theme").
- **All strategies must include options.**
- Develop on any paper account, but **SUBMIT with a brand-new dedicated paper account**
  (reused accounts are disqualified); set it to **$100,000**; submit its **account ID**.
- Deliverables: **public MIT-licensed GitHub repo**, cover image, **video**, **slides**,
  demo URL, the account ID, the one-page write-up, and up to **5 social posts**.
- Register on **lablab.ai AND the Discord**. Teams 1–6.

## What we reuse (so we're not starting cold)
| From | Reused as |
|---|---|
| `ai-trading-pipeline/pipeline.py` | `signals.py` (EMA/RSI/ATR features + directional logic) and `backtest_signal.py` (out-of-sample honesty check) |
| `Trading_signal_production/config.py` | `config.py` (central settings + .env keys pattern) |
| `Trading_signal_production` risk/paper discipline | `risk.py` (risk gates), paper-only design |
| `crypto-companion` data fetch | `data.py` (free Yahoo daily bars for the underlyings) |

## Daily plan

**Day 0 — Setup (you; do before/on Aug 28)**
- Register on **lablab.ai** for the hackathon **and join the Discord** (both required).
- Dev: use any paper account to build. **For submission**, create a **brand-new dedicated**
  Alpaca paper account, set balance to **$100,000**, and note its **account ID**.
- Generate the submission account's paper API keys → copy `.env.example` to `.env`, paste them.
- (Me, in parallel) **MIT LICENSE + local git repo** ready to push to a public GitHub repo.

**Day 1 — Connect to Alpaca**
- `pip install -r requirements.txt`; confirm `alpaca-py` connects to the paper account.
- Read account equity + positions. Place ONE test paper **stock** order to confirm plumbing.
- Fill the `get_equity()` / `get_open_positions()` TODOs in `agent.py`.

**Day 2 — Options plumbing (the required part)**
- Learn Alpaca's option chain API; fetch a chain for SPY.
- Place ONE test paper **option** order (buy 1 call). Confirm fill + position shows up.
- Fill the `select_contract()` TODO (nearest-ATM, DTE 14–60, liquid) and `place_order()`.

**Day 3 — Signal → option intent**
- Verify `signals.py` produces bull/bear/neutral; map bull→call, bear→put (already wired).
- Run `backtest_signal.py` for the honest out-of-sample read; note results for the write-up.

**Day 4 — Risk gates (judges want these)**
- Confirm all gates in `risk.py`: 2% max risk/trade, ≤5 concurrent, 5% daily-loss halt,
  defined-risk (long only), DTE window, take-profit/stop. Tune limits.
- Fill `manage_positions()` TODO: take-profit +50%, stop −50%, close near expiry.

**Day 5 — Autonomy + monitoring**
- Run the agent on a schedule (`--loop`, or macOS `cron`/`launchd`) during market hours.
- Add a simple status view / log review (reuse the companion dashboard if time).

**Day 6 — Live paper run + engagement**
- Flip `AGENT_MODE=LIVE_PAPER`; let it trade the paper account. Watch logs, fix issues.
- Post progress on socials (screenshots, the honesty angle) → the 2 Social Engagement Awards.

**Day 6.5 — Presentation assets (Presentation & Execution is a full criterion)**
- Record a short **video demo** of the agent trading; build a **slide deck**.
- Make a **cover image**; confirm the **public MIT GitHub repo** is pushed + demo URL works.

**Day 7 (Sep 4, before 10:00 AM CDT) — Finalize + WRITE-UP (last)**
- Capture final P&L + screenshots; grab the **paper account ID**.
- Write the one-page `WRITEUP.md`: **AI logic · risk gates · Alpaca infrastructure**.
- Submit on lablab.ai: repo, video, slides, cover, demo URL, **account ID**, up to **5 social posts**.

## Hard boundaries
- **Paper only.** Never wire a real-money account.
- **Defined-risk only.** The agent buys options; it never sells naked.
- You do all account creation / key generation / submission; the code never sees real money.
