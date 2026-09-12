"""
backtest_fetch.py — pull & cache daily crypto bars for the backtester (WS1, step 1.1).
Fetches per-year to avoid per-request caps, dedupes, saves research/data/<SYM>.csv.
Run:  .venv/bin/python research/backtest_fetch.py
"""
from __future__ import annotations
import os, sys, csv, asyncio, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from mcp_client import mcp_session, call

COINS = ["BTC/USD", "ETH/USD", "SOL/USD", "LTC/USD"]
DATA = os.path.join(os.path.dirname(__file__), "data")
YEARS = range(2021, dt.date.today().year + 1)


async def fetch_coin(session, sym) -> list[dict]:
    rows: dict[str, dict] = {}
    for y in YEARS:
        res = await call(session, "get_crypto_bars", {
            "symbols": sym, "timeframe": "1Day",
            "start": f"{y}-01-01", "end": f"{y}-12-31",
            "limit": 10000, "sort": "asc"})
        bars = (res or {}).get("bars", {}).get(sym, []) if isinstance(res, dict) else []
        for b in bars:
            rows[b["t"][:10]] = {
                "date": b["t"][:10], "open": b["o"], "high": b["h"],
                "low": b["l"], "close": b["c"], "volume": b["v"]}
    return [rows[d] for d in sorted(rows)]


async def main():
    os.makedirs(DATA, exist_ok=True)
    async with mcp_session() as s:
        for sym in COINS:
            rows = await fetch_coin(s, sym)
            path = os.path.join(DATA, sym.replace("/", "-") + ".csv")
            with open(path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
                w.writeheader()
                w.writerows(rows)
            span = f"{rows[0]['date']} → {rows[-1]['date']}" if rows else "EMPTY"
            print(f"{sym:9} {len(rows):5} bars  {span}  -> {os.path.relpath(path)}")


if __name__ == "__main__":
    asyncio.run(main())
