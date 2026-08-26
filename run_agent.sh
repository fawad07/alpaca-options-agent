#!/bin/bash
# ─────────────────────────────────────────────────────────────
# run_agent.sh — one agent pass, but ONLY during US market hours.
# Safe to fire all day; it exits immediately when the market is closed.
#
# HANDS-OFF (cron) — run every 15 minutes:
#   crontab -e
#   then add this line (keep the full path):
#   */15 * * * * /Users/fawad/Desktop/alpaca-options-agent/run_agent.sh
#
# SIMPLEST (no cron) — just leave this running in a Terminal at market open:
#   cd ~/Desktop/alpaca-options-agent && .venv/bin/python agent.py --loop 900
#
# Either way: set AGENT_MODE=LIVE_PAPER in .env first, and keep the Mac awake
# during market hours (cron/loops don't run while the machine is asleep).
# ─────────────────────────────────────────────────────────────
cd "$(dirname "$0")" || exit 1
PY=".venv/bin/python"

if [ "$("$PY" market_open.py 2>/dev/null)" != "OPEN" ]; then
  exit 0   # market closed — do nothing
fi

mkdir -p logs
echo "=== run $(date) ===" >> logs/agent_cron.log
"$PY" agent.py >> logs/agent_cron.log 2>&1
