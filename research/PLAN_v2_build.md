# v2 Build Plan — Multi-account + Crypto-spot (with broker stops)

**Status:** approved design; sequenced plan below. Build happens on a **`v2` branch**,
DRY_RUN-first, backward-compatible. `main` (V1) keeps running the live track record
untouched until we merge. Companion docs: `DESIGN_v2_multiaccount_multiasset.md`,
`ROADMAP_V2.md`.

## Locked decisions
- **Where:** `v2` branch off `main`; merge back when proven.
- **Accounts:** 2 personal paper accounts, isolated risk each.
- **Assets:** stock/ETF **options** (as today) + crypto **spot** (BTC/USD, ETH/USD, ETC/USD).
- **Crypto stop mechanism:** **B — broker/bracket stop orders** (Alpaca holds the stop; no blind window). Agent A-style checks remain only as a backup monitor.
- **Crypto percentages:** set from a **backtested robust range** (walk-forward, out-of-sample), not guessed.
- **Risk budget:** one **global cap per account** (5 open total, 2%/trade, 5% daily halt). Account-level 2%/5% unchanged.

## Key dependency to verify FIRST
Decision **B depends on Alpaca supporting stop/bracket orders for _crypto_** (confirmed for stocks; crypto order types are more limited). Also confirm **ETC/USD** is listed. → **Step 0** below. If crypto stops are NOT supported, we pause and choose: interim A (with a tighter/ more-frequent loop) or defer crypto until B is possible.

---

## The plan — 4 workstreams, sequenced

### Step 0 — Feasibility spikes (read-only, ~quick) 🔎
De-risk before any building.
- Verify **ETC/USD** is tradable + has data on Alpaca.
- Verify **crypto stop/bracket order support** via MCP `place_crypto_order` (order types accepted).
- Document findings. **If B unsupported → surface to you and decide.**
- **Deliverable:** a short feasibility note; go/no-go on B.

### Workstream 1 — Honest crypto backtester (offline; finds the numbers) 📊
Runs entirely offline on historical data; touches nothing live.
1. Pull historical bars for BTC/ETH/ETC (Alpaca `get_crypto_bars` and/or Yahoo).
2. Simulate the crypto-spot strategy: EMA/RSI entry → stop / take-profit / size exits, with fees + slippage modeled.
3. **Grid-sweep** stop% × TP% × size% across sensible ranges.
4. **Walk-forward, out-of-sample** validation (tune on older window, test on newer; roll forward).
5. Report a **robust plateau** (a range that works across periods), not a single spike.
- **Deliverable:** recommended robust ranges for stop%, TP%, size% — the inputs for the live crypto config.

### Workstream 2 — Core refactor on `v2` (additive, regression-tested) 🏗️
Each step is small, DRY_RUN-testable, and must leave single-account/options behavior identical.
1. **Account model** + `server_params(account)` / `mcp_session(account)`. One account = same behavior (regression check).
2. **Extract `OptionsHandler`** from `agent.run_live` — pure move, no behavior change.
3. **`InstrumentHandler` interface** + dispatch in `agent.py` (still options-only) — verify unchanged output.
4. **`data.fetch_bars(symbol, asset_class)`** crypto path + **`CryptoSpotHandler`** (DRY_RUN: prints intended crypto trades only).
5. **Crypto sizing in `risk.py`** (using backtested ranges) + **broker stop/bracket order** placement (decision B).
6. **Crypto live exits / position management** (broker stop is primary; agent monitors as backup).
7. **Multi-account loop** (both paper accounts, isolated risk).
8. **Journal + reporting**: add `account` + `asset_class` columns; update `dashboard.py`, `results.py`, `refresh_stats.py`.
9. **Cloud**: add a **24/7 `trade-crypto.yml`** workflow + per-account secrets; keep the market-hours options workflow.

### Workstream 3 — Validate & merge ✅
- Paper-run v2 (DRY_RUN then LIVE_PAPER on the 2 accounts) and confirm behavior.
- **Regression:** single-account/options output matches V1.
- Confirm broker stops actually fire on crypto in paper.
- **Merge `v2` → `main`**; cloud picks up the upgraded agent; track record continues.

---

## Sequencing (what depends on what)
```
Step 0 (feasibility)  ──►  gates Workstream 2 step 5 (broker stops) and crypto at all
Workstream 1 (backtest) ──►  feeds Workstream 2 step 5 (the crypto numbers)   [can run in parallel with WS2 steps 1–4]
Workstream 2 steps 1–4  ──►  refactor scaffolding (safe anytime)
Workstream 2 steps 5–9  ──►  need Step 0 (go) + WS1 (numbers)
Workstream 3            ──►  after all of WS2
```
So the **immediate next actions** are **Step 0** (verify B + ETC) and **Workstream 1** (backtester) — both are safe/offline and unblock everything else. The v2-branch refactor (WS2 steps 1–4) can proceed in parallel since it's behavior-preserving.

## Guardrails (every step)
- **DRY_RUN first**, always.
- **`main`/V1 stays live and untouched** until the final merge.
- Each step **small, testable, reversible**; keep single-account/options as the default so nothing regresses.
- **No real money** anywhere in v2 — paper only. (Real money is a separate, later, heavily-gated phase.)
- Honesty rule holds: backtest numbers must survive **out-of-sample**, or they don't ship.

## Definition of done (v2 milestone)
Two paper accounts, each trading stock-options + crypto-spot, with broker stops on crypto,
global per-account risk gates, one decision journal spanning accounts+assets, running
autonomously in the cloud (options market-hours, crypto 24/7) — merged to `main`, with the
single-account/options behavior provably unchanged.

## Still out of scope here (later phases)
Ensemble ML models, Discord "I'm doing X because Y" narration, the rebrand, and Phase 5
real money. This plan is strictly **multi-account + crypto-spot + broker stops + the backtester**.
