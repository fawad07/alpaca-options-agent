"""
instruments/options.py — OptionsHandler (v2, step 2).

The exact option logic extracted verbatim from agent.run_live (exits by premium
unrealized_plpc vs ±TP/SL; entries via ATM contract selection, premium, risk-sized
contracts, buy-to-open). Behavior is unchanged — this is a pure move.
"""
from __future__ import annotations
import datetime as dt
import config as C
from instruments.base import InstrumentHandler
from mcp_client import (option_positions, find_atm_contract, option_premium,
                        buy_option, close_option)


def _dte(expiration_date: str) -> int:
    return (dt.date.fromisoformat(expiration_date) - dt.date.today()).days


class OptionsHandler(InstrumentHandler):
    asset_class = "option"

    async def get_positions(self, s) -> list:
        return await option_positions(s)

    async def manage_exits(self, s, positions, rm) -> int:
        exits_n = 0
        for p in positions:
            sym = p.get('symbol')
            try:
                plpc = float(p.get('unrealized_plpc', 0))
            except Exception:
                plpc = 0.0
            if plpc >= C.TAKE_PROFIT_PCT:
                print(f"  EXIT {sym}: {plpc:+.0%} — take-profit, closing")
                await close_option(s, sym); rm.open_positions -= 1; exits_n += 1
            elif plpc <= -C.STOP_LOSS_PCT:
                print(f"  EXIT {sym}: {plpc:+.0%} — stop-loss, closing")
                await close_option(s, sym); rm.open_positions -= 1; exits_n += 1
        return exits_n

    async def scan_and_enter(self, s, symbol, sig, price, rm):
        ok, why = rm.can_open_new()
        if not ok:
            print(f"  {symbol}: BLOCKED — {why}"); return None
        right = 'call' if sig['direction'] == 'bull' else 'put'
        c = await find_atm_contract(s, symbol, right, price, C.MIN_DTE, C.MAX_DTE)
        if not c:
            print(f"  {symbol}: no suitable contract"); return None
        ok, why = rm.contract_ok(_dte(c['expiration_date']), is_long=True)
        if not ok:
            print(f"  {symbol}: contract rejected — {why}"); return None
        prem = await option_premium(s, c['symbol'])
        if not prem:
            print(f"  {symbol}: no premium quote"); return None
        qty = rm.size_contracts(prem)
        if qty < 1:
            print(f"  {symbol}: 1 lot (${prem*100:,.0f}) exceeds risk cap"); return None
        print(f"  {symbol}: {sig['direction'].upper()} — BUY {qty}x {c['symbol']} @ ~${prem:.2f}"
              f"  ({sig['reason']})")
        res = await buy_option(s, c['symbol'], qty)
        from agent import log            # lazy import avoids a circular import at load
        log({'symbol': symbol, 'contract': c['symbol'], 'qty': qty, 'premium': prem,
             'signal': sig, 'order_result': str(res)[:400], 'mode': 'LIVE_PAPER'})
        rm.open_positions += 1
        return f"{qty}x {symbol} {right}"
