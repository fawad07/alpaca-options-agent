# Future Enhancements — Risk Gate

Parked ideas that are **designed but deliberately NOT built yet**. Each entry is a
blueprint to pick up later, with the reason it's deferred. Nothing here is wired into
the live agent, the dashboard, or the workflows.

**Prime directive (unchanged):** protect the honest A-vs-B research. No enhancement
ships if it disturbs Account A (the pure V1 options-only research account) or muddies
the live A-vs-B comparison while that track record is still accumulating.

---

## 1. "Bank Profit & Reset" button  —  *status: DESIGNED, DEFERRED*

**What it is:** a dashboard button that cleanly banks an account's profit and resets its
working baseline to $100k — the "realize everything, then withdraw the gain, then keep
trading" cycle — done safely with a preview-then-confirm flow.

**Why deferred (read first):** running this on Account A or B *right now* would change
that account's numbers and break the clean A-vs-B comparison the research paper depends
on. It's wanted for the future, but not while the current live experiment is in flight.
Revisit only once the A-vs-B record is long enough that a reset won't compromise it (or
build it against a *third*, separate account so A and B stay pure).

### Decisions locked (2026-09-27)
- **Withdrawal model:** *Simulate + ledger*. Positions are really closed (gains genuinely
  realized), but the "withdrawal" is a recorded ledger entry — a paper account can't wire
  cash out (Alpaca exposes `close_all_positions` but **no** withdraw/transfer tool). On a
  real account, the same code would swap the ledger entry for a real transfer.
- **After banking:** *Reset to $100k and keep trading* (bank the win, keep playing).
- **Scope:** *Both A and B*, but A requires an extra, louder confirmation because it alters
  the research baseline.

### The key architectural insight
Paper cash can't physically leave, so "reset to $100k" means *accounting* for it as removed,
via one number:

```
working_equity = actual_equity − cumulative_banked
```

- `cumulative_banked` = running total "withdrawn" over time (from the ledger).
- Every P&L figure and the agent's position sizing use `working_equity`, not the raw balance.

Worked example (B at the time of design): actual $110,460, banked $0 → working $110,460,
cycle profit **+$10,460**. Bank it → `cumulative_banked = $10,460` → working = $110,460 −
$10,460 = **$100,000**, cycle profit **$0**. The banked $10,460 sits idle as parked cash
(the withdrawn profit); the agent resumes sized off $100k, not the inflated $110k.

### The flow (one button press)
**Preview** (nothing executes): read equity + open positions → compute cycle profit → list
what will be sold → warn if options are held while the market is closed → return the plan
**and a one-time nonce**.

**Confirm** (explicit click):
1. Hard-verify it's a **paper** account.
2. `cancel_all_orders` → `close_all_positions` → poll until flat (gains realized for real).
3. Read post-close equity → `banked = equity − 100k − prior_banked`.
4. If `banked ≤ 0`, abort ("no profit to bank").
5. Append to the ledger, update `cumulative_banked`.
6. Agent resumes next run, sized off the fresh $100k.

### Pieces to build (when greenlit)
| Piece | Job |
|---|---|
| `cashout_state.json` | Per-account `cumulative_banked` — single source of truth. |
| `withdrawals-{A,B}.csv` | Audit ledger: timestamp, equity before, profit banked, cumulative, new baseline. |
| `capital.py` (helper) | `working_equity(acct, actual)` and `banked(acct)`, used everywhere. |
| `risk.py` (edit) | Size positions off `working_equity` so parked profit isn't re-traded. |
| `dashboard.py` + `.html` | Cards show working equity + cycle P&L + lifetime-banked line; the button + confirm step. |
| `refresh_stats.py`, `compare.py`, agent summary | All switch to `working_equity` so every view agrees. |

### Safety (this reverses the dashboard's read-only hardening)
- **Off unless `ENABLE_CASHOUT=1`** (default disabled).
- **Token-gated, POST-only, two-step** (preview issues a nonce; confirm must echo it) — no
  stray click or prefetch can fire it.
- **Paper-only** hard guard — refuses the instant it detects a live account.
- **Account A** requires an extra "this alters your research baseline — are you sure?" confirm.

### Suggested build order
1. **Plumbing first** — `working_equity` everywhere with `banked = 0` (invisible refactor; A
   and B behave exactly as today). Prove nothing breaks.
2. **Core logic as a CLI** — `./run.sh cashout b`, test on B with the market open.
3. **Ledger + dashboard display** of banked/cycle numbers.
4. **The button + gated endpoint + confirm.**
5. **Docs + security pass.**

### Honest caveats
- Simulated withdrawal (paper can't wire out); cash stays but is accounted as removed.
- Options only close during market hours → a full clean reset needs the market open if
  options are held (crypto closes 24/7).
- Banking = exiting = giving up future upside on those positions; the agent rebuilds next run.
- Real-money version must also account for **taxes** (the banked figure is pre-tax) and
  settlement delays.
