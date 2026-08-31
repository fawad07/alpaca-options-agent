#!/usr/bin/env bash
# ── Force ONE immediate trade pass in the cloud, then show the result ───────
# Use this any time you want to GUARANTEE a run (don't wait for the schedule).
# Safe to run repeatedly — the risk gates still cap positions at 5.
#   ./trade-now.sh
set -uo pipefail
cd "$(dirname "$0")"

echo "▶ Firing a cloud run..."
gh workflow run trade.yml || { echo "  couldn't trigger — is 'gh' logged in?"; exit 1; }
echo "  waiting for it to start..."
sleep 20
id=$(gh run list --workflow=trade.yml --limit 1 --json databaseId -q '.[0].databaseId')
echo "  run $id — watching until it finishes..."
gh run watch "$id" --exit-status --interval 10 || true

echo
echo "▶ What it did (latest journal rows):"
git pull --rebase --autostash -q 2>/dev/null || true
tail -n 3 ACTIVITY.md 2>/dev/null || echo "  (no journal row yet — re-run ./check.sh in a moment)"
