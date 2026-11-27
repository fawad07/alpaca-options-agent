# Account B → crypto-only (2026-11-27)

**What changed:** Account B was repurposed from **options + crypto** to **crypto-only**, keeping
its **6 slots** and the 4 coins (BTC/ETH/SOL/LTC). It is now the **live-running paper mirror of
Account C** (the future live crypto account): same crypto-only strategy, same 6 slots, so by the
time C is funded with real money there's a real track record of exactly what that strategy does.

**Why:** to watch, over time, how the crypto-only strategy behaves before putting real money on
it in Account C. This is effectively go-live step 3 (the paper dress rehearsal), running
continuously instead of as a one-off.

## Deliberate trade-offs (named honestly)
- **This ends the original A-vs-B experiment.** B is no longer "options+crypto vs A's
  options-only." Account A is untouched and stays the pure options track.
- **B's past record was options.** Its +7.4%-ish history was almost entirely options (see
  `research/ANALYSIS_crypto_for_C.md`). The crypto-only era starts 2026-11-27; judge the crypto
  strategy from here, not from the mixed history.
- **B is NOT a dollar-for-dollar mirror of live C.** B sizes crypto off the normal rules
  (~2% of equity / stop%, capped at 15% notional) → ~$2,000/trade on ~$104k. Live C will be
  clamped by the hard caps ($100/trade, $300/day). So B shows the **strategy** (which coins,
  when, win/loss, % returns) faithfully; the **dollar sizes** will differ. Compare % behavior.

## Baseline
Per the instruction to "use the current paper cash as the base," B's crypto-only scorecard base
is set to **$104,312.26** (B's equity at the switch, which becomes all-cash once the legacy
options liquidate). The prior $2,000 cash-out rehearsal was cleared so the new epoch measures
cleanly from today. `cashout_state.json` holds this; A's baseline is untouched ($100k).

## The legacy options (auto-handled)
B held 5 option positions at the switch (AAPL call, 3 GOOGL puts, SPY put). They could not be
closed on 2026-11-27 (a Thanksgiving half-day — the options market had already closed at 1pm ET).
Rather than strand them, the agent now **auto-liquidates any holding outside its mandate** at the
next market open (`agent.run_live`, self-healing): it retries each run while the market is shut
and closes them cleanly when it reopens (**Monday 2026-11-30, 9:30 ET**). It counts only
positions that actually closed (verified by re-fetch), so the journal stays honest.

## Net effect
- **A:** unchanged (pure options).
- **B:** crypto-only, 6 slots — the paper mirror of live Account C. Starts trading crypto
  immediately (crypto is 24/7); legacy options clear Monday.
- **C:** still prep-only on `feature/account-c-live`; still not safe to run live.
