# V7 Regime Entry Results
## M5

| Regime / concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| STRONG_TREND / TREND_CONTINUATION | 16726 | 0.100 | 5869 | 0.405 | 0.490 | 1.144 |
| STRONG_TREND / PULLBACK_CONTINUATION | 1407 | -0.023 | 476 | 0.439 | 0.496 | 1.030 |
| RANGE_LOW_VOL / MEAN_REVERSION | 120 | -1.070 | 28 | -1.445 | 0.393 | 0.569 |
| RANGE_NORMAL_VOL / RANGE_FADE | 313 | 0.606 | 85 | 2.832 | 0.565 | 1.689 |
| HIGH_VOL_EXPANSION / BREAKOUT | 181 | 0.589 | 42 | 0.445 | 0.476 | 0.985 |
| HIGH_VOL_EXPANSION / VOLATILITY_EXPANSION | 181 | 0.589 | 42 | 0.445 | 0.476 | 0.985 |

Leading: `('RANGE_NORMAL_VOL', 'RANGE_FADE')`; frozen: `('STRONG_TREND', 'TREND_CONTINUATION')`.

## M15

| Regime / concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| STRONG_TREND / TREND_CONTINUATION | 16671 | -0.004 | 5771 | 0.348 | 0.503 | 1.104 |
| STRONG_TREND / PULLBACK_CONTINUATION | 1373 | -0.126 | 424 | 0.924 | 0.524 | 1.215 |
| RANGE_LOW_VOL / MEAN_REVERSION | 101 | 0.020 | 42 | -2.296 | 0.429 | 0.729 |
| RANGE_NORMAL_VOL / RANGE_FADE | 322 | -0.186 | 127 | -2.094 | 0.409 | 0.665 |
| HIGH_VOL_EXPANSION / BREAKOUT | 86 | -0.621 | 51 | 3.447 | 0.569 | 1.543 |
| HIGH_VOL_EXPANSION / VOLATILITY_EXPANSION | 86 | -0.621 | 51 | 3.447 | 0.569 | 1.543 |

Leading: `('HIGH_VOL_EXPANSION', 'BREAKOUT')`; frozen: `None`.

## M30

| Regime / concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| STRONG_TREND / TREND_CONTINUATION | 14091 | 0.137 | 4624 | 0.059 | 0.483 | 1.033 |
| STRONG_TREND / PULLBACK_CONTINUATION | 1172 | 0.092 | 351 | -0.370 | 0.453 | 0.870 |
| RANGE_LOW_VOL / MEAN_REVERSION | 99 | -0.195 | 38 | -3.357 | 0.395 | 0.497 |
| RANGE_NORMAL_VOL / RANGE_FADE | 233 | 0.050 | 102 | 0.029 | 0.520 | 0.910 |
| HIGH_VOL_EXPANSION / BREAKOUT | 97 | 0.579 | 37 | -1.009 | 0.459 | 0.773 |
| HIGH_VOL_EXPANSION / VOLATILITY_EXPANSION | 97 | 0.579 | 37 | -1.009 | 0.459 | 0.773 |

Leading: `('STRONG_TREND', 'TREND_CONTINUATION')`; frozen: `None`.

## H1

| Regime / concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| STRONG_TREND / TREND_CONTINUATION | 7141 | 0.007 | 2655 | 0.254 | 0.485 | 1.072 |
| STRONG_TREND / PULLBACK_CONTINUATION | 445 | -0.119 | 191 | -0.054 | 0.476 | 1.039 |
| RANGE_LOW_VOL / MEAN_REVERSION | 40 | -1.573 | 16 | 1.476 | 0.562 | 1.023 |
| RANGE_NORMAL_VOL / RANGE_FADE | 56 | -2.041 | 17 | 2.565 | 0.588 | 1.870 |
| HIGH_VOL_EXPANSION / BREAKOUT | 11 | 0.397 | 0 | — | — | — |
| HIGH_VOL_EXPANSION / VOLATILITY_EXPANSION | 11 | 0.397 | 0 | — | — | — |

Leading: `('STRONG_TREND', 'TREND_CONTINUATION')`; frozen: `None`.

## H4

| Regime / concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| STRONG_TREND / TREND_CONTINUATION | 1919 | 0.268 | 905 | -0.635 | 0.455 | 0.960 |
| STRONG_TREND / PULLBACK_CONTINUATION | 105 | 0.065 | 71 | 1.095 | 0.563 | 1.056 |
| RANGE_LOW_VOL / MEAN_REVERSION | 10 | -4.873 | 7 | -1.291 | 0.571 | 0.555 |
| RANGE_NORMAL_VOL / RANGE_FADE | 12 | -2.813 | 12 | -0.285 | 0.500 | 1.129 |
| HIGH_VOL_EXPANSION / BREAKOUT | 6 | 0.515 | 3 | -4.083 | 0.667 | 0.781 |
| HIGH_VOL_EXPANSION / VOLATILITY_EXPANSION | 6 | 0.515 | 3 | -4.083 | 0.667 | 0.781 |

Leading: `('STRONG_TREND', 'PULLBACK_CONTINUATION')`; frozen: `None`.

## D1

| Regime / concept | Dev n | Dev 5b exp | Val n | Val 5b exp | Accuracy | MFE/MAE |
| --- | --- | --- | --- | --- | --- | --- |
| STRONG_TREND / TREND_CONTINUATION | 1236 | -1.341 | 473 | -0.093 | 0.535 | 1.048 |
| STRONG_TREND / PULLBACK_CONTINUATION | 79 | 4.860 | 37 | 2.243 | 0.486 | 1.160 |
| RANGE_LOW_VOL / MEAN_REVERSION | 9 | -4.158 | 5 | -8.642 | 0.200 | 0.686 |
| RANGE_NORMAL_VOL / RANGE_FADE | 28 | -4.044 | 7 | -3.566 | 0.571 | 0.595 |
| HIGH_VOL_EXPANSION / BREAKOUT | 10 | -3.742 | 3 | -7.843 | 0.333 | 0.577 |
| HIGH_VOL_EXPANSION / VOLATILITY_EXPANSION | 10 | -3.742 | 3 | -7.843 | 0.333 | 0.577 |

Leading: `('STRONG_TREND', 'PULLBACK_CONTINUATION')`; frozen: `None`.

