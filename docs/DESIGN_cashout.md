# Design: Cash-Out / Withdraw (flexible, with tax rehearsal)

**Status: ✅ BUILT (paper, Account B) — 2026-11-05.** A dashboard + CLI tool to practice
withdrawing money from a paper account the way you would on a real one, so the discipline
transfers to live money later. Supersedes the terser "Bank Profit & Reset" entry in
`FUTURE_ENHANCEMENTS.md`. Decisions locked at build time: **default assumed tax rate 24%**
(realistic mid federal short-term/ordinary-income bracket — see §3), **built against Account B**.
The feature is **OFF by default** and Account A is never touched, so the A-vs-B research is
unaffected until you turn it on and record a withdrawal. See "What was built" at the bottom.

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

## Decisions (resolved 2026-11-05)
1. **Default assumed tax rate = 24%.** Account B trades crypto actively (positions held
   days, not a year) → every gain is **short-term**, taxed as **ordinary income** federally,
   not the lower long-term rate. 24% is a realistic mid federal bracket; your real number =
   your federal bracket (10/12/22/24/32/35/37%) **plus** state income tax (0% in TX/FL/WA/NV
   … up to ~13% in CA). Editable in the UI, via the CLI `--rate`, or `CASHOUT_TAX_RATE` env.
   Clearly labelled an assumption; **not tax advice**.
2. **Built against Account B**, on paper, now. Account A stays pure (never withdrawn from).

---

## What was built (2026-11-05)

New, isolated pieces — the trading agent, the risk gates' *logic*, and Account A are all
untouched. The one sizing change is invisible while nothing is withdrawn (`working == actual`).

| File | What it does |
|---|---|
| `capital.py` | The accounting: `working_equity`, `withdrawn`, `true_return`, state + ledger I/O. Invisible at zero. |
| `cashout.py` | The engine + CLI: `facts` / `preview` / `execute`. Paper-only guard; crypto-first sell plan; tax rehearsal. |
| `cashout_state.json` | Per-account `withdrawn` + `contributed` (both start 0 / $100k). |
| `withdrawals-B.csv` | Append-only audit ledger (created on first withdrawal). |
| `dashboard.py` | Gated routes `/api/cashout/{facts,preview,confirm}` + working-equity cards for B. |
| `templates/dashboard.html` | The 💸 panel: facts, amount + presets, tax-rate input, preview → confirm, ledger. |
| `config.py` | `ENABLE_CASHOUT` (default off) + `CASHOUT_TAX_RATE_DEFAULT = 0.24`. |
| `agent.py` | Sizes off `working_equity` (one line; identical to before while withdrawn = 0). |
| `run.sh` | `./run.sh cashout <facts|preview|execute> b [amount]`. |

### How to use it

**CLI (always available, local):**
```bash
./run.sh cashout facts   b              # read-only snapshot
./run.sh cashout preview b 2500         # read-only: what it would do (sell? tax? after-tax?)
./run.sh cashout execute b 2500 --yes   # ACTS on paper: sells if needed, records the ledger
```

**Dashboard button (off by default):** launch with the flag, then use the 💸 panel:
```bash
ENABLE_CASHOUT=1 ./run.sh dashboard
```
Preview is read-only; **Confirm** pops a summary dialog, then records it. The confirm endpoint
is POST-only, paper-only, and needs a single-use nonce a matching preview just issued — no
stray click or prefetch can move money.

### How it stays out of the research
- **Account A** is never withdrawn from → `working == actual` forever → byte-identical to today.
- **The cloud agent** reads `cashout_state.json` from its checkout. On this feature branch it
  isn't on `main`, so the cloud bots keep sizing off full equity — a withdrawal here is a pure
  **local rehearsal** until you merge. Merge to `main` only when you want a B withdrawal to
  actually shrink what the live agent trades. (A's state stays zero either way.)

### Not done on purpose
- No real transfer (paper can't wire out — it's a ledger entry; the code swaps to a real
  transfer on a live account).
- `execute`/Confirm is left for **you** to run with an amount you choose — the first real
  withdrawal changes B's working numbers, so it's your call, not something auto-run.
