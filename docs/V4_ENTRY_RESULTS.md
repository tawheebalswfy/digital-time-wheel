# V4 Entry Results
## M15

| Candidate | Dev n | Dev 5b exp | Val n | Val 5b exp | Val accuracy | Val MFE | Val MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMA_ADX20 | 24548 | 0.024 | 8279 | 0.346 | 0.496 | 7.113 | 6.521 |
| EMA_ADX25 | 17397 | -0.003 | 6042 | 0.434 | 0.507 | 7.397 | 6.610 |
| STRONG_ADX30 | 11620 | -0.040 | 4188 | 0.088 | 0.490 | 7.492 | 7.021 |
| SLOPE_ADX25 | 16671 | -0.004 | 5771 | 0.348 | 0.503 | 7.323 | 6.633 |
| RSI_MOMENTUM | 23207 | 0.037 | 7889 | 0.321 | 0.495 | 7.100 | 6.544 |
| PULLBACK | 1341 | -0.209 | 390 | 0.857 | 0.508 | 7.379 | 6.055 |
| NORMAL_ATR_TREND | 18038 | -0.026 | 6927 | 0.440 | 0.501 | 7.094 | 6.438 |
| LOW_ATR_TREND | 6338 | -0.013 | 1766 | 0.434 | 0.502 | 5.986 | 5.670 |

Frozen technical candidate: `RSI_MOMENTUM`; leading validation-positive candidate used for attribution: `RSI_MOMENTUM`. Validation-month stability: `8/11` positive 5-bar-expectancy months. Time Wheel comparison (validation):

| Arm | Signals | 5b expectancy | Accuracy | V1-exit PF | V1-exit DD |
| --- | --- | --- | --- | --- | --- |
| technical_only | 7889 | 0.321 | 0.495 | 0.658 | 1868.478 |
| confirmation | 1259 | 0.122 | 0.484 | 0.617 | 639.630 |
| veto | 6540 | 0.297 | 0.493 | 0.660 | 1711.887 |

## M30

| Candidate | Dev n | Dev 5b exp | Val n | Val 5b exp | Val accuracy | Val MFE | Val MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMA_ADX20 | 20888 | 0.037 | 6888 | -0.037 | 0.476 | 4.673 | 4.607 |
| EMA_ADX25 | 14818 | 0.117 | 4801 | 0.052 | 0.482 | 4.808 | 4.660 |
| STRONG_ADX30 | 10007 | 0.055 | 3225 | 0.170 | 0.495 | 4.974 | 4.587 |
| SLOPE_ADX25 | 14091 | 0.137 | 4624 | 0.059 | 0.483 | 4.830 | 4.677 |
| RSI_MOMENTUM | 19803 | 0.058 | 6474 | -0.031 | 0.477 | 4.694 | 4.624 |
| PULLBACK | 1085 | -0.354 | 414 | -0.128 | 0.459 | 4.345 | 4.346 |
| NORMAL_ATR_TREND | 18248 | 0.081 | 5982 | -0.137 | 0.468 | 4.543 | 4.607 |
| LOW_ATR_TREND | 5880 | 0.002 | 2061 | 0.112 | 0.487 | 4.073 | 3.905 |

Frozen technical candidate: `None`; leading validation-positive candidate used for attribution: `SLOPE_ADX25`. Validation-month stability: `10/21` positive 5-bar-expectancy months. Time Wheel comparison (validation):

| Arm | Signals | 5b expectancy | Accuracy | V1-exit PF | V1-exit DD |
| --- | --- | --- | --- | --- | --- |
| technical_only | 4624 | 0.059 | 0.483 | 0.569 | 1182.356 |
| confirmation | 783 | 0.587 | 0.529 | 0.530 | 381.547 |
| veto | 3870 | 0.054 | 0.484 | 0.546 | 1173.186 |

## H1

| Candidate | Dev n | Dev 5b exp | Val n | Val 5b exp | Val accuracy | Val MFE | Val MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMA_ADX20 | 9920 | 0.097 | 3697 | -0.080 | 0.472 | 5.657 | 5.617 |
| EMA_ADX25 | 7504 | -0.012 | 2758 | 0.191 | 0.481 | 5.832 | 5.506 |
| STRONG_ADX30 | 5414 | 0.052 | 1948 | 0.117 | 0.483 | 5.912 | 5.585 |
| SLOPE_ADX25 | 7141 | 0.007 | 2655 | 0.254 | 0.485 | 5.914 | 5.515 |
| RSI_MOMENTUM | 9395 | 0.136 | 3518 | -0.047 | 0.474 | 5.683 | 5.596 |
| PULLBACK | 525 | -0.608 | 179 | -0.725 | 0.430 | 5.139 | 6.018 |
| NORMAL_ATR_TREND | 9049 | 0.136 | 3484 | 0.015 | 0.474 | 5.580 | 5.418 |
| LOW_ATR_TREND | 3025 | -0.041 | 1118 | 0.169 | 0.484 | 5.396 | 5.135 |

Frozen technical candidate: `EMA_ADX25`; leading validation-positive candidate used for attribution: `NORMAL_ATR_TREND`. Validation-month stability: `17/28` positive 5-bar-expectancy months. Time Wheel comparison (validation):

| Arm | Signals | 5b expectancy | Accuracy | V1-exit PF | V1-exit DD |
| --- | --- | --- | --- | --- | --- |
| technical_only | 2758 | 0.191 | 0.481 | 0.560 | 1202.954 |
| confirmation | 469 | 0.394 | 0.501 | 0.487 | 456.152 |
| veto | 2328 | 0.152 | 0.478 | 0.547 | 1146.895 |

