"""
test_live_c_caps.py — proves the live Account C hard dollar caps actually clamp.

Run:  .venv/bin/python test_live_c_caps.py
These are the caps from Flag 1 (docs/DESIGN_account_c_live.md, go-live step 2). Until this
passes, Account C is NOT safe to run live. It tests the sizing math directly (no network):
  1. Per-trade notional cap clamps one buy.
  2. Daily spend cap halts new buys once the day's total would exceed it.
  3. A and B (no caps) are completely unaffected.
"""
import config as C
from risk import RiskManager

PASS, FAIL = "✅", "❌"
fails = 0


def check(name, cond):
    global fails
    print(f"  {PASS if cond else FAIL} {name}")
    if not cond:
        fails += 1


print("=== 1) PER-TRADE notional cap ===")
# Big equity so the normal % sizing would WANT far more than the $ cap.
cap = 100.0
rm = RiskManager(equity=50_000, day_start_equity=50_000, open_positions=0,
                 hard_notional_cap=cap)
qty, notional, worst = rm.size_crypto(price=90_000.0, stop_pct=C.CRYPTO_STOP_PCT,
                                      max_notional_pct=C.CRYPTO_MAX_NOTIONAL_PCT)
print(f"    equity $50,000, cap ${cap:.0f} → sized notional ${notional:.2f} (qty {qty})")
check("one buy is clamped to the per-trade cap", notional <= cap + 1e-6)
check("clamped buy still produces a positive qty", qty > 0)

# Same inputs WITHOUT a cap must size bigger (proves the cap is what bound it).
rm_nocap = RiskManager(equity=50_000, day_start_equity=50_000, open_positions=0)
_, notional_nocap, _ = rm_nocap.size_crypto(90_000.0, C.CRYPTO_STOP_PCT, C.CRYPTO_MAX_NOTIONAL_PCT)
print(f"    same inputs, NO cap → notional ${notional_nocap:.2f}")
check("uncapped notional is larger (cap really bit)", notional_nocap > notional)

print("\n=== 2) DAILY spend cap ===")
daily = 300.0
rm = RiskManager(equity=50_000, day_start_equity=50_000, open_positions=0,
                 hard_notional_cap=100.0, daily_spend_cap=daily, spent_today=0.0)
# Simulate three $100 buys across the day.
ok1, _ = rm.spend_ok(100);  rm.spent_today += 100 if ok1 else 0
ok2, _ = rm.spend_ok(100);  rm.spent_today += 100 if ok2 else 0
ok3, _ = rm.spend_ok(100);  rm.spent_today += 100 if ok3 else 0
ok4, why4 = rm.spend_ok(100)   # this 4th would make $400 > $300 → must be refused
print(f"    after $300 spent, 4th $100 buy allowed? {ok4}  ({why4})")
check("first three $100 buys allowed (==$300 cap)", ok1 and ok2 and ok3)
check("4th buy refused (would exceed daily cap)", not ok4)
check("refusal explains why", "daily spend cap" in why4)

# A partial buy that fits exactly up to the cap is allowed; a hair over is not.
rm2 = RiskManager(equity=1, day_start_equity=1, open_positions=0,
                  daily_spend_cap=300.0, spent_today=250.0)
check("a $50 buy at $250 spent is allowed (==cap)", rm2.spend_ok(50)[0])
check("a $51 buy at $250 spent is refused (>cap)", not rm2.spend_ok(51)[0])

print("\n=== 3) A and B (NO caps) are unaffected ===")
rm_ab = RiskManager(equity=50_000, day_start_equity=50_000, open_positions=0)
check("spend_ok always True when no daily cap", rm_ab.spend_ok(1_000_000)[0])
_, n_ab, _ = rm_ab.size_crypto(90_000.0, C.CRYPTO_STOP_PCT, C.CRYPTO_MAX_NOTIONAL_PCT)
check("size_crypto ignores cap when none set", n_ab > 100)

print()
if fails:
    print(f"{FAIL} {fails} check(s) FAILED — caps are NOT trustworthy yet. Do not run C live.")
    raise SystemExit(1)
print(f"{PASS} ALL CHECKS PASSED — the hard caps clamp as intended (proven on the sizing math).")
print("   Still required before live: a paper dress rehearsal of Account C end-to-end.")
