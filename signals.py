"""
signals.py — the "AI logic": turn price history into a directional view.
Reused/adapted from ai-trading-pipeline (EMA/RSI/ATR features + trend logic).

The agent maps this view to an OPTION intent:
    bull  -> buy a CALL   (bet up)
    bear  -> buy a PUT    (bet down)
    neutral -> no trade

We deliberately keep the logic transparent and rule-based so the one-page
write-up can explain exactly why every trade happened (judges want clarity),
and so it can be honestly backtested out-of-sample.
"""
from __future__ import annotations
import pandas as pd
import config as C


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df['close']
    df['EMA_fast'] = c.ewm(span=C.EMA_FAST).mean()
    df['EMA_slow'] = c.ewm(span=C.EMA_SLOW).mean()
    d = c.diff()
    gain = d.clip(lower=0).rolling(C.RSI_PERIOD).mean()
    loss = (-d.clip(upper=0)).rolling(C.RSI_PERIOD).mean()
    df['RSI'] = 100 - 100 / (1 + gain / (loss + 1e-9))
    tr = pd.concat([df['high'] - df['low'],
                    (df['high'] - c.shift()).abs(),
                    (df['low'] - c.shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    return df


def signal(df: pd.DataFrame) -> dict:
    """Return {'direction','confidence','reason'} from the latest bar."""
    if df is None or len(df) < C.EMA_SLOW + 5:
        return {'direction': 'neutral', 'confidence': 0.0, 'reason': 'not enough data'}
    f = add_features(df).iloc[-1]
    ema_fast, ema_slow, rsi = f['EMA_fast'], f['EMA_slow'], f['RSI']
    trend_up = ema_fast > ema_slow
    gap = abs(ema_fast - ema_slow) / ema_slow      # how strong the trend is
    conf = min(1.0, 0.5 + gap * 8)                 # bigger gap -> more confidence

    if trend_up and rsi < C.RSI_BULL_MAX:
        return {'direction': 'bull', 'confidence': round(conf, 2),
                'reason': f'uptrend (EMA{C.EMA_FAST}>EMA{C.EMA_SLOW}), RSI {rsi:.0f} not overbought'}
    if (not trend_up) and rsi > C.RSI_BEAR_MIN:
        return {'direction': 'bear', 'confidence': round(conf, 2),
                'reason': f'downtrend (EMA{C.EMA_FAST}<EMA{C.EMA_SLOW}), RSI {rsi:.0f} not oversold'}
    return {'direction': 'neutral', 'confidence': round(conf, 2),
            'reason': f'no clean setup (RSI {rsi:.0f})'}
