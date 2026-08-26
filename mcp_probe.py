"""mcp_probe.py — learn the option-contract + snapshot data shapes for SPY."""
from __future__ import annotations
import asyncio, json, datetime as dt
from mcp_client import mcp_session, call
import data as D


async def main():
    today = dt.date.today()
    lo = (today + dt.timedelta(days=14)).isoformat()
    hi = (today + dt.timedelta(days=60)).isoformat()
    px = float(D.fetch_daily('SPY', rng='1mo')['close'].iloc[-1])
    print(f"SPY ~{px:.2f} | expiry window {lo} .. {hi}")

    async with mcp_session() as s:
        contracts = await call(s, 'get_option_contracts', {
            'underlying_symbols': 'SPY', 'type': 'call', 'status': 'active',
            'expiration_date_gte': lo, 'expiration_date_lte': hi,
            'strike_price_gte': round(px * 0.98), 'strike_price_lte': round(px * 1.02),
            'limit': 5,
        })
        print("\n=== get_option_contracts (top-level keys) ===")
        print(type(contracts), list(contracts.keys()) if isinstance(contracts, dict) else 'list')
        print(json.dumps(contracts, indent=2)[:1500])

        # pull one contract symbol to snapshot
        sym = None
        lst = contracts.get('option_contracts') if isinstance(contracts, dict) else contracts
        if isinstance(lst, list) and lst:
            sym = lst[0].get('symbol')
        print(f"\nfirst contract symbol: {sym}")
        if sym:
            snap = await call(s, 'get_option_snapshot', {'symbols': sym})
            print("\n=== get_option_snapshot ===")
            print(json.dumps(snap, indent=2)[:1500])


if __name__ == '__main__':
    asyncio.run(main())
