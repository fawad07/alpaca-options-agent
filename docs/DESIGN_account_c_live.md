# Design: Account C — LIVE MONEY (crypto-only, 6 slots)

**Status: 🧰 PREP / SCAFFOLDING (2026-11-19).** The plumbing for a real-money Account C is
built and in the tree, but it is **inert and OFF by default** — nothing trades live until
*you* complete the go-live checklist below, by hand. The assistant builds the rails; it does
**not** add live keys, flip the live switch, create a live cloud workflow, or place the first
real order. Those are your deliberate steps.

## What C is
- **Real money.** A live Alpaca account (not paper).
- **Crypto only** — BTC/USD, ETH/USD, SOL/USD, LTC/USD. No options.
- **6 concurrent slots** (`max_concurrent=6`).
- Same signal + risk logic the paper agent already runs; only the money is real.

## The honest caveat (unchanged, and it matters more here)
The strategy still has **no proven edge** — the A/B paper record is too short to tell skill
from luck. Going live funds an unproven strategy with real dollars. This doc makes it *safe
to operate*, not *proven to work*. No part of it is financial advice.

---

## Safety architecture (defense in depth)

C can touch real money **only when ALL of these are true at once.** Miss any one → C stays
on paper or idle:

| Gate | Where | Default |
|---|---|---|
| 1. `DEPLOY_ACCOUNT=C` | env | unset (runs A) |
| 2. `ENABLE_LIVE_C=1` (master switch) | `config.py` | **OFF** |
| 3. `ALPACA_LIVE_API_KEY` + `ALPACA_LIVE_SECRET_KEY` present | `accounts.py` (no paper fallback) | empty → safe auth-fail |
| 4. `KILL_LIVE_C` not set (emergency stop) | `config.py` | not set |
| 5. Live cloud workflow armed | `.github/workflows/trade-c.yml` | exists but **inert**: manual-only, schedule commented out, typed confirmation required |

**The one fork line:** `mcp_test.server_params` sends `ALPACA_PAPER_TRADE='false'` *only* when
`acct.live AND ENABLE_LIVE_C AND not KILL_LIVE_C`. Every other path ships `'true'` (paper).
This is the single line that can route to real money; it defaults to paper.

**Other guards already wired:**
- **Cash-out tool is blocked from C.** `cashout._assert_paper(acct)` now refuses any account
  with `live=True`, so the withdrawal/rehearsal tool can never sell real positions.
- **No paper-key fallback for C.** Unlike B (which falls back to the A keys), C's keys come
  *only* from `ALPACA_LIVE_*`. Forget them → empty keys → the broker rejects auth → no trade.
- **Kill switch** (`KILL_LIVE_C=1`) forces C back to paper on its very next run.

## What was built in this prep pass (inert)
| File | Change |
|---|---|
| `accounts.py` | `Account.live` flag; `ACCOUNT_C` defined (crypto-only, cap 6, live-only keys); registered in `ACCOUNTS`. |
| `config.py` | `ENABLE_LIVE_C` (off), `KILL_LIVE_C`, `LIVE_C_MAX_NOTIONAL_PER_TRADE`, `LIVE_C_MAX_DAILY_SPEND`. |
| `mcp_test.py` | `server_params` paper→live fork, triple-gated; paper by default. |
| `cashout.py` | `_assert_paper(acct)` refuses live accounts. |
| `.env.example` | Documented, commented-out live vars (nothing active). |

| `.github/workflows/trade-c.yml` | Live cloud workflow, built **inert**: manual-trigger only (no active schedule), typed `LIVE-C` confirmation, keys from repo secrets, `KILL_LIVE_C` repo-var halt. |

**Deliberately NOT done** (these are the dangerous, go-live-only acts, left for you):
- The workflow's **`schedule:` cron is commented out** — uncommenting it *and* merging the
  file to `main` is what makes C fully auto on real money unattended. Left for your deliberate
  choice; scheduled workflows only fire from the default branch, so on a feature branch it
  can't auto-run regardless.
- **Hard spend caps are DEFINED but NOT YET ENFORCED.** `LIVE_C_MAX_*` are passed into the
  workflow but are just numbers until wired into sizing — see checklist step 2. Not active yet.
- No real keys set, no live switch flipped, no first order placed.

---

## Go-live checklist — YOUR by-hand steps (in order; do not skip)

> Do these yourself, deliberately. The assistant can help *write* code for steps 1–2, but
> **will not** perform steps 3–7 (adding real keys, flipping the switch, creating the live
> workflow, or placing real orders).

1. **Let A/B run longer first.** Get a track record long enough to mean something, including
   a losing stretch. Right now it's too short — this is the honest gate, not a technical one.
2. **Enforce the hard caps (and test on paper).** Wire `LIVE_C_MAX_NOTIONAL_PER_TRADE` and
   `LIVE_C_MAX_DAILY_SPEND` into the crypto sizing / risk gate, then prove on a PAPER run that
   a buy is capped and the daily limit halts new buys. Until this passes, do not go live.
3. **Paper dress rehearsal of C itself.** Point `ALPACA_LIVE_*` at a *fresh paper* crypto
   account, keep `ENABLE_LIVE_C` OFF, run `DEPLOY_ACCOUNT=C` by hand, and confirm C opens/caps
   crypto correctly with 6 slots. Fix anything odd. (Keep A and B untouched.)
4. **Fund the real account small.** Put in an amount you can afford to lose entirely. Start
   tiny — the caps default to $100/trade, $300/day for a reason.
5. **Add real keys + flip the switch (you, by hand).** Put `ALPACA_LIVE_*` in `.env`, set
   `ENABLE_LIVE_C=1`. Do the first few runs **manually** (`DEPLOY_ACCOUNT=C ./run.sh ...`),
   watching each one. Verify fills on the real Alpaca site.
6. **Go unattended (the real "fully auto" step).** `trade-c.yml` already exists but is inert.
   To automate it: set the GitHub secrets (`gh secret set ALPACA_LIVE_API_KEY` /
   `ALPACA_LIVE_SECRET_KEY`), **uncomment the `schedule:` block**, and **merge the file to
   `main`** (scheduled workflows only fire from the default branch). Keep the cron sparse at
   first. Until you do all three, the workflow only runs when you click "Run workflow" and type
   `LIVE-C`. This is a conscious decision — make it one.
7. **Know your stop.** `KILL_LIVE_C=1` (or pull the live keys) halts C. Decide in advance the
   loss at which you stop, and who/what enforces it.

## How this keeps A and B safe
- A and B are untouched — same keys, same paper fork, same behavior. Adding C changed only
  new, gated code paths.
- C is crypto-only and separate; it is not part of the A-vs-B research comparison.
