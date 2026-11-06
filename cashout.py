"""
cashout.py — the cash-out / withdraw engine (flexible partial withdrawals + tax rehearsal).

Three steps, all honest:
  • facts(acct)            → read-only: equity, FREE CASH (withdraw w/o selling), open
                             positions + their unrealized P&L, working equity, what's
                             been withdrawn so far, lifetime return.
  • preview(acct, amount)  → read-only: for an amount, what (if anything) must be SOLD,
                             the gain/loss that realizes, an ESTIMATED tax, the after-tax
                             proceeds, and what the account looks like after. No side effects.
  • execute(acct, amount)  → the only step that acts: hard paper-only guard, sell what's
                             needed, record the withdrawal in the ledger. Confirmed-only.

Principle (docs/DESIGN_cashout.md): it shows the facts and does the math — you decide.
No "safe/unsafe" verdict, no buy/sell advice, no tax advice. The tax number is a
REHEARSAL estimate at an assumption YOU set; $0 is actually charged on paper.

CLI:
  .venv/bin/python cashout.py facts   b
  .venv/bin/python cashout.py preview b 5000 [--rate 0.24]
  .venv/bin/python cashout.py execute b 5000 [--rate 0.24] --yes   (acts on paper!)
"""
from __future__ import annotations
import asyncio, argparse
import config as C
import capital
from accounts import ACCOUNTS, ACCOUNT_A, ACCOUNT_B   # noqa: F401 (ACCOUNTS used)
from mcp_client import (mcp_session, account as acct_info, option_positions,
                        crypto_positions, call, to_pair, _rows)


def _is_crypto(p: dict) -> bool:
    return ('crypto' in str(p.get('asset_class', '')).lower()
            or '/' in str(p.get('symbol', '')))


# ── FACTS (read-only) ─────────────────────────────────────────────────────────
async def facts(acct) -> dict:
    async with mcp_session(acct) as s:
        a = await acct_info(s)
        pos = await option_positions(s) + await crypto_positions(s)
    equity = float(a.get('equity', 0) or 0)
    free_cash = float(a.get('cash', 0) or 0)      # withdraw-able without selling anything
    positions = []
    for p in pos:
        mv = float(p.get('market_value', 0) or 0)
        upl = float(p.get('unrealized_pl', 0) or 0)
        positions.append({'symbol': str(p.get('symbol', '')),
                          'is_crypto': _is_crypto(p), 'market_value': mv,
                          'unrealized_pl': upl, 'qty': p.get('qty')})
    pos_value = sum(p['market_value'] for p in positions)
    unrealized = sum(p['unrealized_pl'] for p in positions)
    w = capital.withdrawn(acct.name)
    working = equity - w
    # "Profit vs contributed" measured on working equity; realized ≈ profit that isn't
    # still riding in open positions (an estimate — the exact figure is in the fill ledger).
    profit = working - capital.contributed(acct.name)
    realized_est = profit - unrealized
    return {
        'account': acct.name, 'equity': equity, 'free_cash': free_cash,
        'positions': positions, 'position_value': pos_value, 'unrealized': unrealized,
        'withdrawn': w, 'working_equity': working,
        'contributed': capital.contributed(acct.name),
        'profit': profit, 'realized_est': realized_est,
        'true_return_pct': capital.true_return(acct.name, equity) * 100,
    }


# ── SELL PLAN (which positions to sell to raise a shortfall) ────────────────────
def _plan_sells(positions: list, shortfall: float) -> tuple[list, float]:
    """Raise `shortfall` dollars by selling positions — crypto first (sellable 24/7),
    then largest market value first. Returns (plan, realized_gain). realized_gain for a
    partial sale is the proportional share of that position's unrealized P&L."""
    ordered = sorted(positions, key=lambda p: (0 if p['is_crypto'] else 1, -p['market_value']))
    need, plan, realized = float(shortfall), [], 0.0
    for p in ordered:
        if need <= 1e-9:
            break
        mv = p['market_value']
        if mv <= 0:
            continue
        take = min(mv, need)
        frac = take / mv
        g = p['unrealized_pl'] * frac
        plan.append({'symbol': p['symbol'], 'is_crypto': p['is_crypto'],
                     'sell_value': round(take, 2), 'pct_of_pos': round(frac * 100, 2),
                     'realized': round(g, 2)})
        realized += g
        need -= take
    return plan, realized


# ── PREVIEW (read-only) ─────────────────────────────────────────────────────────
async def preview(acct, amount: float, rate: float | None = None) -> dict:
    rate = C.CASHOUT_TAX_RATE_DEFAULT if rate is None else float(rate)
    f = await facts(acct)
    amount = float(amount)
    out = {'account': acct.name, 'amount': amount, 'tax_rate': rate,
           'free_cash': f['free_cash'], 'equity': f['equity'],
           'working_before': f['working_equity']}
    if amount <= 0:
        out['error'] = 'Enter an amount greater than $0.'
        return out
    if amount > f['equity'] + 1e-6:
        out['error'] = (f"${amount:,.2f} is more than the account holds "
                        f"(equity ${f['equity']:,.2f}).")
        return out

    if amount <= f['free_cash'] + 1e-6:
        # Covered by settled cash → a ledger entry only. Nothing is sold, so this action
        # creates NO new taxable event (those gains were realized when positions were
        # originally sold). Estimated tax on THIS action = $0.
        sold, plan, realized_gain = False, [], 0.0
    else:
        sold = True
        shortfall = amount - f['free_cash']
        plan, realized_gain = _plan_sells(f['positions'], shortfall)

    taxable = max(0.0, realized_gain)          # a realized LOSS is not taxed here
    est_tax = taxable * rate
    after_tax = amount - est_tax
    out.update({
        'sold': sold, 'sell_plan': plan,
        'shortfall': round(max(0.0, amount - f['free_cash']), 2),
        'realized_gain': round(realized_gain, 2),
        'taxable_gain': round(taxable, 2),
        'est_tax': round(est_tax, 2), 'after_tax': round(after_tax, 2),
        'working_after': round(f['working_equity'] - amount, 2),
        'free_cash_after': round(max(0.0, f['free_cash'] - amount), 2),
    })
    return out


# ── EXECUTE (the only acting step — confirmed, paper-only) ──────────────────────
def _assert_paper() -> None:
    """Hard guard: this project is wired paper-only (mcp_test.server_params forces
    ALPACA_PAPER_TRADE=true against the paper URL). Refuse the instant that isn't true."""
    url = str(getattr(C, 'ALPACA_PAPER_URL', ''))
    if 'paper' not in url.lower():
        raise RuntimeError(f'cash-out refused: not a paper endpoint ({url!r}).')


async def execute(acct, amount: float, rate: float | None = None) -> dict:
    """Perform the withdrawal on PAPER: sell what's needed, then record it in the ledger.
    Caller must have confirmed. Recomputes a fresh plan at the moment of execution."""
    _assert_paper()
    rate = C.CASHOUT_TAX_RATE_DEFAULT if rate is None else float(rate)
    p = await preview(acct, amount, rate)
    if p.get('error'):
        return p
    sold_done = []
    async with mcp_session(acct) as s:
        if p['sold'] and p['sell_plan']:
            try:
                await call(s, 'cancel_all_orders')          # clear resting stops first
            except Exception:
                pass
            for leg in p['sell_plan']:
                sym = to_pair(leg['symbol']) if leg['is_crypto'] else leg['symbol']
                pct = min(100.0, max(0.0, leg['pct_of_pos']))
                try:
                    await call(s, 'close_position',
                               {'symbol_or_asset_id': sym, 'percentage': pct})
                    sold_done.append(sym)
                except Exception as e:
                    p['exec_error'] = f'close {sym} failed: {str(e)[:120]}'
                    return p
        a = await acct_info(s)                              # post-sale equity
    equity_after = float(a.get('equity', p['equity']) or p['equity'])
    capital.record_withdrawal(
        acct.name, amount=amount, sold=p['sold'], realized_gain=p['realized_gain'],
        tax_rate=rate, est_tax=p['est_tax'], after_tax=p['after_tax'],
        equity_before=p['equity'],
        note=('sold ' + ', '.join(sold_done)) if sold_done else 'from free cash')
    p.update({'executed': True, 'equity_after': round(equity_after, 2),
              'cumulative_withdrawn': capital.withdrawn(acct.name)})
    return p


# ── CLI ─────────────────────────────────────────────────────────────────────────
def _money(x) -> str:
    return f"${float(x):,.2f}"


def _print_facts(f: dict) -> None:
    print(f"\n  Cash-out facts — Account {f['account']}")
    print(f"  {'equity':24}{_money(f['equity']):>16}")
    print(f"  {'free cash (no sale)':24}{_money(f['free_cash']):>16}")
    print(f"  {'open positions value':24}{_money(f['position_value']):>16}"
          f"   (unrealized {f['unrealized']:+,.2f})")
    print(f"  {'withdrawn so far':24}{_money(f['withdrawn']):>16}")
    print(f"  {'working equity':24}{_money(f['working_equity']):>16}")
    print(f"  {'profit vs contributed':24}{f['profit']:>+16,.2f}")
    print(f"  {'lifetime return':24}{f['true_return_pct']:>+15.2f}%")
    if f['positions']:
        print("  positions:")
        for p in f['positions']:
            print(f"     {p['symbol']:22} {_money(p['market_value']):>14}"
                  f"   unreal {p['unrealized_pl']:+,.2f}")


def _print_preview(p: dict) -> None:
    if p.get('error'):
        print(f"\n  ✖ {p['error']}")
        return
    print(f"\n  Preview — withdraw {_money(p['amount'])} from Account {p['account']}"
          f"   (assumed tax {p['tax_rate']*100:.0f}%)")
    if not p['sold']:
        print(f"  • Covered by free cash — nothing sold (ledger entry only).")
        print(f"  • New realized gain from this action: {_money(0)}  →  est. tax {_money(0)}.")
    else:
        print(f"  • Free cash {_money(p['free_cash'])} isn't enough — sell "
              f"{_money(p['shortfall'])} of positions:")
        for leg in p['sell_plan']:
            print(f"     sell {leg['pct_of_pos']:.1f}% of {leg['symbol']} "
                  f"(~{_money(leg['sell_value'])})  realizes {leg['realized']:+,.2f}")
        print(f"  • Realized gain/loss this action: {p['realized_gain']:+,.2f}")
        print(f"  • Taxable gain {_money(p['taxable_gain'])} × {p['tax_rate']*100:.0f}%"
              f"  →  est. tax {_money(p['est_tax'])}   (rehearsal estimate, not tax advice)")
    print(f"  • After-tax proceeds:  {_money(p['after_tax'])}")
    print(f"  • Working equity after: {_money(p['working_after'])}  "
          f"(free cash after ~{_money(p['free_cash_after'])})")


def main() -> None:
    ap = argparse.ArgumentParser(description='Cash-out rehearsal (paper).')
    ap.add_argument('cmd', choices=['facts', 'preview', 'execute'])
    ap.add_argument('acct', nargs='?', default='B')
    ap.add_argument('amount', nargs='?', type=float, default=0.0)
    ap.add_argument('--rate', type=float, default=None)
    ap.add_argument('--yes', action='store_true', help='required to actually execute')
    args = ap.parse_args()
    acct = ACCOUNTS.get(args.acct.upper())
    if not acct:
        raise SystemExit(f'unknown account {args.acct!r} (use A or B)')

    if args.cmd == 'facts':
        _print_facts(asyncio.run(facts(acct)))
    elif args.cmd == 'preview':
        _print_preview(asyncio.run(preview(acct, args.amount, args.rate)))
    elif args.cmd == 'execute':
        if not args.yes:
            print("Refusing to execute without --yes. Here's the preview instead:")
            _print_preview(asyncio.run(preview(acct, args.amount, args.rate)))
            return
        p = asyncio.run(execute(acct, args.amount, args.rate))
        _print_preview(p)
        if p.get('executed'):
            print(f"\n  ✔ recorded. cumulative withdrawn now "
                  f"{_money(p['cumulative_withdrawn'])}  (equity after {_money(p['equity_after'])})")
        elif p.get('exec_error'):
            print(f"\n  ✖ {p['exec_error']}")


if __name__ == '__main__':
    main()
