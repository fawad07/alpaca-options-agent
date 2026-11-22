"""
risk.py — the risk gates. Every intended trade must pass ALL of these before
it can be placed. This is the part judges specifically ask for, and it's the
part that keeps a paper account from blowing up.

Design principle carried over from the whole project: protect the account first.
"""
from __future__ import annotations
import config as C


class RiskManager:
    def __init__(self, equity: float, day_start_equity: float, open_positions: int,
                 max_concurrent: int | None = None,
                 hard_notional_cap: float | None = None,
                 daily_spend_cap: float | None = None,
                 spent_today: float = 0.0):
        self.equity = equity
        self.day_start_equity = day_start_equity
        self.open_positions = open_positions
        self.max_concurrent = max_concurrent if max_concurrent is not None else C.MAX_CONCURRENT
        # Hard DOLLAR caps — used only by the live Account C (LIVE_C_MAX_*). None = no cap
        # (A and B behave exactly as before). hard_notional_cap clamps one buy; daily_spend_cap
        # halts new buys once spent_today + this buy would exceed it. spent_today is seeded from
        # today's real filled buys. See config.LIVE_C_MAX_* and docs/DESIGN_account_c_live.md.
        self.hard_notional_cap = hard_notional_cap
        self.daily_spend_cap = daily_spend_cap
        self.spent_today = float(spent_today)

    # ── portfolio-level gates ────────────────────────────────
    def daily_loss_ok(self) -> tuple[bool, str]:
        if self.day_start_equity <= 0:
            return True, ''
        dd = (self.equity - self.day_start_equity) / self.day_start_equity
        if dd <= -C.DAILY_LOSS_LIMIT_PCT:
            return False, f'daily loss limit hit ({dd:.1%}) — no new trades today'
        return True, ''

    def capacity_ok(self) -> tuple[bool, str]:
        if self.open_positions >= self.max_concurrent:
            return False, f'max {self.max_concurrent} concurrent positions reached'
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

    def size_crypto(self, price: float, stop_pct: float,
                    max_notional_pct: float) -> tuple[float, float, float]:
        """Crypto spot is NOT defined-risk, so risk = position notional × stop distance.
        notional = min( (2% of equity) / stop%,  max_notional% × equity );  qty = notional/price.
        Returns (qty, notional$, worst_case_loss$). The max-notional cap keeps one coin
        from dominating and usually holds actual risk at or below the 2% cap."""
        if price <= 0 or stop_pct <= 0:
            return 0.0, 0.0, 0.0
        notional = min(self.equity * C.MAX_RISK_PER_TRADE_PCT / stop_pct,
                       self.equity * max_notional_pct)
        # Live Account C only: never let one buy exceed the hard dollar ceiling.
        if self.hard_notional_cap is not None:
            notional = min(notional, self.hard_notional_cap)
        qty = notional / price
        return round(qty, 6), round(notional, 2), round(notional * stop_pct, 2)

    def spend_ok(self, notional: float) -> tuple[bool, str]:
        """Daily spend gate (live Account C only). Refuse a new buy once today's spend
        plus this buy would exceed daily_spend_cap. No cap set → always ok (A/B)."""
        if self.daily_spend_cap is None:
            return True, ''
        if self.spent_today + notional > self.daily_spend_cap + 1e-9:
            return (False, f'daily spend cap ${self.daily_spend_cap:,.0f} would be exceeded '
                           f'(${self.spent_today:,.0f} spent today + ${notional:,.0f} this buy)')
        return True, ''

    # ── one call that checks the portfolio gates ─────────────
    def can_open_new(self) -> tuple[bool, str]:
        for ok, why in (self.daily_loss_ok(), self.capacity_ok()):
            if not ok:
                return False, why
        return True, ''
