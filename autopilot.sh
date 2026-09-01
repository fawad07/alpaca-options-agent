#!/usr/bin/env bash
# ── autopilot.sh — local hourly backstop for the flaky GitHub scheduler ─────
# While this is running (Mac awake + this terminal open), it fires ONE cloud
# trade pass every hour during US market hours. That keeps trades flowing and,
# crucially, keeps your +50%/-50% EXITS managed between GitHub's rare runs.
# Off-hours it just waits. Press Ctrl-C to stop it.
#
#   ./autopilot.sh              # fire every hour (3600s)
#   ./autopilot.sh 1800         # or every 30 min
#   caffeinate -i ./autopilot.sh   # also stop the Mac from idle-sleeping
#
# NOTE: this needs your Mac ON and this window open. If the Mac sleeps, it
# pauses. For true 24/7 hands-off reliability, use Render (Option 2) instead.
set -uo pipefail
cd "$(dirname "$0")"

INTERVAL="${1:-3600}"          # seconds between passes (default 1 hour)

echo "autopilot: firing a cloud pass every ${INTERVAL}s during market hours."
echo "           keep this window open. Ctrl-C to stop."
echo

while true; do
  h=$((10#$(TZ=America/New_York date '+%H')))     # 10# = force base-10 (avoid 08/09 octal error)
  m=$((10#$(TZ=America/New_York date '+%M')))
  dow=$(TZ=America/New_York date '+%u')           # 1=Mon .. 7=Sun
  now=$(TZ=America/New_York date '+%Y-%m-%d %H:%M ET')

  open=false
  if [ "$dow" -le 5 ]; then
    if   [ "$h" -gt 9 ] && [ "$h" -lt 16 ]; then open=true
    elif [ "$h" -eq 9 ] && [ "$m" -ge 30 ]; then open=true
    fi
  fi

  if $open; then
    echo "════ [$now] market OPEN — firing a cloud trade pass ════"
    ./trade-now.sh
  else
    echo "════ [$now] market closed — skipping (will re-check next cycle) ════"
  fi

  echo "── sleeping ${INTERVAL}s (Ctrl-C to stop) ──"
  echo
  sleep "$INTERVAL"
done
