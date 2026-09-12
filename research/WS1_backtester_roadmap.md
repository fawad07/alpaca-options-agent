# Workstream 1 — Honest Crypto Backtester (roadmap)

**Nature:** offline research under `research/`. No live orders, doesn't touch V1, no branch needed.
**Goal:** find **robust ranges** (not overfit spikes) for crypto **stop % / take-profit % /
position-size %**, validated **out-of-sample (walk-forward)** on BTC/ETH/SOL/LTC.

## Important modeling note
Crypto is **long-only spot** (no shorting). So unlike the options agent (which buys puts on
bear signals), the crypto strategy only **goes long on a bull signal**; a bear signal = stay
flat / exit. The backtest models exactly that.

## Sub-steps
- **1.1 Data pull & prep** — daily bars 2021→now for the 4 coins (`get_crypto_bars`, `loc=us`);
  cache to `research/data/` for fast, reproducible runs; compute the same features as live
  (EMA20/50, RSI14).
- **1.2 Strategy simulator** — mirror the live logic: entry on bull signal → long; exit on
  **−stop%** or **+TP%** (bar-by-bar, first to hit); size via `2% risk ÷ stop%`, capped by
  max-notional%. **Model fees + slippage.** Track equity, trades, drawdown, win rate, profit factor.
- **1.3 Grid sweep** — stop% (≈5–20%) × TP% (≈8–40%) × size-cap% (≈5–20%), per coin.
- **1.4 Walk-forward / OOS validation** *(the honesty core)* — rolling train→test windows
  (e.g., train 12mo → test next 3mo, roll forward). Pick params on train, measure on **unseen**
  test. Find a **broad plateau** that works across coins + windows, not one lucky spike.
- **1.5 Report** — `research/BACKTEST_crypto.md`: recommended robust ranges + reasoning, equity
  curves, **in-sample vs OOS** comparison, and honest caveats.

## Honesty rules (same as the paper's thesis)
- Report **out-of-sample** results, not just best in-sample.
- Benchmark against **buy-and-hold** per coin. **If nothing beats buy-and-hold OOS, say so.**
  (Crypto trended hard in stretches of 2021–2026 — buy-and-hold is a tough bar; we stay honest.)
- Costs modeled so results aren't fantasy.

## Deliverable
Recommended **robust stop/TP/size ranges** to feed the live crypto config — evidence-based,
OOS-validated — plus an honest report. No numbers ship unless they survive out-of-sample.
