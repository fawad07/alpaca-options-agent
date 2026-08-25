"""
data.py — free daily price history for the UNDERLYINGS (stocks/ETFs).
Reused from the crypto-companion / ai-trading-pipeline projects (Yahoo chart API,
no key). The agent uses this to compute its directional signal; Alpaca is only
needed for live option quotes + order execution.
"""
from __future__ import annotations
import requests
import pandas as pd


def fetch_daily(symbol: str, rng: str = '1y') -> pd.DataFrame:
    """Daily OHLC for a stock/ETF from Yahoo. Returns empty DataFrame on failure."""
    try:
        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={'interval': '1d', 'range': rng},
            headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame()
        res = r.json()['chart']['result'][0]
        ts = res['timestamp']
        q = res['indicators']['quote'][0]
        df = pd.DataFrame({
            'time': pd.to_datetime(ts, unit='s'),
            'open': q['open'], 'high': q['high'], 'low': q['low'],
            'close': q['close'], 'volume': q['volume'],
        }).dropna(subset=['close']).set_index('time').sort_index()
        return df
    except Exception:
        return pd.DataFrame()
