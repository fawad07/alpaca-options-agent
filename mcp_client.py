"""
mcp_client.py — thin async wrapper around Alpaca's MCP server.
The agent opens ONE session per run and calls tools through it.
Alpaca wraps results as {"_alpaca_mcp_security":..., "data": ...}; we unwrap `data`.
"""
from __future__ import annotations
import json
from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp_test import server_params   # reuse the paper-keyed server launch


def _parse(result):
    for c in result.content:
        text = getattr(c, 'text', None)
        if text:
            try:
                obj = json.loads(text)
                return obj.get('data', obj) if isinstance(obj, dict) else obj
            except Exception:
                return text
    return None


@asynccontextmanager
async def mcp_session():
    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def call(session, tool: str, args: dict | None = None):
    return _parse(await session.call_tool(tool, args or {}))


# ── high-level helpers the agent uses ─────────────────────────
import datetime as _dt


async def account(session) -> dict:
    return await call(session, 'get_account_info') or {}


async def option_positions(session) -> list:
    data = await call(session, 'get_all_positions')
    rows = data if isinstance(data, list) else (data or {}).get('positions', []) or []
    return [p for p in rows if 'option' in str(p.get('asset_class', '')).lower()]


async def find_atm_contract(session, underlying: str, right: str, price: float,
                            min_dte: int, max_dte: int, target_dte: int = 30) -> dict | None:
    """Pick the tradable contract nearest to at-the-money, at the expiration
    closest to `target_dte` within the [min_dte, max_dte] window."""
    today = _dt.date.today()
    lo = (today + _dt.timedelta(days=min_dte)).isoformat()
    hi = (today + _dt.timedelta(days=max_dte)).isoformat()
    data = await call(session, 'get_option_contracts', {
        'underlying_symbols': underlying, 'type': right, 'status': 'active',
        'expiration_date_gte': lo, 'expiration_date_lte': hi,
        'strike_price_gte': round(price * 0.90), 'strike_price_lte': round(price * 1.10),
        'limit': 500,
    })
    lst = [c for c in (data or {}).get('option_contracts', []) if c.get('tradable')]
    if not lst:
        return None
    target = today + _dt.timedelta(days=target_dte)
    exps = {c['expiration_date'] for c in lst}
    best_exp = min(exps, key=lambda e: abs(_dt.date.fromisoformat(e) - target))
    cands = [c for c in lst if c['expiration_date'] == best_exp]
    return min(cands, key=lambda c: abs(float(c['strike_price']) - price))


async def option_premium(session, option_symbol: str) -> float | None:
    data = await call(session, 'get_option_snapshot', {'symbols': option_symbol})
    snap = (data or {}).get('snapshots', {}).get(option_symbol, {})
    q = snap.get('latestQuote') or {}
    bid, ask = q.get('bp'), q.get('ap')
    if bid and ask and ask > 0:
        return (float(bid) + float(ask)) / 2
    t = snap.get('latestTrade') or {}
    if t.get('p'):
        return float(t['p'])
    db = snap.get('dailyBar') or {}
    return float(db['c']) if db.get('c') else None


async def buy_option(session, option_symbol: str, qty: int) -> dict:
    return await call(session, 'place_option_order', {
        'symbol': option_symbol, 'qty': str(qty), 'side': 'buy',
        'type': 'market', 'time_in_force': 'day', 'position_intent': 'buy_to_open'})


async def close_option(session, option_symbol: str, percentage: float = 100.0) -> dict:
    return await call(session, 'close_position',
                      {'symbol_or_asset_id': option_symbol, 'percentage': percentage})
