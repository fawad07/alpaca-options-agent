"""
instruments/crypto.py — CryptoSpotHandler (v2, steps 4–6).

Crypto is LONG-ONLY spot (no shorting), and NOT defined-risk, so every entry gets a
broker-held stop (Alpaca crypto stop order) plus a resting take-profit limit; the agent
cancels the sibling when one fills (no OCO on crypto).

`plan_entry` is pure/session-free — it computes the intended buy + stop + TP and is what
DRY_RUN prints for review. `scan_and_enter` (LIVE, step 6) uses it, then places the orders.
"""
from __future__ import annotations
import config as C
from instruments.base import InstrumentHandler
from mcp_client import (crypto_positions, buy_crypto, crypto_stop,
                        crypto_take_profit, close_option)


class CryptoSpotHandler(InstrumentHandler):
    asset_class = "crypto"

    # ── pure planning (no session) — used by DRY_RUN preview + LIVE entry ──
    def plan_entry(self, symbol: str, sig: dict, price: float, rm) -> dict | None:
        if sig.get('direction') != 'bull':
            return None                                   # long-only spot: no shorting
        ok, _ = rm.can_open_new()
        if not ok:
            return None                                   # global cap (shared with options)
        qty, notional, worst = rm.size_crypto(
            price, C.CRYPTO_STOP_PCT, C.CRYPTO_MAX_NOTIONAL_PCT)
        if qty <= 0 or notional < 1:
            return None
        return {'symbol': symbol, 'qty': qty, 'notional': notional, 'price': price,
                'stop_price': round(price * (1 - C.CRYPTO_STOP_PCT), 2),
                'tp_price': round(price * (1 + C.CRYPTO_TP_PCT), 2),
                'worst_loss': worst}

    # ── live (step 6) ─────────────────────────────────────────
    async def get_positions(self, s) -> list:
        return await crypto_positions(s)

    async def manage_exits(self, s, positions, rm) -> int:
        """Backup exit check (broker stop is primary). Close if price ran past
        stop/TP levels vs entry — protects if a broker order was missed."""
        exits_n = 0
        for p in positions:
            sym = p.get('symbol')
            try:
                plpc = float(p.get('unrealized_plpc', 0))
            except Exception:
                plpc = 0.0
            if plpc >= C.CRYPTO_TP_PCT:
                print(f"  EXIT {sym}: {plpc:+.0%} — take-profit (backup), closing")
                await close_option(s, sym); rm.open_positions -= 1; exits_n += 1
            elif plpc <= -C.CRYPTO_STOP_PCT:
                print(f"  EXIT {sym}: {plpc:+.0%} — stop (backup), closing")
                await close_option(s, sym); rm.open_positions -= 1; exits_n += 1
        return exits_n

    async def scan_and_enter(self, s, symbol, sig, price, rm):
        plan = self.plan_entry(symbol, sig, price, rm)
        if not plan:
            print(f"  {symbol}: no crypto entry (long-only / over cap / too small)")
            return None
        print(f"  {symbol}: BULL — BUY {plan['qty']:.4f} (~${plan['notional']:,.0f}) @ ~${price:,.2f}"
              f"  stop ${plan['stop_price']:,.2f} / TP ${plan['tp_price']:,.2f}")
        await buy_crypto(s, symbol, plan['qty'])
        await crypto_stop(s, symbol, plan['qty'], plan['stop_price'])          # broker stop
        await crypto_take_profit(s, symbol, plan['qty'], plan['tp_price'])     # resting TP
        rm.open_positions += 1
        return f"{plan['qty']:.4f} {symbol}"
