"""
agent.py — the autonomous options agent (Risk Gate).

Modes (set AGENT_MODE in .env):
  • DRY_RUN     — real data + signals + risk gates, prints the trades it WOULD make.
                  No account or MCP needed. Build/test freely.
  • LIVE_PAPER  — trades your Alpaca PAPER account THROUGH the MCP server:
                  picks an ATM option, applies every risk gate, places the order,
                  and manages exits (take-profit / stop). Paper money only.

Flow per run:
  manage open positions (TP/SL) → for each symbol: data → signal → option → GATES → buy

Run once:   .venv/bin/python agent.py
Loop:       .venv/bin/python agent.py --loop 900      (every 15 min, during market hours)
"""
from __future__ import annotations
import sys, json, time, asyncio, datetime as dt
from datetime import datetime
import config as C
import data as D
import signals as S
from risk import RiskManager


def log(event: dict):
    event['ts'] = datetime.now().isoformat(timespec='seconds')
    C.LOG_DIR.mkdir(exist_ok=True)
    with open(C.TRADE_LOG, 'a') as f:
        f.write(json.dumps(event) + '\n')


def _dte(expiration_date: str) -> int:
    return (dt.date.fromisoformat(expiration_date) - dt.date.today()).days


# ─────────────────────────── DRY RUN ───────────────────────────
def run_dry():
    print(f"\n=== Agent run @ {datetime.now():%Y-%m-%d %H:%M}  [DRY_RUN] ===")
    equity = C.ACCOUNT_START
    rm = RiskManager(equity=equity, day_start_equity=equity, open_positions=0)
    print(f"  Equity ${equity:,.0f} | risk cap/trade ${rm.max_spend():,.0f}")
    for sym in C.UNIVERSE:
        df = D.fetch_daily(sym)
        if df.empty:
            print(f"  {sym}: no data"); continue
        sig = S.signal(df); price = float(df['close'].iloc[-1])
        if sig['direction'] == 'neutral' or sig['confidence'] < C.MIN_CONFIDENCE:
            print(f"  {sym}: no trade — {sig['reason']} (conf {sig['confidence']})"); continue
        est = round(price * 0.03, 2)          # rough ATM ~30DTE premium estimate
        qty = rm.size_contracts(est)
        right = 'C' if sig['direction'] == 'bull' else 'P'
        if qty < 1:
            print(f"  {sym}: 1 lot (~${est*100:,.0f}) exceeds risk cap"); continue
        print(f"  {sym}: {sig['direction'].upper()} — would BUY {qty}x ~{round(price)}{right} "
              f"(~${est}/ct) — {sig['reason']}")
        rm.open_positions += 1


# ────────────────────────── LIVE PAPER (via MCP) ───────────────
async def run_live(account=None) -> dict:
    from mcp_client import mcp_session, account as acct_info
    from instruments.options import OptionsHandler
    handler = OptionsHandler()
    print(f"\n=== Agent run @ {datetime.now():%Y-%m-%d %H:%M}  [LIVE_PAPER via MCP] ===")
    placed, blocked, signals_n, exits_n = [], [], 0, 0
    async with mcp_session(account) as s:
        acct = await acct_info(s)
        equity = float(acct.get('equity', C.ACCOUNT_START))
        positions = await handler.get_positions(s)
        rm = RiskManager(equity=equity, day_start_equity=equity, open_positions=len(positions))
        print(f"  Equity ${equity:,.0f} | open option positions {len(positions)} | "
              f"risk cap/trade ${rm.max_spend():,.0f}")

        # 1) manage exits — take-profit / stop (handler-specific)
        exits_n = await handler.manage_exits(s, positions, rm)

        # 2) scan for new entries (generic signal → handler places the trade)
        for symu in C.UNIVERSE:
            df = D.fetch_daily(symu)
            if df.empty:
                print(f"  {symu}: no data"); continue
            sig = S.signal(df); price = float(df['close'].iloc[-1])
            if sig['direction'] == 'neutral' or sig['confidence'] < C.MIN_CONFIDENCE:
                print(f"  {symu}: no trade — {sig['reason']}"); continue
            signals_n += 1                      # an actionable signal fired
            label = await handler.scan_and_enter(s, symu, sig, price, rm)
            if label:
                placed.append(label)
            else:
                blocked.append(symu)

    # build the one-line journal summary of this pass
    parts = []
    if placed:
        parts.append("BOUGHT " + "; ".join(placed))
    if exits_n:
        parts.append(f"closed {exits_n} position(s)")
    if not placed:
        if signals_n == 0:
            parts.append(f"no signal — all {len(C.UNIVERSE)} symbols neutral/low-confidence")
        else:
            parts.append(f"{signals_n} signal(s) fired but none opened "
                         f"(risk gate / no contract / over cap): {', '.join(blocked)}")
    return {'equity': round(equity, 2), 'open_positions': rm.open_positions,
            'new_trades': len(placed), 'exits': exits_n, 'summary': "; ".join(parts)}


def run_once() -> dict:
    if C.MODE == 'LIVE_PAPER':
        return asyncio.run(run_live())
    run_dry()
    return {'summary': 'dry run (no live account)'}


if __name__ == '__main__':
    loop_secs = None
    if '--loop' in sys.argv:
        try:
            loop_secs = int(sys.argv[sys.argv.index('--loop') + 1])
        except Exception:
            loop_secs = 900
    if loop_secs:
        print(f"Looping every {loop_secs}s — Ctrl-C to stop.")
        while True:
            run_once()
            time.sleep(loop_secs)
    else:
        run_once()
