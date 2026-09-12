"""
accounts.py — the Account model (v2, step 1).

Lets the agent target one or more Alpaca accounts by passing an Account around
instead of reading global keys. **Backward-compatible:** with nothing extra
configured, `default_account()` builds a single account from the existing
ALPACA_* env — identical to V1 behavior.

Later steps add per-account universe / asset-classes / mode here; step 1 keeps it
minimal (name + keys) so the refactor changes no behavior.
"""
from __future__ import annotations
from dataclasses import dataclass
import config as C


@dataclass(frozen=True)
class Account:
    name: str
    api_key: str
    secret_key: str


def default_account() -> Account:
    """The single account built from ALPACA_* env — today's behavior."""
    return Account(name="default", api_key=C.ALPACA_API_KEY, secret_key=C.ALPACA_SECRET_KEY)
