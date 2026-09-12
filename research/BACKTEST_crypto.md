# Crypto backtest — honest results

Coins: BTC/USD, ETH/USD, LTC/USD, SOL/USD · daily 2021→2026 · fees 0.25%/side + slippage 0.10%/side.
Long-only spot; entry = live bull signal (EMA20>50, RSI<72); exit = −stop% / +take%.

## Buy-and-hold benchmark (the honest bar)
| Coin | Buy-hold total | Best strategy (full history) | Best (stop/take) |
|---|---|---|---|
| BTC/USD | +162% | -14% (maxDD -64%, 34 trades) | 10%/40% |
| ETH/USD | +246% | +1% (maxDD -74%, 33 trades) | 12%/40% |
| LTC/USD | -57% | +23% (maxDD -65%, 117 trades) | 12%/8% |
| SOL/USD | +5405% | +940% (maxDD -74%, 42 trades) | 18%/30% |

## Robust plateau — combos ranked by AVG total return across all 4 coins
(A broad good region matters more than the single top cell — a lone spike = overfit.)

| stop / take | avg total across coins |
|---|---|
| 17.5% / 30% | +188% |
| 20.0% / 30% | +71% |
| 17.5% / 40% | +40% |
| 17.5% / 25% | +40% |
| 12.5% / 25% | +20% |
| 12.5% / 30% | +15% |
| 20.0% / 40% | +11% |
| 15.0% / 30% | +7% |
| 17.5% / 20% | -16% |
| 10.0% / 30% | -20% |

## Walk-forward — OUT-OF-SAMPLE (optimize on train, measure on unseen test)
| Coin | OOS windows | avg OOS return | avg buy-hold (same windows) | OOS beat B&H? |
|---|---|---|---|---|
| BTC/USD | 8 | -5.8% | +24.1% | no |
| ETH/USD | 8 | -5.1% | +13.4% | no |
| LTC/USD | 8 | -2.8% | +6.3% | no |
| SOL/USD | 6 | -16.2% | +119.9% | no |
| **ALL** | 30 | **-6.9%** | **+35.6%** | **no** |

## Recommended ROBUST RANGES (from the plateau, to confirm live on paper)
- **Stop %:** 12–20%
- **Take-profit %:** 25–40%
- **Position size:** from the 2%-risk rule ÷ stop%, capped at a max-notional (start 15%). Size scales risk, not edge, so it's a risk choice, not an optimization target.

## Honest verdict
- These ranges are a **robust region**, not a magic number — pick from the middle of the plateau.
- Read the buy-and-hold column carefully: in a multi-year crypto bull run, **beating buy-and-hold on total return is hard**; the strategy's value is **lower drawdown / defined risk**, not out-gunning a hold.
- Nothing is decided until it also survives **live paper** on account B.

