"""
config.py — Single source of settings for the Alpaca options agent.
Credentials come from a .env file (never hardcoded). See .env.example.
"""
from __future__ import annotations
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
except Exception:
    pass   # dotenv optional; env vars still work

# ── MODE ──────────────────────────────────────────────────────
# DRY_RUN    : compute signals + intended option trades, print them, place NOTHING.
#              Runs with zero setup (no Alpaca account needed). Use this to build/test.
# LIVE_PAPER : place real orders on your Alpaca PAPER account ($100k competition account).
#              NEVER a real-money account — this agent is paper-only by design.
MODE = os.getenv('AGENT_MODE', 'DRY_RUN').upper()

# ── ALPACA (paper) ────────────────────────────────────────────
ALPACA_API_KEY    = os.getenv('ALPACA_API_KEY', '')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
ALPACA_PAPER_URL  = 'https://paper-api.alpaca.markets'

# ── UNIVERSE — liquid, optionable US underlyings ──────────────
UNIVERSE = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'TSLA', 'GOOGL']

# ── ACCOUNT ───────────────────────────────────────────────────
ACCOUNT_START = 100_000.0   # competition starting balance

# ── RISK GATES (judges explicitly want these) ────────────────
MAX_RISK_PER_TRADE_PCT = 0.02    # never risk >2% of equity on one option trade
MAX_CONCURRENT         = 6       # at most 6 open positions at once (options + crypto combined)
DAILY_LOSS_LIMIT_PCT   = 0.05    # stop opening new trades if down >5% on the day
DEFINED_RISK_ONLY      = True    # only BUY options (long calls/puts) — never sell naked
MIN_DTE                = 14      # days-to-expiry floor (avoid gamma/theta cliff)
MAX_DTE                = 60      # days-to-expiry ceiling
TAKE_PROFIT_PCT        = 0.50    # close a winning option at +50% of premium
STOP_LOSS_PCT          = 0.50    # close a losing option at -50% of premium

# ── CRYPTO (v2 — spot, long-only) ─────────────────────────────
# Numbers from the WS1 backtest robust range (stop 12–20% / TP 25–40%); mid-plateau.
# Broker holds the stop (Alpaca crypto supports a standalone stop order, not a bracket).
CRYPTO_UNIVERSE          = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'LTC/USD']
CRYPTO_STOP_PCT          = 0.15    # broker stop distance below entry
CRYPTO_TP_PCT            = 0.30    # take-profit distance above entry (agent-managed — no OCO on crypto)
CRYPTO_MAX_NOTIONAL_PCT  = 0.15    # cap one coin's notional vs equity
CRYPTO_STOP_LIMIT_BUFFER = 0.02    # stop_limit's limit sits this far below the stop (crypto = stop_limit, not stop)

# ── SIGNAL PARAMS ─────────────────────────────────────────────
EMA_FAST      = 20
EMA_SLOW      = 50
RSI_PERIOD    = 14
RSI_BULL_MAX  = 72     # don't chase overbought
RSI_BEAR_MIN  = 28     # don't chase oversold
MIN_CONFIDENCE = 0.55  # skip weak signals

# ── FILES ─────────────────────────────────────────────────────
LOG_DIR   = Path(__file__).parent / 'logs'
TRADE_LOG = LOG_DIR / 'trades.jsonl'
