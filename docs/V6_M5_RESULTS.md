# V6 M5 Results

| Concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TREND_CONTINUATION | 27465 | 0.136 | 9464 | -0.123 | 0.475 | 1.049 |
| PULLBACK_CONTINUATION | 7727 | -0.037 | 2681 | 0.051 | 0.501 | 0.984 |
| BREAKOUT | 6264 | -0.120 | 1914 | 0.058 | 0.471 | 1.120 |
| MEAN_REVERSION | 263 | -0.207 | 68 | -0.857 | 0.412 | 0.830 |
| VOLATILITY_EXPANSION | 14 | 3.134 | 7 | -1.477 | 0.429 | 1.012 |

Leading raw validation concept: `BREAKOUT`; frozen: `None`.

## BUY / SELL

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| BUY | 913 | -0.231 | 0.455 | 1.024 |
| SELL | 1001 | 0.322 | 0.487 | 1.204 |

## Trend regime

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| strong_trend | 1040 | 0.532 | 0.484 | 1.186 |
| weak_trend | 874 | -0.506 | 0.457 | 1.035 |

## Volatility regime

| Group | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| high_vol | 790 | 0.073 | 0.485 | 1.140 |
| normal_vol | 1124 | 0.048 | 0.462 | 1.101 |

## UTC session analysis

| Session | Signals | 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- |
| Asia | 518 | 0.746 | 0.508 | 1.183 |
| London | 500 | -0.434 | 0.452 | 1.044 |
| New_York | 446 | -0.750 | 0.464 | 1.069 |
| Overlap | 450 | 0.613 | 0.458 | 1.177 |
