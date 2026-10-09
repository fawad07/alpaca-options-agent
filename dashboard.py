"""
dashboard.py — live status dashboard for the Risk Gate agent.

Shows, through the Alpaca MCP server: account equity + P&L, open option
positions, recent orders, and the agent's recent decisions (from the trade log).
Auto-refreshes. Read-only — it never places trades.

Run:   .venv/bin/python dashboard.py    →   http://localhost:8095
"""
from __future__ import annotations
import os, csv, asyncio, json, time, re, hmac
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request, abort, make_response, redirect
import config as C
from mcp_client import mcp_session, account, option_positions, crypto_positions, call, _rows
from accounts import ACCOUNT_A, ACCOUNT_B

app = Flask(__name__)
_cache = {'t': 0.0, 'data': None}
_chart = {'t': 0.0, 'data': None}

# Access gate. Local runs bind 127.0.0.1 and may stay open; a public deploy (a host
# like Render sets $PORT and we bind 0.0.0.0) MUST have a token or we refuse to boot —
# so account data is never world-readable by accident (fail-closed).
DASH_TOKEN = os.getenv('DASH_TOKEN', '')
_PUBLIC = bool(os.getenv('PORT'))          # a host provides $PORT → we're internet-facing

if _PUBLIC and not DASH_TOKEN:
    raise SystemExit(
        "Refusing to start: $PORT is set (public deploy) but DASH_TOKEN is unset. "
        "Set DASH_TOKEN so the dashboard isn't world-readable, then redeploy.")


def _token_ok(val: str) -> bool:
    """Constant-time compare — no timing side-channel on the token."""
    return bool(val) and hmac.compare_digest(str(val), DASH_TOKEN)


@app.before_request
def _gate():
    if not DASH_TOKEN:
        return                              # local, intentionally open (localhost-bound)
    # Preferred: token via header or the httponly cookie — never lands in logs/history.
    if _token_ok(request.headers.get('X-Dash-Token', '')) or \
       _token_ok(request.cookies.get('dash_token', '')):
        return
    # First browser visit may pass ?token=… — accept it ONCE, stash it in an httponly
    # cookie, and redirect to a clean URL so the secret doesn't linger in the address
    # bar, history, or access logs on later requests.
    if _token_ok(request.args.get('token', '')):
        resp = make_response(redirect(request.path))
        resp.set_cookie('dash_token', DASH_TOKEN, httponly=True,
                        secure=_PUBLIC, samesite='Strict', max_age=7 * 24 * 3600)
        return resp
    abort(403)


def market_status() -> str:
    et = datetime.now(ZoneInfo('America/New_York'))
    open_ = et.weekday() < 5 and (et.hour, et.minute) >= (9, 30) and et.hour < 16
    return 'OPEN' if open_ else 'CLOSED'


def read_decisions(n: int = 14) -> list:
    """Recent agent decisions from the committed journals (activity.csv = A,
    activity-B.csv = B) — the trade log is cloud-only/ephemeral, the journal is what
    the workflows commit back. Merged, newest first. Reflects the last `git pull`."""
    here = os.path.dirname(__file__)
    rows = []
    for fn, default_acct in (('activity.csv', 'A'), ('activity-B.csv', 'B')):
        path = os.path.join(here, fn)
        if not os.path.exists(path):
            continue
        try:
            for r in csv.DictReader(open(path)):
                rows.append({'ts': r.get('timestamp_et', ''),
                             'acct': r.get('account') or default_acct,
                             'summary': r.get('summary', '')})
        except Exception:
            pass
    rows.sort(key=lambda r: r['ts'])
    return rows[-n:][::-1]


def _f(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def _short_sym(sym: str) -> str:
    """Compact display: 'AAPL261016C00330000' → 'AAPL 330C'; 'ETHUSD'/'ETH/USD' → 'ETH'."""
    s = str(sym or '')
    m = re.match(r'^([A-Z]+)(\d{6})([CP])(\d{8})$', s)
    if m:
        return f"{m.group(1)} {int(m.group(4)) / 1000:g}{m.group(3)}"
    if s.replace('/', '').upper().endswith('USD'):
        return s.replace('/', '')[:-3]
    return s


def fmt_pos(p: dict) -> dict:
    return {'symbol': _short_sym(p.get('symbol', '')),
            'qty': p.get('qty'), 'value': _f(p.get('market_value')),
            'pl': _f(p.get('unrealized_pl')), 'plpc': _f(p.get('unrealized_plpc')) * 100}


def fmt_order(o: dict) -> dict:
    return {'symbol': o.get('symbol'), 'side': o.get('side'), 'qty': o.get('qty'),
            'type': o.get('order_type') or o.get('type'), 'status': o.get('status'),
            'time': (o.get('submitted_at') or o.get('created_at') or '')[:19].replace('T', ' ')}


async def _fetch_b():
    """Account B headline numbers + its positions (options + crypto)."""
    async with mcp_session(ACCOUNT_B) as s:
        a = await account(s)
        pos = await option_positions(s) + await crypto_positions(s)
    eq, start = _f(a.get('equity')), C.ACCOUNT_START
    nums = {'equity': eq, 'cash': _f(a.get('cash')),
            'pl': eq - start, 'pl_pct': (eq - start) / start * 100 if start else 0}
    return nums, pos


async def _fetch_live():
    async with mcp_session() as s:
        acct = await account(s)
        pos = await option_positions(s)
        try:
            orders = _rows(await call(s, 'get_orders', {'status': 'all', 'limit': 15}))
        except Exception:
            orders = []
        return acct, pos, orders


def build_status() -> dict:
    now = time.time()
    if _cache['data'] and now - _cache['t'] < 15:
        return _cache['data']
    keyed = bool(C.ALPACA_API_KEY) and not C.ALPACA_API_KEY.lower().startswith('your_')
    data = {'mode': C.MODE, 'market': market_status(),
            'updated': datetime.now().strftime('%H:%M:%S'),
            'connected': False, 'account': None, 'positions': [], 'orders': [],
            'log': read_decisions()}
    if keyed:
        try:
            acct, pos, orders = asyncio.run(_fetch_live())
            eq, start = _f(acct.get('equity')), C.ACCOUNT_START
            data['connected'] = True
            data['account'] = {
                'equity': eq, 'cash': _f(acct.get('cash')),
                'buying_power': _f(acct.get('buying_power')),
                'options_bp': _f(acct.get('options_buying_power')),
                'pl': eq - start, 'pl_pct': (eq - start) / start * 100 if start else 0}
            data['positions'] = [fmt_pos(p) for p in pos]
            data['orders'] = [fmt_order(o) for o in orders][:15]
            try:
                data['accountB'], bpos = asyncio.run(_fetch_b())
                data['positionsB'] = [fmt_pos(p) for p in bpos]
            except Exception as e:
                data['accountB_err'] = str(e)[:120]
        except Exception as e:
            data['error'] = str(e)[:200]
    _cache.update(t=now, data=data)
    return data


# Equity curve source = the 24/7 CONTINUOUS hourly series (weekends included), keyed by
# unix seconds. Two parts merged: (1) the growing local archive (unlimited history —
# research/equity_hourly*.csv, written daily by collect_hourly.py) and (2) a live Alpaca
# fetch for the freshest hours not yet archived. This is why weekend crypto moves show up
# on the one main chart and why it keeps history past Alpaca's rolling 28-day window.
_ARCHIVE = {'A': 'research/equity_hourly.csv', 'B': 'research/equity_hourly-B.csv'}
# Sanity band — Alpaca's `continuous` mode glitches when its window reaches the account's
# funding cashflow: it adds base_value and ~doubles equity. We request 25D (clear of it)
# AND drop any point outside this band, so a glitch can never corrupt the chart.
_SANE_HI = C.ACCOUNT_START * 1.5
_SANE_LO = C.ACCOUNT_START * 0.3
_sane = lambda v: v is not None and _SANE_LO < v < _SANE_HI


def _read_archive(rel: str) -> dict:
    """Archived hourly points {unix_ts: equity} — empty until the collector has run."""
    out, path = {}, os.path.join(os.path.dirname(__file__), rel)
    if os.path.exists(path):
        try:
            for r in csv.DictReader(open(path)):
                v = _f(r['equity'])
                if _sane(v):
                    out[int(r['timestamp'])] = v
        except Exception:
            pass
    return out


async def _live_continuous(acct) -> dict:
    """Freshest 24/7 hourly points from Alpaca {unix_ts: equity}. Uses 25D (not the 28D
    max) to avoid the funding-date glitch, and sanity-filters anything implausible."""
    async with mcp_session(acct) as s:
        h = await call(s, 'get_portfolio_history',
                       {'period': '25D', 'timeframe': '1H',
                        'intraday_reporting': 'continuous'})
    if not isinstance(h, dict):
        return {}
    ts, eq = h.get('timestamp') or [], h.get('equity') or []
    return {int(t): _f(e) for t, e in zip(ts, eq) if _sane(_f(e))}


def build_chart() -> dict:
    now = time.time()
    if _chart['data'] and now - _chart['t'] < 60:
        return _chart['data']
    series, errs = {}, {}
    for key, acct in (('A', ACCOUNT_A), ('B', ACCOUNT_B)):
        pts = _read_archive(_ARCHIVE[key])               # unlimited history from disk
        try:
            pts.update(asyncio.run(_live_continuous(acct)))  # + freshest live hours
        except Exception as e:
            errs[key + '_err'] = str(e)[:120]
        series[key] = pts
    A, B = series['A'], series['B']
    stamps = sorted(set(A) | set(B))                     # shared axis, hourly (unix secs)
    # Labels/tooltips in US MARKET TIME (ET), same for every viewer regardless of location.
    et = ZoneInfo('America/New_York')
    labels = [f"{(d := datetime.fromtimestamp(t, et)):%b} {d.day}" for t in stamps]  # x-axis
    tips = [f"{datetime.fromtimestamp(t, et):%b %d, %I%p}".replace(' 0', ' ') for t in stamps]
    out = {'start': C.ACCOUNT_START, 'labels': labels, 'tips': tips,
           'A': [A.get(t) for t in stamps], 'B': [B.get(t) for t in stamps], **errs}
    _chart.update(t=now, data=out)
    return out


@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    return jsonify(build_status())

@app.route('/api/chart')
def api_chart():
    return jsonify(build_chart())


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8095))   # Render/hosts provide $PORT
    # Local runs bind to localhost only (don't expose account data on the LAN).
    # A host (Render) sets $PORT, so there we bind 0.0.0.0 so it's routable.
    host = '0.0.0.0' if os.getenv('PORT') else '127.0.0.1'
    print(f"\n  Risk Gate — live status dashboard")
    print(f"  Open:  http://localhost:{port}\n")
    app.run(host=host, port=port, debug=False, threaded=True)
