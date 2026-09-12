"""
instruments/crypto.py — CryptoSpotHandler (v2, steps 4–6).

Crypto is LONG-ONLY spot. Alpaca crypto rejects plain 'stop' orders but accepts
'stop_limit', and has NO OCO/bracket — so each entry gets a broker-held STOP_LIMIT
(downside protection), while the TAKE-PROFIT is agent-managed (cancel the stop, then
market-close when the target is hit). Verified live on account B (2026-09-12).

`plan_entry` is pure/session-free (used by the DRY preview + LIVE entry).
"""
from __future__ import annotations
import asyncio
import config as C
from instruments.base import InstrumentHandler
from mcp_client import (crypto_positions, buy_crypto, crypto_stop,
                        open_crypto_orders, cancel_order, close_option, _norm, to_pair)


class CryptoSpotHandler(InstrumentHandler):
    asset_class = "crypto"

    def wants(self, sig) -> bool:
        return sig.get('direction') == 'bull'             # long-only spot: no shorting

    def dry_candidate(self, symbol, sig, price, rm) -> dict:
        plan = self.plan_entry(symbol, sig, price, rm)
        if not plan:
            return {'ok': False, 'note': 'no long entry / too small'}
        return {'ok': True,
                'label': (f"BULL BUY {plan['qty']:.4f} (~${plan['notional']:,.0f}) @ ${price:,.2f}"
                          f" · stop_limit ${plan['stop_price']:,.2f} / TP ${plan['tp_price']:,.2f}")}

    # ── pure planning (no session, capacity-agnostic) ─────────
    def plan_entry(self, symbol: str, sig: dict, price: float, rm) -> dict | None:
        if sig.get('direction') != 'bull':
            return None
        qty, notional, worst = rm.size_crypto(
            price, C.CRYPTO_STOP_PCT, C.CRYPTO_MAX_NOTIONAL_PCT)
        if qty <= 0 or notional < 1:
            return None
        stop_price = round(price * (1 - C.CRYPTO_STOP_PCT), 2)
        return {'symbol': symbol, 'qty': qty, 'notional': notional, 'price': price,
                'stop_price': stop_price,
                'stop_limit_price': round(stop_price * (1 - C.CRYPTO_STOP_LIMIT_BUFFER), 2),
                'tp_price': round(price * (1 + C.CRYPTO_TP_PCT), 2),
                'worst_loss': worst}

    # ── live ──────────────────────────────────────────────────
    async def get_positions(self, s) -> list:
        return await crypto_positions(s)

    async def manage_exits(self, s, positions, rm) -> int:
        """Broker stop_limit covers the downside. Here we (1) handle the AGENT-managed
        take-profit (cancel the resting stop, then close) plus a backup stop close, then
        (2) ENSURE every remaining position has a resting stop_limit (self-heals if an
        entry-time stop failed to place)."""
        exits_n = 0
        for p in positions:
            sym = p.get('symbol')
            try:
                plpc = float(p.get('unrealized_plpc', 0))
            except Exception:
                plpc = 0.0
            hit_tp = plpc >= C.CRYPTO_TP_PCT
            hit_stop = plpc <= -C.CRYPTO_STOP_PCT
            if hit_tp or hit_stop:
                why = 'take-profit' if hit_tp else 'stop (backup)'
                print(f"  EXIT {sym}: {plpc:+.0%} — {why}, cancelling resting stop + closing")
                for o in await open_crypto_orders(s, sym):
                    await cancel_order(s, o.get('id'))
                await close_option(s, sym)          # close_position handles crypto too
                rm.open_positions -= 1
                exits_n += 1

        # ensure protection on every still-open crypto position
        for p in await self.get_positions(s):
            sym = p.get('symbol')
            avail = float(p.get('qty_available') or 0)
            entry = float(p.get('avg_entry_price') or 0)
            if avail <= 0 or entry <= 0:
                continue
            has_stop = any(str(o.get('type')) == 'stop_limit' and str(o.get('side')) == 'sell'
                           for o in await open_crypto_orders(s, sym))
            if not has_stop:
                sp = round(entry * (1 - C.CRYPTO_STOP_PCT), 2)
                slp = round(sp * (1 - C.CRYPTO_STOP_LIMIT_BUFFER), 2)
                print(f"  PROTECT {sym}: no stop found — placing stop_limit ${sp}→${slp}")
                await crypto_stop(s, to_pair(sym), round(avail, 6), sp, slp)
        return exits_n

    async def scan_and_enter(self, s, symbol, sig, price, rm):
        plan = self.plan_entry(symbol, sig, price, rm)
        if not plan:
            print(f"  {symbol}: no crypto entry (long-only / too small)")
            return None
        print(f"  {symbol}: BULL — BUY {plan['qty']:.4f} (~${plan['notional']:,.0f}) @ ~${price:,.2f}"
              f"  stop_limit ${plan['stop_price']:,.2f}→${plan['stop_limit_price']:,.2f}"
              f"  · TP ${plan['tp_price']:,.2f} (agent-managed)")
        await buy_crypto(s, symbol, plan['qty'])
        # wait for the buy to fill AND its qty to become available, then stop that qty
        fqty = 0.0
        for _ in range(8):
            await asyncio.sleep(1.5)
            held = next((p for p in await crypto_positions(s)
                         if _norm(p.get('symbol')) == _norm(symbol)), None)
            if held:
                fqty = float(held.get('qty_available') or 0)
                if fqty > 0:
                    break
        if fqty > 0:
            await crypto_stop(s, symbol, round(fqty, 6),
                              plan['stop_price'], plan['stop_limit_price'])
        else:
            print(f"  {symbol}: ⚠️ qty not available yet — stop placed next run (ensure-protection)")
        rm.open_positions += 1
        return f"{plan['qty']:.4f} {symbol}"
