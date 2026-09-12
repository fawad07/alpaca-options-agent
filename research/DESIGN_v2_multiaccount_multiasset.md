# Design — Multi-account + Multi-asset (stocks/options + crypto spot)

**Status:** design only — nothing coded yet. Examine, decide the open questions, *then* build.
**Scope of THIS design:** (1) run on multiple Alpaca accounts, (2) trade crypto **spot**
alongside stock/ETF **options**. **Out of scope here:** the ensemble-ML and backtest-gate
work — that's a separate later phase. Keep this change focused.

> ⚠️ Alpaca has **no crypto options** — only crypto **spot** (buy/sell the coin). So the
> real mix is: stocks/ETFs → options (defined risk), crypto → spot (needs a stop-loss).

---

## 0. The biggest decision: WHERE to build it
V1 is **live right now** — it trades, writes the decision journal, and the daily-snapshot
job is building your track record. It's also your clean, submitted hackathon artifact.

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **In-place on `main`** | one repo | risks breaking the live agent + track record | ❌ avoid |
| **New `v2` branch (same repo)** | `main` keeps running untouched; merge when proven | cloud runs off `main`, so v2 runs only after merge (fine for dev) | ✅ **recommended** |
| **New repo (copy of V1)** | total isolation | duplicates infra; splits the track record | ok, heavier |

**Recommendation:** develop on a **`v2` branch**, test everything in `DRY_RUN` locally, keep
`main` (V1) running the track record, and merge to `main` only when the new agent is proven.
The refactor stays **additive & backward-compatible** — with one account and options only,
behavior is identical to today.

---

## 1. Current V1 pipeline (as-is)
```
cron_once (market-hours gate)
   └─ agent.run_once → run_live()               [SINGLE account, SINGLE asset: options]
        ├─ mcp_session()                         (keys from config.ALPACA_*)
        ├─ account(); option_positions()
        ├─ RiskManager(equity, day_start, open)
        ├─ manage exits (unrealized_plpc vs TP/SL)
        └─ for sym in UNIVERSE:
             data.fetch_daily → signals.signal → risk gates → find_atm_contract
             → option_premium → size_contracts → buy_option → journal
```

## 2. Target pipeline (to-be) — two new axes
```
runner (per-asset schedule gate)
   └─ for ACCOUNT in ACCOUNTS:                   [NEW outer loop]
        ├─ mcp_session(account)                  (that account's keys)
        ├─ RiskManager(account equity/positions) (isolated per account)
        └─ for ASSET_CLASS in account.assets:    [NEW inner axis]
             handler = OptionsHandler | CryptoSpotHandler
             ├─ handler.manage_exits(session, rm)
             └─ for sym in account.universe[asset_class]:
                  data.fetch_bars(sym, asset_class) → signals.signal (UNCHANGED)
                  → handler.scan_and_enter(session, sym, signal, rm) → journal(account, asset)
```

## 3. Piece-by-piece mapping (which file changes, and how)

| File | Today | Change needed | Type |
|---|---|---|---|
| **signals.py** | `signal(df)` on price bars | **none** — works on any bars incl. crypto | ✅ reuse as-is |
| **config.py** | single key pair, one `UNIVERSE`, flat risk params | add `ACCOUNTS` list (name, keys, mode, per-asset universe, asset_classes); add crypto params (stop %, TP %, max-notional, crypto universe). Single-account stays the default. | modify (additive) |
| **mcp_test.py** | `server_params()` reads global keys | `server_params(account)` — keys per account | modify |
| **mcp_client.py** | `mcp_session()`, option helpers | `mcp_session(account)`; generalize `positions(session, asset_class)`; add crypto helpers (`crypto_price`, `place_crypto_order`, `crypto_positions`, `close_crypto`) | modify + add |
| **data.py** | `fetch_daily(symbol)` (Yahoo) | add `fetch_bars(symbol, asset_class)` — stocks (Yahoo/Alpaca), crypto (`get_crypto_bars`) | add |
| **risk.py** | per-account gates + `size_contracts(premium)` | keep gates (per account); add `size_crypto(price, stop_pct)` + a max-notional cap; keep `contract_ok` for options | add |
| **agent.py** | `run_live()` single acct/asset | becomes the **orchestrator** (loops accounts × asset_classes, dispatches to handlers, aggregates per-account summary) | refactor |
| **NEW `instruments/options.py`** | (logic lives in agent) | `OptionsHandler` — move the current option flow here unchanged | new (extract) |
| **NEW `instruments/crypto.py`** | — | `CryptoSpotHandler` — crypto price, stop-based sizing, `place_crypto_order`, agent-managed exits | new |
| **cron_once.py** | one market-hours gate | gate **per asset**: options/stocks only when market open; crypto 24/7 | modify |
| **journal.py** | flat columns | add `account` + `asset_class` columns (back-compatible) | modify |
| **workflows** | `trade.yml` (market hours) | per-account secrets; a **separate 24/7 crypto workflow** (or one runner that self-selects) | modify + add |
| dashboard / results / refresh_stats | single account/options | later: group by account + asset_class | defer |

**Key insight:** signals + the MCP transport already generalize. The real *new* code is
one file — `instruments/crypto.py` — plus additive config/risk/orchestration. Everything
else is refactor-in-place, regression-tested against today's single-account/options behavior.

## 4. New abstraction — the InstrumentHandler interface
One tiny interface both asset classes implement, so `agent.py` doesn't care which it's driving:
```
class InstrumentHandler:
    asset_class: str
    def manage_exits(self, session, rm) -> dict          # close winners/losers
    def scan_and_enter(self, session, symbol, signal, rm) -> dict | None   # maybe open
```
- **OptionsHandler** = today's logic, moved verbatim (defined risk = premium; exit on unrealized_plpc vs ±50%).
- **CryptoSpotHandler** = new (spot, stop-based risk; exit on price vs entry±stop/target).

## 5. Three risk/design questions to EXAMINE before coding

### Q-A. Risk budget across asset classes (per account)
- **Option 1 — one global cap** (≤5 positions total across options+crypto, 2%/trade on total
  equity, 5% daily halt on total equity). Simple; matches today's gates. ← **recommended start**
- **Option 2 — per-asset sub-budgets** (e.g., ≤3 options + ≤2 crypto; separate halts). More
  control, more state. Add later if wanted.

### Q-B. Crypto risk model (spot is NOT defined-risk — a stop is mandatory)
- **Sizing:** `risk$ = equity × 2%`; with a crypto `stop_pct` (say 8%), `notional = risk$ / stop_pct`;
  `qty = notional / price`. Also cap notional (e.g., ≤ 15–20% of equity per coin) so one
  position can't dominate. ← decide the stop % and notional cap.
- **Stop mechanism:**
  - **Agent-managed stop** (check price each pass, close if ≤ entry×(1−stop)) — matches V1's
    exit style, simplest, works with 24/7 passes; **gap risk between passes**. ← **recommended start**
  - **Broker stop/bracket order** — tighter, but Alpaca crypto order types are limited; verify support.

### Q-C. Scheduling (crypto is 24/7, stocks/options are not)
- Options/stocks: keep the market-hours gate.
- Crypto: **separate 24/7 schedule** (GitHub cron every 15–30 min, all week) — cleanest as its
  **own workflow** (`trade-crypto.yml`), independent of the market-hours trader.

## 6. Config shape (illustrative — not final)
```
ACCOUNTS = [
  { name: "paper-main", key: env, secret: env, mode: LIVE_PAPER,
    assets: { options: [SPY,QQQ,AAPL,MSFT,NVDA,AMZN,TSLA],
              crypto:  [BTC/USD, ETH/USD] } },
  # add more accounts here; each isolated
]
CRYPTO_STOP_PCT = 0.08     # stop distance for spot
CRYPTO_TP_PCT   = 0.15     # take-profit for spot
CRYPTO_MAX_NOTIONAL_PCT = 0.15   # cap one coin's size vs equity
```
Back-compat: if `ACCOUNTS` is unset, build a single default account from today's
`ALPACA_*` + `UNIVERSE` (options only) → **identical to current behavior**.

## 7. Proposed build order (small steps, each DRY_RUN-testable)
1. **Account model** + `mcp_session(account)` / `server_params(account)` — one account = identical behavior (regression check).
2. **Extract `OptionsHandler`** from `agent.run_live` — pure refactor, no behavior change.
3. **Handler dispatch** in `agent.py` (still options-only) — verify unchanged output.
4. **`data.fetch_bars` crypto path** + **`CryptoSpotHandler`** in DRY_RUN (prints intended crypto trades only).
5. **Crypto sizing + stops** in `risk.py`.
6. **Crypto live exits/positions** via MCP.
7. **Multi-account loop**.
8. **Journal columns** (account, asset_class) + dashboard/results/refresh_stats updates.
9. **Cloud**: 24/7 `trade-crypto.yml` + per-account secrets.

Each step merges to `main` only after the DRY_RUN output looks right and the single-account/
options regression passes — so the live track record is never disrupted.

## 8. Open questions for you (decide before step 1)
1. **Where:** confirm the **`v2` branch** approach (recommended) vs new repo.
2. **Risk budget:** global cap (recommended) vs per-asset sub-budgets? (Q-A)
3. **Crypto stop %, take-profit %, and max-notional cap** — starting values? (Q-B)
4. **Crypto stop mechanism:** agent-managed (recommended) vs broker bracket? (Q-B)
5. **Crypto universe:** which coins to start (e.g., BTC/USD, ETH/USD)?
6. **Accounts:** how many, and are they all *your own* paper accounts? (managing others' real money is regulated)
