"""
agent.py — the autonomous options agent.

Two modes (set AGENT_MODE in .env or config.py):
  • DRY_RUN     — runs with ZERO setup. Fetches real data, computes signals,
                  picks the option it *would* trade, runs every risk gate, and
                  prints/logs the decision. Places nothing. Build & test here.
  • LIVE_PAPER  — does the same, but places real orders on your Alpaca PAPER
                  account and manages exits. (Alpaca calls are marked  # TODO(alpaca)
                  and only import the SDK in this mode.)

The flow, per run:
  for each symbol:  data -> signal -> option intent -> RISK GATES -> (place)
Then: manage open positions (take-profit / stop / near-expiry).

Run once:   python3 agent.py
Loop:       python3 agent.py --loop 900      (every 900s = 15 min)
"""
from __future__ import annotations
import sys, json, time
from datetime import datetime
import config as C
import data as D
import signals as S
from risk import RiskManager


def log(event: dict):
    event['ts'] = datetime.now().isoformat(timespec='seconds')
    C.LOG_DIR.mkdir(exist_ok=True)
    with open(C.TRADE_LOG, 'a') as f:
        f.write(json.dumps(event) + '\n')


# ── account state ─────────────────────────────────────────────
def get_equity() -> float:
    if C.MODE == 'LIVE_PAPER':
        # TODO(alpaca): return float(trading_client.get_account().equity)
        raise NotImplementedError('wire Alpaca account in LIVE_PAPER mode')
    return C.ACCOUNT_START

def get_open_positions() -> list:
    if C.MODE == 'LIVE_PAPER':
        # TODO(alpaca): return trading_client.get_all_positions()  (options)
        raise NotImplementedError('wire Alpaca positions in LIVE_PAPER mode')
    return []


# ── option selection ──────────────────────────────────────────
def select_contract(symbol: str, direction: str, price: float) -> dict | None:
    """Pick the option contract to trade.
    LIVE_PAPER: query Alpaca's option chain for the nearest-ATM call/put with
    DTE in [MIN_DTE, MAX_DTE] and decent open interest/volume.  # TODO(alpaca)
    DRY_RUN: synthesize a realistic ATM contract with an ESTIMATED premium so the
    full pipeline (risk gates, sizing, logging) can run without an account."""
    right = 'call' if direction == 'bull' else 'put'
    dte = 30                                   # target ~1 month out
    strike = round(price)                      # near the money
    if C.MODE == 'LIVE_PAPER':
        # TODO(alpaca): use OptionChainRequest / get option contracts, filter by
        # right, DTE window, liquidity; read the live mid-price as the premium.
        raise NotImplementedError('wire Alpaca option chain in LIVE_PAPER mode')
    est_premium = round(price * 0.03, 2)       # DRY_RUN rough ATM ~30DTE estimate
    return {'symbol': symbol, 'right': right, 'strike': strike,
            'dte': dte, 'premium': est_premium, 'is_long': True}


def place_order(contract: dict, qty: int):
    if C.MODE == 'LIVE_PAPER':
        # TODO(alpaca): submit a buy-to-open MARKET/LIMIT order for `qty`
        # contracts of the chosen option symbol; store the order id.
        raise NotImplementedError('wire Alpaca order submission in LIVE_PAPER mode')
    print(f"    [DRY_RUN] would BUY {qty} {contract['symbol']} "
          f"{contract['strike']}{contract['right'][0].upper()} "
          f"~${contract['premium']}/ct  (~{contract['dte']}d)")


def manage_positions():
    """Exit rules: take-profit / stop-loss on premium, and close near expiry."""
    if C.MODE != 'LIVE_PAPER':
        return
    # TODO(alpaca): for each open option position, read current price; if P/L
    # >= +TAKE_PROFIT_PCT or <= -STOP_LOSS_PCT of entry premium, or DTE <= 1,
    # submit a closing order.
    raise NotImplementedError('wire Alpaca exit management in LIVE_PAPER mode')


# ── one pass of the agent ─────────────────────────────────────
def run_once():
    print(f"\n=== Agent run @ {datetime.now():%Y-%m-%d %H:%M}  [mode: {C.MODE}] ===")
    equity = get_equity()
    open_pos = get_open_positions()
    rm = RiskManager(equity=equity, day_start_equity=equity, open_positions=len(open_pos))
    print(f"  Equity ${equity:,.0f} | open positions {len(open_pos)} | "
          f"risk cap/trade ${rm.max_spend():,.0f}")

    manage_positions()

    for sym in C.UNIVERSE:
        df = D.fetch_daily(sym)
        if df.empty:
            print(f"  {sym}: no data"); continue
        sig = S.signal(df)
        price = float(df['close'].iloc[-1])

        if sig['direction'] == 'neutral' or sig['confidence'] < C.MIN_CONFIDENCE:
            print(f"  {sym}: no trade — {sig['reason']} (conf {sig['confidence']})")
            continue

        ok, why = rm.can_open_new()
        if not ok:
            print(f"  {sym}: BLOCKED — {why}"); continue

        contract = select_contract(sym, sig['direction'], price)
        ok, why = rm.contract_ok(contract['dte'], contract['is_long'])
        if not ok:
            print(f"  {sym}: contract rejected — {why}"); continue

        qty = rm.size_contracts(contract['premium'])
        if qty < 1:
            print(f"  {sym}: skipped — one contract (${contract['premium']*100:,.0f}) "
                  f"exceeds risk cap"); continue

        print(f"  {sym}: {sig['direction'].upper()} (conf {sig['confidence']}) — {sig['reason']}")
        place_order(contract, qty)
        log({'symbol': sym, 'signal': sig, 'contract': contract, 'qty': qty, 'mode': C.MODE})
        rm.open_positions += 1   # count it against capacity within this run


if __name__ == '__main__':
    loop_secs = None
    if '--loop' in sys.argv:
        try:
            loop_secs = int(sys.argv[sys.argv.index('--loop') + 1])
        except Exception:
            loop_secs = 900
    if loop_secs:
        print(f"Looping every {loop_secs}s — Ctrl-C to stop.")
        while True:
            run_once()
            time.sleep(loop_secs)
    else:
        run_once()
