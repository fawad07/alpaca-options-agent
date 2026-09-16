#!/usr/bin/env bash
# ── run.sh — the ONE launcher for Risk Gate ────────────────────────────────
# Run with no args for a menu, or:  ./run.sh <command>
#   status | compare | dashboard | trade [a|b|both] | autopilot [secs] | results | market
# Replaces the old check.sh / trade-now.sh / autopilot.sh / run_agent.sh.
set -uo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python

_fire(){ # fire one cloud workflow and watch it
  local wf="$1"; echo "▶ firing $wf ..."
  gh workflow run "$wf" || { echo "  gh not logged in?"; return 1; }
  sleep 18
  local id; id=$(gh run list --workflow="$wf" --limit 1 --json databaseId -q '.[0].databaseId')
  gh run watch "$id" --exit-status --interval 10 || true
}

status(){  # cloud runs + both journals + A-vs-B P&L
  echo "▶ syncing latest from GitHub..."; git pull --rebase --autostash -q 2>/dev/null || true
  echo; echo "═══ CLOUD RUNS  (want 'success') ═══"
  echo "-- account A (trade.yml) --";   gh run list --workflow=trade.yml   --limit 3 2>/dev/null || echo "  (gh unavailable)"
  echo "-- account B (trade-b.yml) --"; gh run list --workflow=trade-b.yml --limit 3 2>/dev/null || true
  echo; echo "═══ DECISION JOURNALS ═══"
  echo "-- A --"; tail -n 5 ACTIVITY.md   2>/dev/null || echo "  (none yet)"
  echo "-- B --"; tail -n 5 ACTIVITY-B.md 2>/dev/null || echo "  (none yet)"
  echo; echo "═══ LIVE P&L — A vs B ═══"; $PY compare.py 2>/dev/null || echo "  (compare unavailable)"
}

compare(){   $PY compare.py 2>/dev/null; }
results(){   $PY results.py 2>/dev/null; }
market(){    $PY market_open.py 2>/dev/null; }
dashboard(){ echo "Dashboard → http://localhost:8095   (Ctrl-C to stop)"; $PY dashboard.py; }

trade(){  # force a cloud pass: a | b | both (default both)
  case "${1:-both}" in
    a) _fire trade.yml;;
    b) _fire trade-b.yml;;
    *) _fire trade.yml; _fire trade-b.yml;;
  esac
  git pull --rebase --autostash -q 2>/dev/null || true
  echo; echo "latest journal rows:"; tail -n 2 ACTIVITY.md 2>/dev/null; tail -n 2 ACTIVITY-B.md 2>/dev/null
}

autopilot(){  # local hourly backstop for the flaky GitHub scheduler (Mac must stay awake)
  local iv="${1:-3600}"
  echo "autopilot: every ${iv}s — fires account B (24/7) + account A (market hours). Ctrl-C to stop."
  echo "(tip: run  caffeinate -i ./run.sh autopilot  so the Mac doesn't sleep)"; echo
  while true; do
    local h m dow now; h=$((10#$(TZ=America/New_York date '+%H'))); m=$((10#$(TZ=America/New_York date '+%M')))
    dow=$(TZ=America/New_York date '+%u'); now=$(TZ=America/New_York date '+%Y-%m-%d %H:%M ET')
    local open=false
    if [ "$dow" -le 5 ]; then
      if [ "$h" -gt 9 ] && [ "$h" -lt 16 ]; then open=true; elif [ "$h" -eq 9 ] && [ "$m" -ge 30 ]; then open=true; fi
    fi
    echo "════ [$now] account B (crypto 24/7) ════"; _fire trade-b.yml
    if $open; then echo "════ [$now] market OPEN — account A ════"; _fire trade.yml
    else echo "════ [$now] market closed — skipping account A ════"; fi
    echo "── sleeping ${iv}s ──"; echo; sleep "$iv"
  done
}

menu(){
  echo "🛡️  Risk Gate"
  echo "  1) status      cloud runs + journals + A/B P&L"
  echo "  2) compare     A vs B side by side"
  echo "  3) dashboard   live web UI + equity chart"
  echo "  4) trade now   force a cloud pass (A + B)"
  echo "  5) autopilot   hourly local backstop"
  echo "  6) results     single-account P&L"
  echo "  7) market      open / closed"
  read -r -p "  choose [1-7]: " ch
  case "$ch" in
    1) status;; 2) compare;; 3) dashboard;; 4) trade both;;
    5) autopilot;; 6) results;; 7) market;; *) echo "nothing chosen";;
  esac
}

case "${1:-menu}" in
  status)        status;;
  compare)       compare;;
  dashboard|dash) dashboard;;
  trade)         trade "${2:-both}";;
  autopilot)     autopilot "${2:-3600}";;
  results)       results;;
  market)        market;;
  menu|"")       menu;;
  *) echo "usage: ./run.sh [status|compare|dashboard|trade [a|b|both]|autopilot [secs]|results|market]";;
esac
