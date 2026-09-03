# Autonomous trading in the cloud (no Mac needed)

So the agent trades itself during Aug 28–Sep 4 without you keeping a computer awake.
It runs `cron_once.py` every 15 min; that only acts during US market hours and needs
`AGENT_MODE=LIVE_PAPER` + your paper keys. **Pick ONE of the two options** (running
both would double-trade).

## Option A — GitHub Actions ⭐ recommended (FREE)
Your repo is public, so Actions minutes are free.
1. On GitHub: **repo → Settings → Secrets and variables → Actions → New repository secret**
   - `ALPACA_API_KEY` = your paper key
   - `ALPACA_SECRET_KEY` = your paper secret
2. The workflow `.github/workflows/trade.yml` is already in the repo. Enable Actions if
   prompted (**Actions** tab → "I understand… enable").
3. It runs every 15 min during market hours automatically. You can also click
   **Actions → risk-gate-agent → Run workflow** to fire it manually.
- ⚠️ GitHub's scheduler can be **delayed a few minutes** under load — fine for a 15-min
  cadence, not for split-second timing.

## Option B — Render Cron Job (paid, small cost)
`render.yaml` also defines a `risk-gate-agent` cron service.
1. Deploy the blueprint (same as the dashboard). Set `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`.
2. Render runs it on the schedule. Note: **Render Cron Jobs are billed** (small per-run) —
   only use this if you'd rather not use GitHub Actions.

## Either way
- It trades your **paper** submission account (PA327FXF8G6D) — no real money.
- The **dashboard** (Option in DEPLOY.md) is separate and just *shows* what the agent did.
- To pause trading: disable the workflow (Actions tab) or the Render cron job.
