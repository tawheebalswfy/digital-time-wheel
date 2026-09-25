# V6 H4 Results

| Concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TREND_CONTINUATION | 1802 | 0.624 | 890 | -0.146 | 0.461 | 0.994 |
| PULLBACK_CONTINUATION | 277 | -1.768 | 158 | 2.281 | 0.582 | 1.331 |
| BREAKOUT | 271 | 0.738 | 132 | -1.394 | 0.409 | 0.786 |
| MEAN_REVERSION | 19 | -2.031 | 18 | -1.639 | 0.444 | 0.674 |
| VOLATILITY_EXPANSION | 0 | — | 0 | — | — | — |

Leading raw validation concept: `PULLBACK_CONTINUATION`; frozen: `None`.

## BUY / SELL

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| BUY | 63 | 2.947 | 0.619 | 1.348 |
| SELL | 95 | 1.839 | 0.558 | 1.319 |

## Trend regime

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| strong_trend | 158 | 2.281 | 0.582 | 1.331 |

## Volatility regime

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| high_vol | 21 | 7.910 | 0.619 | 1.922 |
| low_vol | 8 | 1.099 | 0.625 | 1.256 |
| normal_vol | 129 | 1.438 | 0.574 | 1.250 |

