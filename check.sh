#!/usr/bin/env bash
# ── Daily health check for the Risk Gate cloud agent ────────────────────────
# Shows everything you need in one shot: recent cloud runs, the decision
# journal, and live account P&L. Run it during market hours on trading days.
#   ./check.sh
set -uo pipefail
cd "$(dirname "$0")"

echo "▶ Getting the latest journal from GitHub..."
git pull --rebase --autostash -q 2>/dev/null || echo "  (skipped git pull)"

echo
echo "═══════ 1) LAST 8 CLOUD RUNS  —  you want the word 'success' ═══════"
gh run list --workflow=trade.yml --limit 8 \
  || echo "  (gh unavailable — check the Actions tab on GitHub instead)"

echo
echo "═══════ 2) DECISION JOURNAL  —  what the agent decided each run ═══════"
if [ -f ACTIVITY.md ]; then
  tail -n 16 ACTIVITY.md
else
  echo "  No journal yet — no cloud run has completed."
fi

echo
echo "═══════ 3) LIVE ACCOUNT P&L ═══════"
.venv/bin/python results.py 2>/dev/null | sed -n '/RISK GATE/,/Paste into/p' \
  || echo "  (couldn't read the account — check your keys in .env)"

echo
echo "───────────────────────────────────────────────────────────────────"
echo "Need to force a trade pass right now?   ./trade-now.sh"
echo "───────────────────────────────────────────────────────────────────"
