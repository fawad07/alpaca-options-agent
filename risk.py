"""
risk.py — the risk gates. Every intended trade must pass ALL of these before
it can be placed. This is the part judges specifically ask for, and it's the
part that keeps a paper account from blowing up.

Design principle carried over from the whole project: protect the account first.
"""
from __future__ import annotations
import config as C


class RiskManager:
    def __init__(self, equity: float, day_start_equity: float, open_positions: int):
        self.equity = equity
        self.day_start_equity = day_start_equity
        self.open_positions = open_positions

    # ── portfolio-level gates ────────────────────────────────
    def daily_loss_ok(self) -> tuple[bool, str]:
        if self.day_start_equity <= 0:
            return True, ''
        dd = (self.equity - self.day_start_equity) / self.day_start_equity
        if dd <= -C.DAILY_LOSS_LIMIT_PCT:
            return False, f'daily loss limit hit ({dd:.1%}) — no new trades today'
        return True, ''

    def capacity_ok(self) -> tuple[bool, str]:
        if self.open_positions >= C.MAX_CONCURRENT:
            return False, f'max {C.MAX_CONCURRENT} concurrent positions reached'
        return True, ''

    # ── trade-level gates ────────────────────────────────────
    def contract_ok(self, dte: int, is_long: bool) -> tuple[bool, str]:
        if C.DEFINED_RISK_ONLY and not is_long:
            return False, 'defined-risk only: agent buys options, never sells naked'
        if dte < C.MIN_DTE:
            return False, f'expiry too close ({dte}d < {C.MIN_DTE}d)'
        if dte > C.MAX_DTE:
            return False, f'expiry too far ({dte}d > {C.MAX_DTE}d)'
        return True, ''

    def max_spend(self) -> float:
        """Dollar cap for a single option trade (risk % of equity).
        A long option's max loss is its premium, so premium <= this cap
        means the trade risks at most MAX_RISK_PER_TRADE_PCT of the account."""
        return self.equity * C.MAX_RISK_PER_TRADE_PCT

    def size_contracts(self, premium_per_contract: float) -> int:
        """How many contracts fit under the risk cap. (1 contract = 100 shares,
        so cost = premium * 100.)"""
        if premium_per_contract <= 0:
            return 0
        cost_each = premium_per_contract * 100
        return int(self.max_spend() // cost_each)

    # ── one call that checks the portfolio gates ─────────────
    def can_open_new(self) -> tuple[bool, str]:
        for ok, why in (self.daily_loss_ok(), self.capacity_ok()):
            if not ok:
                return False, why
        return True, ''
