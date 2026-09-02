"""
dashboard.py — live status dashboard for the Risk Gate agent.

Shows, through the Alpaca MCP server: account equity + P&L, open option
positions, recent orders, and the agent's recent decisions (from the trade log).
Auto-refreshes. Read-only — it never places trades.

Run:   .venv/bin/python dashboard.py    →   http://localhost:8095
"""
from __future__ import annotations
import os, asyncio, json, time, re
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request, abort
import config as C
from mcp_client import mcp_session, account, option_positions, call, _rows

app = Flask(__name__)
_cache = {'t': 0.0, 'data': None}

# Optional access gate: if DASH_TOKEN is set, every request needs ?token=…
# (handy when the dashboard is deployed to a public URL). Leave unset = open.
DASH_TOKEN = os.getenv('DASH_TOKEN', '')

@app.before_request
def _gate():
    if DASH_TOKEN and request.args.get('token') != DASH_TOKEN:
        abort(403)


def market_status() -> str:
    et = datetime.now(ZoneInfo('America/New_York'))
    open_ = et.weekday() < 5 and (et.hour, et.minute) >= (9, 30) and et.hour < 16
    return 'OPEN' if open_ else 'CLOSED'


def read_log(n: int = 15) -> list:
    try:
        lines = C.TRADE_LOG.read_text().strip().splitlines()[-n:]
        return [json.loads(l) for l in reversed(lines)]
    except Exception:
        return []


def _f(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def _right(sym: str) -> str:
    m = re.search(r'\d{6}([CP])\d{8}$', sym or '')
    return {'C': 'CALL', 'P': 'PUT'}.get(m.group(1), '') if m else ''


def fmt_pos(p: dict) -> dict:
    return {'symbol': p.get('symbol'), 'right': _right(p.get('symbol', '')),
            'qty': p.get('qty'), 'avg': _f(p.get('avg_entry_price')),
            'price': _f(p.get('current_price')), 'value': _f(p.get('market_value')),
            'pl': _f(p.get('unrealized_pl')), 'plpc': _f(p.get('unrealized_plpc')) * 100}


def fmt_order(o: dict) -> dict:
    return {'symbol': o.get('symbol'), 'side': o.get('side'), 'qty': o.get('qty'),
            'type': o.get('order_type') or o.get('type'), 'status': o.get('status'),
            'time': (o.get('submitted_at') or o.get('created_at') or '')[:19].replace('T', ' ')}


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
            'log': read_log()}
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
        except Exception as e:
            data['error'] = str(e)[:200]
    _cache.update(t=now, data=data)
    return data


@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    return jsonify(build_status())


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8095))   # Render/hosts provide $PORT
    # Local runs bind to localhost only (don't expose account data on the LAN).
    # A host (Render) sets $PORT, so there we bind 0.0.0.0 so it's routable.
    host = '0.0.0.0' if os.getenv('PORT') else '127.0.0.1'
    print(f"\n  Risk Gate — live status dashboard")
    print(f"  Open:  http://localhost:{port}\n")
    app.run(host=host, port=port, debug=False, threaded=True)
