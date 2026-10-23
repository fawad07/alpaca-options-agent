"""
simulator.py — the "What-If" contribution simulator (pure math, no side effects).

Two independent jobs, both fed an account's REAL return data:
  • simulate_history(returns, ...)  — apply an account's real past daily returns to a
    regular-deposit schedule → Value vs Contributions over the real window.
  • simulate_forward(start, ...)    — project forward as a RANGE (never a prediction) with
    TWO engines side by side: a smooth formula ±band, and a Monte-Carlo cone (1,000 runs).
    Drift (avg return) is a caller-supplied assumption (honest: no proven edge); only the
    spread comes from the account's real volatility.

Pure functions only — no trades, no account access, no Flask. The dashboard route gathers
the real equity series and calls these; the trading agent never touches this file.
See docs/DESIGN_whatif_simulator.md.
"""
from __future__ import annotations
import math
import numpy as np

Z_90 = 1.2816          # z-score for the 10th/90th percentile band


def simulate_history(returns: list[float], start: float, add: float, every: int) -> dict:
    """returns: real daily fractional returns. add a contribution every `every` data points.
    Returns parallel Value and Contributions series (length len(returns)+1)."""
    value = float(start)
    contributed = float(start)
    out_v, out_c = [round(value, 2)], [round(contributed, 2)]
    for i, r in enumerate(returns, start=1):
        value *= (1.0 + float(r))
        if every and i % every == 0:
            value += add
            contributed += add
        out_v.append(round(value, 2))
        out_c.append(round(contributed, 2))
    return {'value': out_v, 'contributed': out_c,
            'summary': _summary(contributed, value)}


def simulate_forward(start: float, add: float, every: int, horizon_days: int,
                     daily_mu: float, daily_sigma: float,
                     n_runs: int = 1000, points: int = 60) -> dict:
    """Project `horizon_days` ahead. `daily_mu` is the assumed average daily return;
    `daily_sigma` is the real daily volatility. Returns both engines sampled at ~`points`
    steps, each with good(90th)/mid(50th)/bad(10th) and a deterministic contributions line."""
    horizon_days = max(int(horizon_days), 1)
    step = max(1, horizon_days // max(points, 1))
    sample_days = list(range(0, horizon_days + 1, step))
    if sample_days[-1] != horizon_days:
        sample_days.append(horizon_days)
    sset = set(sample_days)

    # contributed (deterministic) at each day
    def contributed_at(d):
        return float(start) + (add * (d // every) if every else 0.0)

    # ---- Engine 1: formula ±band (smooth, idealized) ----
    mid = float(start)
    band_mid, band_good, band_bad, contributed = {}, {}, {}, {}
    for d in range(0, horizon_days + 1):
        if d > 0:
            if every and d % every == 0:
                mid += add
            mid *= (1.0 + daily_mu)
        if d in sset:
            spread = math.exp(Z_90 * daily_sigma * math.sqrt(d))    # widens with √time
            band_mid[d] = mid
            band_good[d] = mid * spread
            band_bad[d] = mid / spread
            contributed[d] = contributed_at(d)

    # ---- Engine 2: Monte-Carlo cone (1,000 real-volatility paths) ----
    rng = np.random.default_rng(42)       # fixed seed → stable cone between refreshes
    vals = np.full(n_runs, float(start), dtype=float)
    mc_good, mc_mid, mc_bad = {}, {}, {}
    if 0 in sset:
        mc_good[0] = mc_mid[0] = mc_bad[0] = float(start)
    for d in range(1, horizon_days + 1):
        if every and d % every == 0:
            vals += add
        vals *= (1.0 + rng.normal(daily_mu, daily_sigma, n_runs))
        np.maximum(vals, 0.0, out=vals)   # a balance can't go below zero
        if d in sset:
            p10, p50, p90 = np.percentile(vals, [10, 50, 90])
            mc_bad[d], mc_mid[d], mc_good[d] = float(p10), float(p50), float(p90)

    r = lambda m: [round(m[d], 2) for d in sample_days]
    return {
        'days': sample_days,
        'contributed': r(contributed),
        'band': {'good': r(band_good), 'mid': r(band_mid), 'bad': r(band_bad)},
        'mc': {'good': r(mc_good), 'mid': r(mc_mid), 'bad': r(mc_bad)},
        'summary': {
            'contributed': round(contributed[horizon_days], 2),
            'band': {'bad': round(band_bad[horizon_days], 2), 'mid': round(band_mid[horizon_days], 2),
                     'good': round(band_good[horizon_days], 2)},
            'mc': {'bad': round(mc_bad[horizon_days], 2), 'mid': round(mc_mid[horizon_days], 2),
                   'good': round(mc_good[horizon_days], 2)},
        },
    }


def _summary(contributed: float, value: float) -> dict:
    return {'contributed': round(contributed, 2), 'value': round(value, 2),
            'gain': round(value - contributed, 2),
            'gain_pct': round((value / contributed - 1) * 100, 2) if contributed else 0.0}
