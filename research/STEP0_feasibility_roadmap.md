# Step 0 — Feasibility Spike (roadmap)

**Nature:** read-only investigation. No `v2` branch, no account B, **no changes to V1**,
no live orders on Account A (keeps its track record pure). Deliverable: `STEP0_feasibility.md`
+ a go/adjust decision on the crypto broker-stop (decision B).

## Goal
Confirm the two things the crypto plan rests on before building:
1. Are BTC/USD, ETH/USD, ETC/USD tradable + have data on Alpaca?
2. Can Alpaca hold a **broker stop** on crypto? (Decision 3 = B depends on it.)

## Sub-steps
- **0.1 Coin availability** — each pair tradable + returns data; note min size / increments. If ETC/USD absent → drop or swap.
- **0.2 Crypto stop-order support** *(critical)* — does `place_crypto_order` accept stop / stop-limit / bracket (server-side stops)? Read-only via the tool schema + docs; the definitive live test is deferred to account B. Branches: ✅ supported → B stands · 🟡 stop-limit only → place stop as a 2nd order · ❌ none → pause & re-decide (interim A with faster loop / defer crypto / fast-track C).
- **0.3 Order mechanics** — min notional/qty, fractional increments, allowed time-in-force (crypto often GTC-only), long-only spot, fees. Feeds the CryptoSpotHandler design.
- **0.4 Historical data depth** — how far back daily bars go for BTC/ETH/ETC. Feeds the backtester (WS1).
- **0.5 Findings + decision** — write `STEP0_feasibility.md`; gate: green → backtester + refactor; red on 0.2 → re-decide stops.

## Guardrails
Read-only / paper-safe · no branch / no account B needed · no changes to V1 · probe scripts stay out of the agent.
