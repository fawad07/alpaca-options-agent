"""
capital.py — withdrawal accounting for the cash-out tool.

ONE honest number governs everything:

    working_equity = actual_equity − cumulative_withdrawn

On a PAPER account the "withdrawn" cash physically stays (Alpaca exposes no transfer
tool), so we *account* for it as gone via a ledger. On a real account the same number
maps to a real wire. Sizing and P&L views call working_equity() so money you've taken
out is never re-traded.

Invisible at zero: with cumulative_withdrawn = 0, working_equity == actual_equity, so
importing/using this changes nothing until you actually record a withdrawal. Account A
is never withdrawn from, so A stays byte-identical to today.

State → cashout_state.json (per account).  Audit ledger → withdrawals.csv (A) /
withdrawals-<acct>.csv (others), append-only.

Design: docs/DESIGN_cashout.md
"""
from __future__ import annotations
import os, csv, json, datetime as dt
from zoneinfo import ZoneInfo
import config as C

_DIR = os.path.dirname(__file__)
STATE_PATH = os.path.join(_DIR, 'cashout_state.json')
_ET = ZoneInfo('America/New_York')


def _blank() -> dict:
    return {'withdrawn': 0.0, 'contributed': float(C.ACCOUNT_START)}


def load_state() -> dict:
    try:
        with open(STATE_PATH) as f:
            s = json.load(f)
            return s if isinstance(s, dict) else {}
    except Exception:
        return {}


def save_state(state: dict) -> None:
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write('\n')


def _acct(state: dict, name: str) -> dict:
    """Account entry with defaults filled in (never KeyErrors on a fresh/missing file)."""
    return {**_blank(), **(state.get(name) or {})}


def withdrawn(name: str) -> float:
    return float(_acct(load_state(), name)['withdrawn'])


def contributed(name: str) -> float:
    return float(_acct(load_state(), name)['contributed'])


def working_equity(name: str, actual_equity: float) -> float:
    """actual_equity minus everything withdrawn to date (floored at 0)."""
    return max(0.0, float(actual_equity) - withdrawn(name))


def true_return(name: str, actual_equity: float) -> float:
    """(equity + withdrawn − contributed) / contributed — the honest lifetime scorecard
    that stays correct once money moves in or out. Returns a fraction (×100 for %)."""
    st = _acct(load_state(), name)
    contrib = float(st['contributed']) or float(C.ACCOUNT_START)
    return (float(actual_equity) + float(st['withdrawn']) - contrib) / contrib


# ── ledger ───────────────────────────────────────────────────────────────────
LEDGER_FIELDS = ['timestamp_et', 'account', 'amount', 'sold', 'realized_gain',
                 'tax_rate', 'est_tax', 'after_tax', 'equity_before',
                 'cumulative_withdrawn', 'working_after', 'note']


def ledger_path(name: str) -> str:
    if name in ('A', 'default', ''):
        return os.path.join(_DIR, 'withdrawals.csv')
    safe = name.replace('/', '-')
    return os.path.join(_DIR, f'withdrawals-{safe}.csv')


def ledger(name: str) -> list:
    path = ledger_path(name)
    if not os.path.exists(path):
        return []
    try:
        return list(csv.DictReader(open(path)))
    except Exception:
        return []


def record_withdrawal(name: str, *, amount: float, sold: bool, realized_gain: float,
                      tax_rate: float, est_tax: float, after_tax: float,
                      equity_before: float, note: str = '') -> dict:
    """Append one ledger row and bump cumulative_withdrawn. Returns the new account state.
    The ONLY function that mutates state — called on an explicit, confirmed withdrawal."""
    state = load_state()
    acct = _acct(state, name)
    acct['withdrawn'] = round(float(acct['withdrawn']) + float(amount), 2)
    state[name] = acct
    save_state(state)
    ts = dt.datetime.now(_ET).strftime('%Y-%m-%d %H:%M ET')
    row = {'timestamp_et': ts, 'account': name, 'amount': round(float(amount), 2),
           'sold': 'yes' if sold else 'no', 'realized_gain': round(float(realized_gain), 2),
           'tax_rate': tax_rate, 'est_tax': round(float(est_tax), 2),
           'after_tax': round(float(after_tax), 2), 'equity_before': round(float(equity_before), 2),
           'cumulative_withdrawn': acct['withdrawn'],
           'working_after': round(float(equity_before) - acct['withdrawn'], 2), 'note': note}
    path = ledger_path(name)
    is_new = not os.path.exists(path)
    with open(path, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)
    return acct
