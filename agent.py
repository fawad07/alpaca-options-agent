"""
agent.py — the autonomous options agent (Risk Gate).

Modes (set AGENT_MODE in .env):
  • DRY_RUN     — real data + signals + risk gates, prints the trades it WOULD make.
                  No account or MCP needed. Build/test freely.
  • LIVE_PAPER  — trades your Alpaca PAPER account THROUGH the MCP server:
                  picks an ATM option, applies every risk gate, places the order,
                  and manages exits (take-profit / stop). Paper money only.

Flow per run:
  manage open positions (TP/SL) → for each symbol: data → signal → option → GATES → buy

Run once:   .venv/bin/python agent.py
Loop:       .venv/bin/python agent.py --loop 900      (every 15 min, during market hours)
"""
from __future__ import annotations
import os, sys, json, time, asyncio, datetime as dt
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


def _dte(expiration_date: str) -> int:
    return (dt.date.fromisoformat(expiration_date) - dt.date.today()).days


# ── multi-asset orchestration (v2, step 7) ─────────────────────
def deployment_name() -> str:
    from accounts import current_account
    return current_account().name


def deployment_assets() -> str:
    from accounts import current_account
    return "+".join(current_account().asset_classes)


def market_open() -> bool:
    """US equity/options market hours (ET). Crypto ignores this — it trades 24/7."""
    from zoneinfo import ZoneInfo
    et = datetime.now(ZoneInfo('America/New_York'))
    return et.weekday() < 5 and (et.hour, et.minute) >= (9, 30) and et.hour < 16


def _handlers(account):
    """Asset handlers for THIS account, each with the account's own universe.
    Account A → options only; account B → options + crypto."""
    hs = []
    if 'option' in account.asset_classes:
        from instruments.options import OptionsHandler
        hs.append((OptionsHandler(), list(account.option_universe), 'option'))
    if 'crypto' in account.asset_classes:
        from instruments.crypto import CryptoSpotHandler
        hs.append((CryptoSpotHandler(), list(account.crypto_universe), 'crypto'))
    return hs


def _ranked_signals(handlers):
    """Gather actionable, handler-supported signals across ALL asset classes and rank
    by confidence (strongest first) — so options and crypto compete for the shared cap.
    Session-free (signals use daily bars). Returns (ranked, skipped)."""
    ranked, skipped = [], []
    for h, uni, ac in handlers:
        for sym in uni:
            df = D.fetch_bars(sym, ac)
            if df.empty:
                skipped.append((sym, ac, 'no data')); continue
            sig = S.signal(df); price = float(df['close'].iloc[-1])
            if sig['direction'] == 'neutral' or sig['confidence'] < C.MIN_CONFIDENCE:
                skipped.append((sym, ac, f"no signal ({sig['reason']})")); continue
            if not h.wants(sig):
                skipped.append((sym, ac, f"{sig['direction']} unsupported (long-only)")); continue
            ranked.append((sig['confidence'], h, ac, sym, sig, price))
    ranked.sort(key=lambda c: c[0], reverse=True)
    return ranked, skipped


# ─────────────────────────── DRY RUN ───────────────────────────
def run_dry():
    from accounts import current_account
    acct = current_account()
    print(f"\n=== Agent run @ {datetime.now():%Y-%m-%d %H:%M}  [DRY_RUN · account {acct.name}] ===")
    equity = C.ACCOUNT_START
    rm = RiskManager(equity=equity, day_start_equity=equity, open_positions=0,
                     max_concurrent=acct.max_concurrent)
    print(f"  Equity ${equity:,.0f} | cap {acct.max_concurrent} | assets {'+'.join(acct.asset_classes)}"
          f" | risk/trade ${rm.max_spend():,.0f}")
    ranked, skipped = _ranked_signals(_handlers(acct))
    print(f"  --- {len(ranked)} candidate signal(s), best-first, fill up to {acct.max_concurrent} ---")
    filled = 0
    for conf, h, ac, sym, sig, price in ranked:
        if filled >= acct.max_concurrent:
            print(f"  [no slot]  {sym:8} {ac:6} conf {conf:.2f}"); continue
        prev = h.dry_candidate(sym, sig, price, rm)
        if not prev.get('ok'):
            print(f"  [skip]     {sym:8} {ac:6} conf {conf:.2f} — {prev.get('note')}"); continue
        filled += 1
        print(f"  [FILL {filled}/{acct.max_concurrent}] {sym:8} {ac:6} conf {conf:.2f} — {prev['label']}")
    if skipped:
        print(f"  ({len(skipped)} not actionable: " +
              ", ".join(f"{s}" for s, _, _ in skipped[:14]) + ")")


# ────────────────────────── LIVE PAPER (via MCP) ───────────────
async def run_live(account=None) -> dict:
    from mcp_client import mcp_session, account as acct_info, _norm
    from accounts import current_account
    acct_cfg = account or current_account()
    handlers = _handlers(acct_cfg)
    print(f"\n=== Agent run @ {datetime.now():%Y-%m-%d %H:%M}  [LIVE_PAPER · account {acct_cfg.name}] ===")
    placed, exits_n = [], 0
    async with mcp_session(acct_cfg) as s:
        info = await acct_info(s)
        equity = float(info.get('equity', C.ACCOUNT_START))
        # starting open positions across all asset classes → one global count
        pos_by_h = [await h.get_positions(s) for h, _, _ in handlers]
        open0 = sum(len(p) for p in pos_by_h)
        rm = RiskManager(equity=equity, day_start_equity=equity, open_positions=open0,
                         max_concurrent=acct_cfg.max_concurrent)
        print(f"  Equity ${equity:,.0f} | open {open0}/{acct_cfg.max_concurrent} | "
              f"assets {'+'.join(acct_cfg.asset_classes)} | risk/trade ${rm.max_spend():,.0f}")

        mkt = market_open()
        held_syms = {_norm(p.get('symbol')) for pos in pos_by_h for p in pos}
        # 1) manage exits — options only during market hours; crypto anytime
        for (h, _, ac), pos in zip(handlers, pos_by_h):
            if ac == 'option' and not mkt:
                continue
            exits_n += await h.manage_exits(s, pos, rm)

        # 2) ranked entries — options gated to market hours; crypto 24/7;
        #    skip any symbol we already hold (one position per symbol — no pyramiding)
        ranked, _ = _ranked_signals(handlers)
        if not mkt:
            ranked = [c for c in ranked if c[2] != 'option']
        signals_n = len(ranked)
        for conf, h, ac, sym, sig, price in ranked:
            ok, _ = rm.can_open_new()
            if not ok:
                break
            if _norm(sym) in held_syms:
                continue
            label = await h.scan_and_enter(s, sym, sig, price, rm)
            if label:
                placed.append(label)
                held_syms.add(_norm(sym))

    # build the one-line journal summary of this pass
    parts = []
    if placed:
        parts.append("BOUGHT " + "; ".join(placed))
    if exits_n:
        parts.append(f"closed {exits_n} position(s)")
    if not placed:
        if signals_n == 0:
            parts.append("no signal — nothing actionable across options + crypto")
        else:
            parts.append(f"{signals_n} signal(s) ranked but none opened (cap full / risk gate / no contract)")
    return {'account': acct_cfg.name, 'assets': "+".join(acct_cfg.asset_classes),
            'equity': round(equity, 2), 'open_positions': rm.open_positions,
            'new_trades': len(placed), 'exits': exits_n, 'summary': "; ".join(parts)}


def run_once() -> dict:
    if C.MODE == 'LIVE_PAPER':
        return asyncio.run(run_live())
    run_dry()
    return {'account': deployment_name(), 'assets': deployment_assets(),
            'summary': 'dry run (no live account)'}


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
