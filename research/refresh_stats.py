"""
refresh_stats.py — regenerate the research paper's real numbers in one command.

Pulls the live account (via MCP) + the decision journal, computes every figure the
paper cites (trade ledger, realized P&L, win rate, profit factor, gate blocks,
equity waypoints), writes a refreshable snapshot, and appends one row to a growing
time-series so we can watch the track record lengthen.

Run:  .venv/bin/python research/refresh_stats.py
Outputs:
  research/stats_snapshot.md   (overwritten each run — paste-ready for the paper)
  research/stats_history.csv   (appended each run — the growing track record)
"""
from __future__ import annotations
import os, re, csv, sys, asyncio, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # import project root
import config as C
from mcp_client import mcp_session, call, account, option_positions, _rows

HERE = os.path.dirname(__file__)
JOURNAL = os.path.join(os.path.dirname(HERE), "activity.csv")
SNAP = os.path.join(HERE, "stats_snapshot.md")
HIST = os.path.join(HERE, "stats_history.csv")


def journal_stats() -> dict:
    rows = list(csv.DictReader(open(JOURNAL)))
    open_rows = [r for r in rows if r["market"] == "open"]
    eqs = [float(r["equity"]) for r in open_rows if r["equity"]]
    sig_blocks = 0
    block_runs = 0
    for r in rows:
        if "none opened" in r["summary"]:
            block_runs += 1
            m = re.search(r"(\d+) signal", r["summary"])
            if m:
                sig_blocks += int(m.group(1))
    return {
        "rows": len(rows), "open_runs": len(open_rows),
        "trades": sum(int(r["new_trades"] or 0) for r in rows),
        "exits": sum(int(r["exits"] or 0) for r in rows),
        "block_runs": block_runs, "sig_blocks": sig_blocks,
        "eq_first": eqs[0] if eqs else 0, "eq_peak": max(eqs) if eqs else 0,
        "eq_trough": min(eqs) if eqs else 0, "eq_last": eqs[-1] if eqs else 0,
        "first_ts": open_rows[0]["timestamp_et"] if open_rows else "",
        "last_ts": open_rows[-1]["timestamp_et"] if open_rows else "",
    }


async def account_stats() -> dict:
    async with mcp_session() as s:
        a = await account(s)
        pos = await option_positions(s)
        orders = _rows(await call(s, "get_orders", {"status": "all", "limit": 500}))
    fills = [o for o in orders if str(o.get("status")) == "filled"]
    fills.sort(key=lambda o: o.get("filled_at") or "")
    book: dict[str, list] = {}
    ledger = []
    for o in fills:
        sym = o["symbol"]; side = o["side"]
        q = int(float(o["filled_qty"])); px = float(o["filled_avg_price"])
        t = (o.get("filled_at") or "")[:16].replace("T", " ")
        ledger.append((t, side, q, sym, px))
        book.setdefault(sym, []).append((side, q, px))
    roundtrips = []
    for sym, legs in book.items():
        buys = [(q, px) for sd, q, px in legs if sd == "buy"]
        sells = [(q, px) for sd, q, px in legs if sd == "sell"]
        if buys and sells:
            bpx = buys[0][1]; spx, q = sells[0][1], sells[0][0]
            pl = (spx - bpx) * 100 * q
            roundtrips.append({"sym": sym, "buy": bpx, "sell": spx,
                               "pct": (spx - bpx) / bpx * 100, "pl": pl})
    wins = [r for r in roundtrips if r["pl"] > 0]
    losses = [r for r in roundtrips if r["pl"] <= 0]
    gross_win = sum(r["pl"] for r in wins)
    gross_loss = -sum(r["pl"] for r in losses)
    eq = float(a.get("equity", 0)); cash = float(a.get("cash", 0))
    realized = sum(r["pl"] for r in roundtrips)
    return {
        "equity": eq, "cash": cash, "open_positions": len(pos),
        "total_pl": eq - C.ACCOUNT_START, "total_pct": (eq - C.ACCOUNT_START) / C.ACCOUNT_START * 100,
        "realized": realized, "unrealized": (eq - C.ACCOUNT_START) - realized,
        "ledger": ledger, "roundtrips": roundtrips,
        "closed": len(roundtrips), "wins": len(wins), "losses": len(losses),
        "win_rate": (len(wins) / len(roundtrips) * 100) if roundtrips else 0,
        "profit_factor": (gross_win / gross_loss) if gross_loss else float("inf"),
        "gross_win": gross_win, "gross_loss": gross_loss,
    }


def write_snapshot(j: dict, a: dict) -> None:
    L = []
    L.append(f"# Stats snapshot — {dt.datetime.now():%Y-%m-%d %H:%M}")
    L.append("")
    L.append(f"- **Equity:** ${a['equity']:,.2f}  ·  **Total P&L:** {a['total_pl']:+,.2f} ({a['total_pct']:+.2f}%)")
    L.append(f"- **Realized:** ${a['realized']:+,.2f}  ·  **Unrealized:** ${a['unrealized']:+,.2f}  ·  **Cash:** ${a['cash']:,.2f}")
    L.append(f"- **Open positions:** {a['open_positions']}")
    L.append(f"- **Closed round-trips:** {a['closed']}  (W {a['wins']} / L {a['losses']}, "
             f"win rate {a['win_rate']:.0f}%, profit factor "
             f"{a['profit_factor']:.2f})" if a['profit_factor'] != float('inf') else
             f"- **Closed round-trips:** {a['closed']}  (all winners)")
    L.append(f"- **Journal:** {j['rows']} rows · {j['open_runs']} market-hours cycles · "
             f"{j['trades']} entries · {j['exits']} exits · {j['sig_blocks']} signal-level gate blocks")
    L.append(f"- **Equity path:** first ${j['eq_first']:,.0f} · peak ${j['eq_peak']:,.0f} · "
             f"trough ${j['eq_trough']:,.0f} · last ${j['eq_last']:,.0f}")
    L.append(f"- **Window:** {j['first_ts']} → {j['last_ts']} ET")
    L.append("")
    L.append("## Closed round-trips")
    L.append("| Contract | Buy | Sell | Return | P&L |")
    L.append("|---|---|---|---|---|")
    for r in a["roundtrips"]:
        L.append(f"| {r['sym']} | ${r['buy']:.2f} | ${r['sell']:.2f} | {r['pct']:+.1f}% | ${r['pl']:+,.0f} |")
    L.append("")
    L.append("## Full fill ledger")
    L.append("```")
    for t, side, q, sym, px in a["ledger"]:
        L.append(f"{t}  {side.upper():4} {q}x {sym} @ ${px:.2f}")
    L.append("```")
    open(SNAP, "w").write("\n".join(L) + "\n")


def append_history(j: dict, a: dict) -> None:
    fields = ["date", "equity", "total_pct", "realized", "closed_trades",
              "wins", "losses", "open_positions", "cycles", "gate_blocks"]
    today = dt.date.today().isoformat()
    # keep exactly one row per date — a re-run today overwrites today's row
    prior = [r for r in csv.DictReader(open(HIST))] if os.path.exists(HIST) else []
    prior = [r for r in prior if r.get("date") != today]
    row = {
        "date": today, "equity": round(a["equity"], 2),
        "total_pct": round(a["total_pct"], 2), "realized": round(a["realized"], 2),
        "closed_trades": a["closed"], "wins": a["wins"], "losses": a["losses"],
        "open_positions": a["open_positions"], "cycles": j["open_runs"],
        "gate_blocks": j["sig_blocks"],
    }
    with open(HIST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in prior:
            w.writerow(r)
        w.writerow(row)


def main():
    j = journal_stats()
    a = asyncio.run(account_stats())
    write_snapshot(j, a)
    append_history(j, a)
    print(f"Equity ${a['equity']:,.2f} ({a['total_pct']:+.2f}%) · "
          f"{a['closed']} closed ({a['wins']}W/{a['losses']}L) · "
          f"realized ${a['realized']:+,.0f} · {j['sig_blocks']} gate blocks")
    print(f"Wrote {os.path.relpath(SNAP)} and appended {os.path.relpath(HIST)}")


if __name__ == "__main__":
    main()
