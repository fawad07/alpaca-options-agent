"""
accounts.py — per-account config (v2, step 7b).

Each account is a full deployment profile: keys + which asset classes it trades +
its position cap + its universes. One codebase, two deployments:

  • Account A  = the V1 options-only agent (cap 5, 7-symbol universe, no crypto) —
                 keeps the pure options track record untouched.
  • Account B  = the experimental combined agent (cap 6, options + crypto).

Which one a run uses is set by the DEPLOY_ACCOUNT env (default 'A'). Account B's keys
come from ALPACA_B_* env (set once you create the 2nd paper account).
"""
from __future__ import annotations
import os
from dataclasses import dataclass
import config as C


@dataclass(frozen=True)
class Account:
    name: str
    api_key: str
    secret_key: str
    asset_classes: tuple = ('option',)
    max_concurrent: int = 5
    option_universe: tuple = ()
    crypto_universe: tuple = ()
    ordering: str = 'confidence'      # 'universe' = V1 list-order fill; 'confidence' = strongest-first


# Account A — pinned to V1 behavior (do not change): options only, cap 5, 7 symbols.
ACCOUNT_A = Account(
    name='A',
    api_key=C.ALPACA_API_KEY,
    secret_key=C.ALPACA_SECRET_KEY,
    asset_classes=('option',),
    max_concurrent=5,
    option_universe=('SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'TSLA'),
    crypto_universe=(),
    ordering='universe',              # keep A byte-identical to V1 (list-order fill)
)

# Account B — CRYPTO-ONLY (since 2026-11-27), cap 6, the 4 coins. Repurposed as the live-running
# PAPER MIRROR of the future live crypto Account C: same crypto-only strategy and 6 slots, so by
# the time C is funded there's a real track record of exactly what it does. Was options+crypto
# until 2026-11-27 (that ended the original A-vs-B options comparison — a deliberate choice).
# Legacy options held at the switch are auto-liquidated by the agent at the next market open.
# Keys fall back to the MAIN account if ALPACA_B_* isn't set.
ACCOUNT_B = Account(
    name='B',
    api_key=os.getenv('ALPACA_B_API_KEY', C.ALPACA_API_KEY),
    secret_key=os.getenv('ALPACA_B_SECRET_KEY', C.ALPACA_SECRET_KEY),
    asset_classes=('crypto',),
    max_concurrent=6,
    option_universe=(),
    crypto_universe=('BTC/USD', 'ETH/USD', 'SOL/USD', 'LTC/USD'),
    ordering='confidence',
)

ACCOUNTS = {'A': ACCOUNT_A, 'B': ACCOUNT_B}


def current_account() -> Account:
    """The account this deployment runs (DEPLOY_ACCOUNT env; default 'A')."""
    return ACCOUNTS.get(os.getenv('DEPLOY_ACCOUNT', 'A'), ACCOUNT_A)


def default_account() -> Account:
    """Backward-compat alias used by mcp_session/server_params."""
    return current_account()
