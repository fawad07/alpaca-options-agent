"""
test_connection.py — confirm your Alpaca PAPER account is wired up correctly.

Run this AFTER you've created the submission paper account and pasted its keys
into .env:
    pip3 install -r requirements.txt
    python3 test_connection.py

It only READS your account (equity, options level). It places no trades.
"""
from __future__ import annotations
import config as C


def main():
    # 1) keys present?
    if not C.ALPACA_API_KEY or C.ALPACA_API_KEY.strip().lower().startswith('your_'):
        print("❌ No API key found.")
        print("   Copy .env.example to .env and paste your PAPER keys, then re-run.")
        return

    # 2) SDK installed?
    try:
        from alpaca.trading.client import TradingClient
    except ImportError:
        print("❌ alpaca-py isn't installed.")
        print("   Run:  pip3 install -r requirements.txt")
        return

    # 3) connect (paper) and read the account
    try:
        client = TradingClient(C.ALPACA_API_KEY, C.ALPACA_SECRET_KEY, paper=True)
        a = client.get_account()
    except Exception as e:
        print(f"❌ Could not connect: {e}")
        print("   Check that these are PAPER keys for the correct (submission) account.")
        return

    print("✅ Connected to your Alpaca PAPER account\n")
    print(f"   Account #      : {a.account_number}")
    print(f"   Status         : {a.status}")
    print(f"   Equity         : ${float(a.equity):,.2f}")
    print(f"   Buying power    : ${float(a.buying_power):,.2f}")
    lvl = getattr(a, 'options_trading_level', None)
    print(f"   Options level  : {lvl}   (need >= 1 to trade options)")

    # 4) friendly checks for the hackathon rules
    print()
    if abs(float(a.equity) - 100_000) > 1:
        print("   ⚠️  Equity is not ~$100,000 — set this account's balance to $100k "
              "(competition requirement).")
    if not lvl or int(lvl) < 1:
        print("   ⚠️  Options not enabled — turn on options trading for this paper "
              "account in the Alpaca dashboard (needed for this hackathon).")
    print(f"   👉 This is the Account # you submit on lablab.ai:  {a.account_number}")


if __name__ == '__main__':
    main()
