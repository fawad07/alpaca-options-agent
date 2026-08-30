"""
results.py — pull the final numbers for the presentation in one command.

Run it (during or after the trading week) with your paper keys loaded:
    .venv/bin/python results.py

It reads the submission paper account through the Alpaca MCP server and prints
slide-ready lines for presentation.pptx slide 9 + WRITEUP.md, then saves
results.json (and a plain results.txt you can copy from).
"""
from __future__ import annotations
import asyncio, json, datetime as _dt
import config
from mcp_client import mcp_session, call, account, option_positions


async def _orders(session):
    """All orders, newest first — used for trade count + win/loss on closed options."""
    data = await call(session, 'get_orders', {'status': 'all', 'limit': 500})
    return data if isinstance(data, list) else (data or {}).get('orders', []) or []


async def _portfolio_history(session):
    """Equity curve since the account started, for the P&L chart / high-water mark."""
    try:
        return await call(session, 'get_portfolio_history',
                          {'period': '1M', 'timeframe': '1D'}) or {}
    except Exception:
        return {}


async def main():
    async with mcp_session() as session:
        acct = await account(session)
        positions = await option_positions(session)
        orders = await _orders(session)
        hist = await _portfolio_history(session)

    equity = float(acct.get('equity', 0) or 0)
    last_equity = float(acct.get('last_equity', 0) or 0)
    start = float(config.ACCOUNT_START)
    total_pl = equity - start
    total_pl_pct = (total_pl / start * 100) if start else 0.0
    day_pl = equity - last_equity

    # option orders only, filled ones = real trades placed
    opt_orders = [o for o in orders
                  if 'option' in str(o.get('asset_class', '')).lower()
                  or (o.get('symbol', '') and len(o.get('symbol', '')) > 6
                      and any(ch.isdigit() for ch in o.get('symbol', '')))]
    filled = [o for o in opt_orders if str(o.get('status', '')).lower() == 'filled']
    buys = [o for o in filled if str(o.get('side', '')).lower() == 'buy']
    sells = [o for o in filled if str(o.get('side', '')).lower() == 'sell']

    open_pl = sum(float(p.get('unrealized_pl', 0) or 0) for p in positions)

    equities = [float(x) for x in (hist.get('equity') or []) if x]
    peak = max(equities) if equities else equity
    trough = min(equities) if equities else equity
    max_dd = ((peak - trough) / peak * 100) if peak else 0.0

    out = {
        'account_id': acct.get('account_number', ''),
        'as_of': _dt.datetime.now().isoformat(timespec='minutes'),
        'starting_equity': start,
        'current_equity': round(equity, 2),
        'total_pl': round(total_pl, 2),
        'total_pl_pct': round(total_pl_pct, 2),
        'day_pl': round(day_pl, 2),
        'open_option_positions': len(positions),
        'open_unrealized_pl': round(open_pl, 2),
        'option_orders_filled': len(filled),
        'buys_to_open': len(buys),
        'sells_to_close': len(sells),
        'peak_equity': round(peak, 2),
        'max_drawdown_pct': round(max_dd, 2),
    }

    sign = '+' if total_pl >= 0 else ''
    lines = [
        "─" * 52,
        "  RISK GATE — RESULTS FOR THE PRESENTATION",
        "─" * 52,
        f"  Account            {out['account_id']}",
        f"  As of              {out['as_of']}",
        f"  Starting equity    ${start:,.0f}",
        f"  Current equity     ${equity:,.2f}",
        f"  TOTAL P&L          {sign}${total_pl:,.2f}  ({sign}{total_pl_pct:.2f}%)",
        f"  Open positions     {len(positions)}  (unrealized {('+' if open_pl>=0 else '')}${open_pl:,.2f})",
        f"  Option trades made {len(filled)}   (buys {len(buys)} / closes {len(sells)})",
        f"  Peak equity        ${peak:,.2f}",
        f"  Max drawdown       {max_dd:.2f}%",
        "─" * 52,
        "  Paste into slide 9 / WRITEUP.md Results section.",
        "─" * 52,
    ]
    text = "\n".join(lines)
    print("\n" + text + "\n")

    with open('results.json', 'w') as f:
        json.dump(out, f, indent=2)
    with open('results.txt', 'w') as f:
        f.write(text + "\n")
    print("Saved results.json and results.txt")


if __name__ == '__main__':
    asyncio.run(main())
