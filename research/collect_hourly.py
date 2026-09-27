"""
collect_hourly.py — archive Alpaca's 24/7 hourly equity before it ages out.

Alpaca's `continuous` portfolio history (24/7, weekends included) only reaches back
~30 days. This appends the latest hourly points into a growing local CSV, so we keep
an UNLIMITED weekend/hourly record for a future A-vs-B intraday chart. It dedupes by
timestamp, so running it daily (well inside the 30-day window) never loses a point and
never double-counts. Account-aware via DEPLOY_ACCOUNT, mirroring refresh_stats.py.

Run:  DEPLOY_ACCOUNT=B .venv/bin/python research/collect_hourly.py
Output:
  research/equity_hourly.csv     (account A)
  research/equity_hourly-B.csv   (account B — the one with weekend crypto movement)
"""
from __future__ import annotations
import os, csv, sys, asyncio, datetime as dt
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # import project root
from accounts import current_account
from mcp_client import mcp_session, call

HERE = os.path.dirname(__file__)
ET = ZoneInfo('America/New_York')
_ACCT = current_account()
_SUFFIX = '' if _ACCT.name in ('A', 'default') else f'-{_ACCT.name}'
OUT = os.path.join(HERE, f"equity_hourly{_SUFFIX}.csv")
FIELDS = ['timestamp', 'datetime_et', 'equity']


async def _fetch() -> dict:
    """Pull the widest continuous (24/7) hourly window Alpaca allows. Intraday history
    is capped at UNDER 30 days (30D/1M are rejected as >30), so we request 28D — plenty
    of overlap for a daily run, and a deep backfill on the very first run."""
    async with mcp_session(_ACCT) as s:
        h = await call(s, 'get_portfolio_history',
                       {'period': '28D', 'timeframe': '1H',
                        'intraday_reporting': 'continuous'})
    if not isinstance(h, dict) or not h.get('timestamp'):
        raise RuntimeError(f"portfolio_history returned no data: {str(h)[:200]}")
    return h


def _load_existing() -> dict:
    """Existing archive keyed by unix timestamp (the dedupe key)."""
    rows = {}
    if os.path.exists(OUT):
        try:
            for r in csv.DictReader(open(OUT)):
                rows[int(r['timestamp'])] = r
        except Exception:
            pass
    return rows


def main() -> None:
    h = asyncio.run(_fetch())
    ts, eq = h.get('timestamp') or [], h.get('equity') or []
    have = _load_existing()
    added = 0
    for t, e in zip(ts, eq):
        if not e:                              # skip null/zero valuation points
            continue
        t = int(t)
        if t in have:                          # already archived — dedupe
            continue
        d = dt.datetime.fromtimestamp(t, ET)
        have[t] = {'timestamp': t,
                   'datetime_et': f"{d:%Y-%m-%d %H:%M}",
                   'equity': round(float(e), 2)}
        added += 1
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for t in sorted(have):                 # keep chronological
            w.writerow(have[t])
    print(f"[collect_hourly] account {_ACCT.name}: +{added} new point(s), "
          f"{len(have)} total → {os.path.basename(OUT)}")


if __name__ == '__main__':
    main()
