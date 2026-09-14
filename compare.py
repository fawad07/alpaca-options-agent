"""
compare.py — account A vs account B, side by side.

A = V1 (options only, cap 5, universe order).  B = combined (options + crypto, cap 6,
calibrated ranking). Both started at $100,000. Pulls each account live via MCP and shows
their track-record trend from the daily snapshots. Run any time:

    .venv/bin/python compare.py
"""
from __future__ import annotations
import os, csv, asyncio
import config as C
from accounts import ACCOUNT_A, ACCOUNT_B
from mcp_client import mcp_session, account, option_positions, crypto_positions


async def live(acct) -> dict:
    async with mcp_session(acct) as s:
        a = await account(s)
        opos = await option_positions(s)
        cpos = await crypto_positions(s)
    eq = float(a.get("equity", 0)); start = C.ACCOUNT_START
    return {"name": acct.name, "assets": "+".join(acct.asset_classes),
            "eq": eq, "cash": float(a.get("cash", 0)),
            "pl": eq - start, "pct": (eq - start) / start * 100 if start else 0,
            "opt": len(opos), "cry": len(cpos)}


def history(name: str, n: int = 6) -> list:
    fn = "stats_history.csv" if name in ("A", "default") else f"stats_history-{name}.csv"
    path = os.path.join(os.path.dirname(__file__), "research", fn)
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path)))[-n:]


async def main():
    A = await live(ACCOUNT_A)
    B = await live(ACCOUNT_B)
    W = 30
    print("\n" + "═" * 64)
    print(f"  RISK GATE — ACCOUNT A vs ACCOUNT B   (both started $100,000)")
    print("═" * 64)
    print(f"  {'':22}{'A (options V1)':>19}{'B (options+crypto)':>21}")
    def row(label, a, b):
        print(f"  {label:22}{a:>19}{b:>21}")
    row("equity",        f"${A['eq']:,.0f}",        f"${B['eq']:,.0f}")
    row("total P&L",     f"{A['pl']:+,.0f}",        f"{B['pl']:+,.0f}")
    row("total return",  f"{A['pct']:+.2f}%",       f"{B['pct']:+.2f}%")
    row("cash",          f"${A['cash']:,.0f}",      f"${B['cash']:,.0f}")
    row("open options",  f"{A['opt']}",             f"{B['opt']}")
    row("open crypto",   f"{A['cry']}",             f"{B['cry']}")
    print("═" * 64)
    lead = "B" if B["pct"] > A["pct"] else "A"
    print(f"  Ahead so far: account {lead}  ({abs(B['pct']-A['pct']):.2f}% apart)")
    print("═" * 64)

    for name in ("A", "B"):
        h = history(name)
        if h:
            print(f"\n  Account {name} — recent daily track record:")
            print(f"    {'date':12}{'equity':>12}{'return':>9}{'trades':>8}{'open':>6}")
            for r in h:
                print(f"    {r['date']:12}{'$'+format(float(r['equity']),',.0f'):>12}"
                      f"{r['total_pct']+'%':>9}{r['closed_trades']:>8}{r['open_positions']:>6}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
