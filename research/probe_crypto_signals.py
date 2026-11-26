"""
probe_crypto_signals.py — how often does Account C actually have crypto to BUY?

Flag-2 hypothesis H1 (research/ANALYSIS_crypto_for_C.md): with no options competing for
slots, Account C would run the crypto strategy far more than B ever did. This probe measures
that directly, on real history, using the SAME production logic (signals.signal + the
long-only bull filter the crypto handler applies):

  a BUY fires when  direction == 'bull'  AND  confidence >= MIN_CONFIDENCE.

For each coin it walks daily bars and reports the % of days a BUY would have fired, the
current signal, and the longest BUY streak. Then an aggregate: on what share of days at
least one coin had a BUY (i.e. C would have had something to open).

Read-only. No trading, no account, no network except free daily bars.
Run:  .venv/bin/python research/probe_crypto_signals.py  [years]   (default 2)

Honest limits: this measures how often a BUY SIGNAL exists, NOT how often C would trade
(it ignores slot capacity, one-position-per-symbol dedup, and positions already held).
It uses daily bars, so the signal changes at most once per day even though C runs intraday.
It is long-only trend-following, so a high BUY rate in an uptrend and a low one in chop/
downtrend is expected — that is H2, visible here as the rate swings with the sample window.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import data as D
from signals import add_features

YEARS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
RNG = f"{YEARS}y"
WARMUP = C.EMA_SLOW + 5          # signals need this many bars before they're meaningful


def buy_series(df):
    """Per-day: (is_bull_buy, direction, confidence) using identical logic to signals.signal.
    add_features uses causal ewm/rolling, so row i matches signal(df.iloc[:i+1])."""
    f = add_features(df)
    out = []
    for i in range(len(f)):
        if i < WARMUP:
            out.append((False, 'warmup', 0.0)); continue
        ema_f, ema_s, rsi = f['EMA_fast'].iloc[i], f['EMA_slow'].iloc[i], f['RSI'].iloc[i]
        trend_up = ema_f > ema_s
        gap = abs(ema_f - ema_s) / ema_s if ema_s else 0.0
        conf = min(1.0, 0.5 + gap * 8)
        if trend_up and rsi < C.RSI_BULL_MAX:
            direction = 'bull'
        elif (not trend_up) and rsi > C.RSI_BEAR_MIN:
            direction = 'bear'
        else:
            direction = 'neutral'
        is_buy = (direction == 'bull') and (conf >= C.MIN_CONFIDENCE)
        out.append((is_buy, direction, round(conf, 2)))
    return out


def longest_run(flags) -> int:
    best = cur = 0
    for b in flags:
        cur = cur + 1 if b else 0
        best = max(best, cur)
    return best


print(f"\n=== Crypto-signal frequency probe — last {YEARS}y, BUY = bull & conf≥{C.MIN_CONFIDENCE} ===")
print(f"    universe: {', '.join(C.CRYPTO_UNIVERSE)}   (same signal logic the live agent uses)\n")
print(f"    {'coin':<9}{'days':>6}{'BUY days':>10}{'% days':>9}{'longest':>9}   current signal")

per_day_counts = None   # across coins, how many had a BUY on each aligned day
n_days_ref = 0
rows_ok = 0
for coin in C.CRYPTO_UNIVERSE:
    df = D.fetch_bars(coin, 'crypto', rng=RNG)
    if df.empty or len(df) <= WARMUP:
        print(f"    {coin:<9}{'—':>6}   (no data)")
        continue
    rows_ok += 1
    series = buy_series(df)
    evaluated = [(b, d, c) for (b, d, c) in series if d != 'warmup']
    flags = [b for b, _, _ in evaluated]
    nbuy = sum(flags)
    pct = 100.0 * nbuy / len(flags) if flags else 0.0
    cur_b, cur_d, cur_c = evaluated[-1]
    cur = f"{cur_d} {cur_c:.2f}" + ("  → BUY" if cur_b else "")
    print(f"    {coin:<9}{len(flags):>6}{nbuy:>10}{pct:>8.0f}%{longest_run(flags):>9}   {cur}")
    # aggregate across coins on the trailing N days they share
    tail = flags[-min(len(flags), 500):]
    if per_day_counts is None:
        per_day_counts = [0] * len(tail); n_days_ref = len(tail)
    n = min(len(tail), len(per_day_counts))
    per_day_counts = [per_day_counts[-n + k] + (1 if tail[-n + k] else 0) for k in range(n)]

print()
if rows_ok and per_day_counts:
    any_buy_days = sum(1 for c in per_day_counts if c >= 1)
    share = 100.0 * any_buy_days / len(per_day_counts)
    avg_coins = sum(per_day_counts) / len(per_day_counts)
    print(f"    AGGREGATE (last {len(per_day_counts)} aligned days):")
    print(f"      • on {share:.0f}% of days at least ONE coin had a BUY signal")
    print(f"      • on an average day {avg_coins:.1f} of {rows_ok} coins had a BUY")
    verdict = ("C would usually have something to open" if share >= 60 else
               "C would sometimes have something to open" if share >= 25 else
               "C would RARELY have a signal — long stretches with nothing to buy")
    print(f"      → H1 read: {verdict}.")
print("\n    Caveat: measures signal EXISTENCE, not trades (ignores slots/dedup/held positions),")
print("    on daily bars, long-only. A paper dress rehearsal of C is still the real test.")
