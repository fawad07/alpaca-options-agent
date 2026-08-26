"""
test_select.py — validate the MCP option-selection + pricing pipeline (read-only,
works after hours). For each universe symbol: signal -> pick ATM contract -> price it.
Run: .venv/bin/python test_select.py
"""
from __future__ import annotations
import asyncio
import config as C, data as D, signals as S
from mcp_client import mcp_session, find_atm_contract, option_premium


async def main():
    async with mcp_session() as s:
        print(f"{'Sym':6}{'Signal':8}{'Contract':<22}{'Premium':>9}{'1-lot cost':>12}")
        print("-" * 60)
        for sym in C.UNIVERSE:
            df = D.fetch_daily(sym)
            if df.empty:
                print(f"{sym:6} no data"); continue
            sig = S.signal(df)
            if sig['direction'] == 'neutral':
                print(f"{sym:6}{'neutral':8}(no trade)"); continue
            right = 'call' if sig['direction'] == 'bull' else 'put'
            price = float(df['close'].iloc[-1])
            c = await find_atm_contract(s, sym, right, price, C.MIN_DTE, C.MAX_DTE)
            if not c:
                print(f"{sym:6}{sig['direction']:8}no contract found"); continue
            prem = await option_premium(s, c['symbol'])
            cost = f"${prem*100:,.0f}" if prem else "n/a"
            prems = f"${prem:.2f}" if prem else "n/a"
            print(f"{sym:6}{sig['direction']:8}{c['symbol']:<22}{prems:>9}{cost:>12}")


if __name__ == '__main__':
    asyncio.run(main())
