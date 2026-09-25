# V6 D1 Results

| Concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TREND_CONTINUATION | 1678 | 0.421 | 607 | 0.074 | 0.509 | 1.034 |
| PULLBACK_CONTINUATION | 70 | 0.064 | 30 | 3.442 | 0.600 | 1.358 |
| BREAKOUT | 200 | -1.699 | 64 | -0.088 | 0.516 | 1.111 |
| MEAN_REVERSION | 28 | -3.496 | 7 | -8.921 | 0.143 | 0.534 |
| VOLATILITY_EXPANSION | 0 | — | 0 | — | — | — |

Leading raw validation concept: `TREND_CONTINUATION`; frozen: `None`.

## BUY / SELL

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| BUY | 371 | 1.225 | 0.534 | 1.113 |
| SELL | 236 | -1.735 | 0.470 | 0.884 |

## Trend regime

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| strong_trend | 431 | 0.977 | 0.527 | 1.076 |
| weak_trend | 176 | -2.138 | 0.466 | 0.916 |

## Volatility regime

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| high_vol | 64 | -1.725 | 0.547 | 0.874 |
| low_vol | 36 | 17.139 | 0.639 | 2.658 |
| normal_vol | 507 | -0.911 | 0.495 | 0.995 |

