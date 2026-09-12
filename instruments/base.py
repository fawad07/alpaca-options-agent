"""
instruments/base.py — the InstrumentHandler interface (v2, step 3).

Both asset classes implement this small contract so agent.py can drive options or
crypto without caring which. Per-run flow the agent uses:
    positions = handler.get_positions(session)
    exits     = handler.manage_exits(session, positions, rm)
    for each symbol with an actionable signal:
        label = handler.scan_and_enter(session, symbol, signal, price, rm)  # str if opened, else None
"""
from __future__ import annotations


class InstrumentHandler:
    asset_class: str = "base"

    def wants(self, sig) -> bool:
        """Is this signal tradable by this asset class? (Options: bull/bear; crypto: bull only.)"""
        return sig.get('direction') in ('bull', 'bear')

    def dry_candidate(self, symbol, sig, price, rm) -> dict:
        """Session-free viability + label for DRY_RUN. Returns {'ok': bool, 'label'/'note': str}."""
        raise NotImplementedError

    async def get_positions(self, session) -> list:
        raise NotImplementedError

    async def manage_exits(self, session, positions, rm) -> int:
        """Close winners/losers; return how many were closed."""
        raise NotImplementedError

    async def scan_and_enter(self, session, symbol, sig, price, rm):
        """Maybe open a position. Return a short label (e.g. '2x SPY call') if opened,
        else None (having printed the block reason)."""
        raise NotImplementedError
