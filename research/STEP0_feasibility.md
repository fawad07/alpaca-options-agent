# Step 0 — Feasibility findings (2026-09-12)

Read-only probe of the Alpaca MCP server (account A keys). No orders placed.

## 0.1 Coin availability
| Coin | Status |
|---|---|
| **BTC/USD** | ✅ tradable, daily data from 2021-01-01, live ~$77k |
| **ETH/USD** | ✅ tradable, daily data from 2021-01-01, live ~$2.5k |
| **ETC/USD** | ❌ **NOT available on Alpaca** (empty data, no error) → must drop or replace |

**Available replacements** (all with long history): LTC/USD, SOL/USD, DOGE/USD, LINK/USD,
BCH/USD, UNI/USD (from 2021-01-01); AVAX/USD (2021-11), AAVE/USD (2021-07); shorter: DOT/USD
(2023-08), XRP/USD (2024-01).

## 0.2 Crypto stop-order support *(decision B — the linchpin)*
Inspected `place_crypto_order` params vs stock/option:
- **Crypto accepts:** `type`, `limit_price`, **`stop_price`** → **standalone STOP / stop-limit orders ARE supported.** ✅
- **Crypto does NOT have:** `order_class`, `legs`, `take_profit_*`, `stop_loss_*` → **no one-shot bracket/OCO** (those exist only on `place_stock_order`).

**Verdict on B: achievable** — but as a **separate broker-held stop order placed right after entry**, not a single bracket. This still meets your core requirement: the **stop-loss is broker-held (no blind window).**
- **Take-profit:** since there's no OCO, TP is either a separate resting limit sell (broker-held) with the **agent cancelling the sibling when one fills**, or agent-managed. Design detail for `CryptoSpotHandler`.
- ⚠️ **Confirm live:** do a definitive stop-order acceptance test on **account B** (paper) before relying on it — the schema allows it; a live paper order proves the API accepts `type=stop` for crypto.

## 0.3 Order mechanics (for CryptoSpotHandler)
- Data calls need a **`loc` param** (`us`) — the crypto data adapter must pass it.
- Sizing: both **`qty` (fractional)** and **`notional`** are supported (crypto is fractional).
- **Long-only spot** (no naked shorting) — fits the defined-risk ethos.
- Time-in-force: crypto is typically **GTC/IOC** (not DAY) — confirm allowed values on the live test.
- Fees apply — model them in the backtester.

## 0.4 Historical data depth (for the backtester)
Daily bars from **2021-01-01 → present** (~5.7 years) for BTC/ETH and all the 2021-listed
replacements. **Sufficient for a real walk-forward, out-of-sample backtest.** `loc=us`.

## 0.5 Decision — GREEN, with two adjustments
1. **Drop ETC/USD** (unavailable). Pick replacement(s) from the available list → **user decision**.
2. **Crypto stop = separate broker order, not a bracket.** Adjust `CryptoSpotHandler`:
   entry order → **place broker stop** (type=stop/stop_limit, stop_price) → manage take-profit
   as a separate limit + **agent-side OCO cancellation**. Core need (broker-held stop, no blind
   window) is **met**. Do the live acceptance test on account B.

**Everything else in the plan proceeds unchanged.** Next: pick the replacement coin(s), then
Workstream 1 (backtester) + the v2-branch refactor.
