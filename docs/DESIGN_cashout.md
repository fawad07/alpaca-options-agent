# Design: Cash-Out / Withdraw (flexible, with tax rehearsal)

**Status: DESIGNED — build on hold.** A dashboard tool to practice withdrawing money from
a paper account the way you would on a real one, so the discipline transfers to live money
later. Supersedes the terser "Bank Profit & Reset" entry in `FUTURE_ENHANCEMENTS.md`.

## Guiding principle (unchanged)
> **It shows the facts and does the math. You decide. It never says an amount is "safe."**
> No safe/unsafe verdict, no buy/sell advice, no tax advice — it lays out what you'd be
> pulling, what it leaves behind, and an *estimated* tax, then hands you the decision. For
> real money, the judgment call is yours and a licensed advisor's / tax pro's.

## Why rehearse on paper
The mechanics and discipline are identical to live money; only the final step is pretend.
What transfers 1:1: realized vs. unrealized, the ledger, sizing the agent off what's left,
and the *when-to-bank* judgment. Only two things change on live money — the withdrawal
becomes a **real transfer**, and **taxes are real** instead of a rehearsal estimate.

---

## 1. Flexible partial withdrawals (not all-or-nothing)

Withdraw **any amount**, not just "bank everything and reset." Two cases:

- **≤ free cash** → a **ledger entry only**, nothing is sold. (On live money: a real transfer.)
- **> free cash** → the tool must **sell positions** to raise the difference, and shows
  exactly what that realizes (a gain *or* a loss) before you confirm.

Presets for convenience: **"banked profit only"**, **"all profit"**, **"custom amount"**,
and the old **"bank everything & reset to $100k"** (now just one option among several).

## 2. What you can actually take out (realized vs unrealized)

You can only truly cash out what's **realized** (already turned into cash). Open positions
are paper until sold. The facts view spells this out with live numbers.

**Worked example — Account B, 2026-11-04:**

| | Amount |
|---|---|
| Equity | $103,296 |
| **Free cash** (withdraw without selling) | **$61,192** |
| Open positions | $42,104 — currently **down $1,577** (paper loss) |
| Profit vs $100k | **+$3,296** = ~$4,873 realized − $1,577 unrealized |

The instructive part: B's positions are **underwater right now**. "Bank everything & reset"
*today* would **sell them and turn the $1,577 paper loss into a real loss.** The tool shows
this plainly so you can decide whether now is the moment — it never tells you not to.

## 3. Tax rehearsal (practice the after-tax number)

On paper no tax is charged, but the tool **estimates** it so you build the habit:

- **The taxable event is *realizing a gain* (selling at a profit), not the withdrawal itself.**
  Cash that's already settled can be withdrawn without a new tax event; selling a position
  at a gain to fund a withdrawal *does* create one.
- **Assumed tax rate** — a number *you* set (like the simulator's assumed return), because
  the real rate depends on your bracket and holding period (short-term <1yr = higher;
  long-term ≥1yr = lower). Default to a plausible short-term rate, clearly labelled an
  assumption.
- The tool shows: **realized gain this action → estimated tax at your rate → after-tax
  proceeds.** Labelled a *rehearsal estimate, not tax advice*; $0 is actually charged on paper.

## 4. The accounting (one honest number)

```
working_equity = actual_equity − cumulative_withdrawn
```
- `cumulative_withdrawn` = running total taken out (from the ledger).
- Every P&L figure and the agent's position sizing use `working_equity`, so withdrawn money
  isn't re-traded. On paper the cash physically stays (accounted as gone); on live it leaves.
- **True lifetime return** = `(equity + cumulative_withdrawn − cumulative_contributed) ÷
  cumulative_contributed` — the scorecard that stays honest once money moves in and out.

## 5. The flow (one withdrawal)

**Facts view** → shows free cash, realized vs unrealized, and the presets.
**Preview** (nothing executes) → for the chosen amount: what (if anything) gets sold, the
gain/loss that realizes, the estimated tax, the after-tax proceeds, and what the account
looks like afterward. Returns a one-time nonce.
**Confirm** (explicit) → hard-verify paper account → if needed `cancel_all_orders` +
sell the required positions (poll until done) → append to the ledger (amount, realized
gain/loss, est. tax, new `cumulative_withdrawn`) → agent resumes sized off `working_equity`.

## Pieces to build (when greenlit)
| Piece | Job |
|---|---|
| `cashout_state.json` | Per-account `cumulative_withdrawn` + `cumulative_contributed`. |
| `withdrawals-{A,B}.csv` | Ledger: timestamp, amount, sold?, realized gain/loss, est. tax, running totals. |
| `capital.py` | `working_equity`, `withdrawn`, `true_return` helpers, used everywhere. |
| `risk.py` (edit) | Size off `working_equity`. |
| `dashboard.py` + `.html` | Facts view, amount picker + presets, tax-rate input, preview→confirm. |
| `refresh_stats.py`, `compare.py`, agent summary | Switch to `working_equity`. |

## Safety guardrails
- **Off unless `ENABLE_CASHOUT=1`** (default disabled).
- **Token-gated, POST-only, two-step** (preview nonce echoed on confirm).
- **Paper-only** hard guard — refuses the instant it detects a live account.
- **Account A** needs an extra "this alters your research baseline — sure?" confirm.
- Shows facts + estimates only — **never** a safe/unsafe verdict or tax advice.

## Paper vs live
| | Paper (now) | Live (later) |
|---|---|---|
| Realized vs unrealized, ledger, sizing | ✅ same | ✅ same |
| Selling to raise cash | ✅ real | ✅ real |
| The withdrawal | 📒 ledger entry (cash stays) | 💸 real transfer (cash leaves) |
| Tax | rehearsal estimate, $0 charged | **real** |

## Build order
1. `working_equity` / ledger plumbing with everything zero (invisible; nothing changes).
2. Facts + preview as a CLI (`./run.sh cashout b <amount>`), test on B.
3. Dashboard facts view + tax estimate.
4. The amount picker + preview→confirm button (gated).
5. Docs + security pass.

## Open decisions
1. **Default assumed tax rate** for the rehearsal (e.g., 25%?) — editable either way.
2. Build on paper now against B, or still wait for a longer A-vs-B record / a 3rd account?

**Build status: HELD** — design only (user, 2026-11-04). Direction locked: flexible partial
withdrawals + tax rehearsal.
