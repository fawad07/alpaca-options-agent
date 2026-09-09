# Risk Gate v2 — Roadmap

**Goal:** an *evolved* version of the Alpaca agent that keeps the proven skeleton
(data → signal → risk → MCP execution → exits → autonomy → journal) and adds
**explainability, ML-backed decisions, backtest-gated strategy selection, richer
P&L reporting, and a disciplined path to real money.**

**Prime directive (non-negotiable):** every new capability must pass the same
**out-of-sample honesty bar** the v1 paper describes before it is trusted, and
**no real capital** is deployed until a long live-paper track record beats
buy-and-hold OOS. The post-submission −1.30% week is the standing reminder of why.

---

## What v1 already gives us (reused, not rebuilt)
| Component | File(s) | Status |
|---|---|---|
| Live loop + exits | `agent.py` | ✅ working |
| Signals (EMA/RSI) | `signals.py` | ✅ (from ai-trading-pipeline) |
| Risk gates + sizing | `risk.py` | ✅ (from Trading_signal_production) |
| MCP execution | `mcp_client.py` | ✅ |
| Autonomy + journal | `cron_once.py`, `journal.py` | ✅ |
| Backtest / OOS check | `backtest_signal.py` | ✅ (from ai-trading-pipeline) |
| Monitoring | `dashboard.py`, `results.py` | ✅ |

v2 is **~80% integration** of things you've already built, plus two genuinely new
layers (explainability, ML).

---

## Target module map (v2)
```
data/         market data adapters (Alpaca equities/options; later crypto)
features/     indicator library (EMA, RSI, MACD, Bollinger, ATR, breakout)
models/       ML models + calibration (XGBoost/RF) → confidence scores
strategies/   strategy definitions; each declares its params + universe
validate/     backtest engine + OOS gate → which strategies may trade
decide/       ensemble: combine rule signals + ML confidence → ranked decision
risk/         the v1 gates + ATR stops + capital controls
execute/      MCP order placement + exit management (v1)
explain/      NEW — natural-language rationale generator
notify/       NEW — Discord/Telegram push + P&L summary
ops/          scheduler, journal, kill-switch, reconciliation
```

---

## Phased plan (all paper until Phase 5)

### Phase 0 — Foundation / merge
- Stand up the v2 repo on v1's live loop; introduce the module map above.
- Port the backtest engine and any ML from Trading_signal_production / ai-trading-pipeline into `validate/` and `models/`.
- **Exit criterion:** v1 behavior reproduced under the new structure; all tests green.

### Phase 1 — Explainability + notifications ⭐ (do first; highest satisfaction, lowest risk)
- `explain/`: for every decision, emit *"I'm doing X because Y, keeping these parameters in mind,"* built from the structured decision (signal values, confidence, risk state, exit plan).
- `notify/`: push that message + a P&L summary to **Discord or Telegram**.
- **Exit criterion:** you receive a readable message on every entry, exit, and block, plus a daily P&L digest.

### Phase 2 — ML confidence + OOS strategy gate
- `models/`: train calibrated classifiers; output a probability the trade is favorable.
- `decide/`: fuse rule signal + ML confidence into one score; require a combined threshold.
- `validate/`: an OOS gate that runs periodically and **enables/disables** each strategy based on whether it beats buy-and-hold OOS. Failing strategies are logged but muted.
- **Exit criterion:** the agent only trades strategies currently passing OOS, and the explanation cites model confidence.

### Phase 3 — Multi-strategy / multi-instrument
- Support several strategies at once (trend, mean-reversion, etc.) and stocks + options (+ crypto later), coordinated by `decide/` under one risk budget.
- **Exit criterion:** the agent runs ≥2 validated strategies across ≥2 instrument types without breaching the global risk budget.

### Phase 4 — Hardening for real money
- Kill-switch (halt-all), secret management, per-day and per-strategy capital caps, failure/heartbeat alerts, order/position reconciliation, and a long paper track record with OOS outperformance.
- **Exit criterion:** an auditable, months-long paper record that beats buy-and-hold OOS, plus every safety control tested.

### Phase 5 — Real money (tiny, gated)
- Only after Phase 4's evidence. Start at **minimal size**, real-money limits stricter than paper, continuous monitoring.
- **Constraint I will hold us to:** I can build the system and flag risks, but capital decisions are yours (ideally with a licensed advisor). No shortcuts past Phase 4.

---

## The "it tells you" message (Phase 1 target)
```
🟢 BUY 2× NVDA call · ~32 DTE · at-the-money
WHY:  trend up (EMA20 > EMA50) · RSI 58 (not overbought) · breakout confirmed
      · ML confidence 0.71 (passed out-of-sample)
KEEPING IN MIND:  risking 1.8% ($1,800) · 3/5 slots · daily loss 0.4% (< 5% halt)
      · 32 DTE (14–60) · exit +50% / −50%
📊 Portfolio P&L: +1.82%
```

---

## Locked decisions (2026-09-09)
1. **Instruments:** **both stocks and crypto** (options where available). Multi-asset from the start.
2. **Notification channel:** **Discord** (reuse the webhook from the prior project).
3. **Name:** **rebrand** (candidates below — pick one).
4. **ML scope:** **ensemble** from the start (multiple models → blended, calibrated confidence).
5. **Real money:** **Phase 5 still wanted**, but **run paper meaningfully longer first** — extended live-paper track record with OOS outperformance before any real capital.

### Name candidates (pick one, or mix)
- **Sentinel** — watchful, risk-first guardian.
- **Ledger** — honest, auditable record at its core.
- **Cassandra** — tells the truth about risk even when unwelcome (the honesty angle).
- **Bastion** — a defended position; risk-gated by design.
- **Northstar** — disciplined guidance, not hype.
- **Keel** — what keeps a ship stable; understated, stability-first.

### Implications of these choices
- Multi-asset (stocks + crypto) means the **data layer** needs a crypto adapter (Alpaca crypto and/or an exchange) alongside equities/options, and the **risk layer** must budget across asset classes under one global cap.
- Discord means Phase 1's `notify/` targets a **Discord webhook** (you already have one).
- Ensemble ML means `models/` ships with ≥2 base learners + a calibrator, and the **OOS gate** validates the *ensemble's* output, not a single model.
- "Run paper longer" makes the **journal + track-record** the gating evidence for Phase 5.

---

## Recommended first step
**Phase 0 + Phase 1** together: scaffold the v2 repo and ship the explainability +
notification layer, because "tell me what it's doing" is the feature you most want
and it carries almost no risk. ML and backtest-gating follow in Phase 2.
