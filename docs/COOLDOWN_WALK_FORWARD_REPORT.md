# Cooldown Walk-Forward Report

This report evaluates only execution-risk filters around the existing strategy. Auto trading remained disabled and no MT5 order was sent. The forensic week was excluded.

## Data status

- Genuine MT5 XAUUSD data: 2026-08-11 through 2026-09-10 UTC, causally resampled to M1/M5/M15/M30/H1.
- BTCUSD and EURUSD history for non-overlapping windows was unavailable from the saved database and direct read-only MT5 history request; no synthetic data was substituted.
- H4/D1 are not included because the available sample is insufficient for a reliable separate holdout.

## Aggregate candidate metrics

| Window | Variant | Trades | Wins | Losses | Win rate | Gross profit | Gross loss | Net P/L | PF | Expectancy | Avg win | Avg loss | Max DD | Max loss | Max exposure | Blocked |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| discovery | baseline | 2981 | 2138 | 843 | 71.7% | 1672.40 | -3117.10 | -1444.70 | 0.537 | -0.485 | 0.782 | -3.698 | 1445.25 | -43.00 | 5 | 0 |
| discovery | cooldown_60s | 2596 | 1820 | 776 | 70.1% | 1205.22 | -2439.51 | -1234.28 | 0.494 | -0.475 | 0.662 | -3.144 | 1234.83 | -43.00 | 3 | 385 |
| discovery | cooldown_120s | 2454 | 1699 | 755 | 69.2% | 1048.62 | -2265.14 | -1216.52 | 0.463 | -0.496 | 0.617 | -3.000 | 1217.07 | -43.00 | 3 | 527 |
| discovery | cooldown_180s | 2098 | 1452 | 646 | 69.2% | 902.72 | -1986.87 | -1084.15 | 0.454 | -0.517 | 0.622 | -3.076 | 1084.70 | -43.00 | 3 | 883 |
| discovery | cooldown_300s | 1696 | 1187 | 509 | 70.0% | 749.51 | -1577.41 | -827.89 | 0.475 | -0.488 | 0.631 | -3.099 | 828.44 | -43.00 | 3 | 1285 |
| discovery | cap_1 | 2454 | 1790 | 664 | 72.9% | 1292.46 | -2301.11 | -1008.65 | 0.562 | -0.411 | 0.722 | -3.466 | 1009.20 | -43.00 | 1 | 527 |
| discovery | cap_2 | 2883 | 2080 | 803 | 72.1% | 1612.99 | -2991.22 | -1378.23 | 0.539 | -0.478 | 0.775 | -3.725 | 1378.78 | -43.00 | 2 | 98 |
| discovery | cooldown_60s_cap_1 | 2326 | 1652 | 674 | 71.0% | 1059.03 | -2091.05 | -1032.02 | 0.506 | -0.444 | 0.641 | -3.102 | 1032.57 | -43.00 | 1 | 655 |
| discovery | cooldown_120s_cap_1 | 2281 | 1599 | 682 | 70.1% | 966.17 | -2033.50 | -1067.33 | 0.475 | -0.468 | 0.604 | -2.982 | 1067.88 | -43.00 | 1 | 700 |
| discovery | cooldown_300s_cap_1 | 1600 | 1133 | 467 | 70.8% | 713.11 | -1499.42 | -786.31 | 0.476 | -0.491 | 0.629 | -3.211 | 786.86 | -43.00 | 1 | 1381 |
| validation | baseline | 1123 | 783 | 340 | 69.7% | 622.50 | -1237.47 | -614.97 | 0.503 | -0.548 | 0.795 | -3.640 | 638.55 | -23.00 | 5 | 0 |
| validation | cooldown_60s | 983 | 674 | 309 | 68.6% | 463.70 | -976.22 | -512.52 | 0.475 | -0.521 | 0.688 | -3.159 | 525.02 | -23.00 | 3 | 140 |
| validation | cooldown_120s | 936 | 638 | 298 | 68.2% | 416.63 | -904.66 | -488.03 | 0.461 | -0.521 | 0.653 | -3.036 | 500.29 | -15.31 | 3 | 187 |
| validation | cooldown_180s | 796 | 544 | 252 | 68.3% | 360.70 | -756.67 | -395.96 | 0.477 | -0.497 | 0.663 | -3.003 | 407.44 | -15.31 | 3 | 327 |
| validation | cooldown_300s | 643 | 437 | 206 | 68.0% | 288.35 | -635.82 | -347.48 | 0.454 | -0.540 | 0.660 | -3.087 | 359.14 | -15.31 | 3 | 480 |
| validation | cap_1 | 918 | 654 | 264 | 71.2% | 494.67 | -943.48 | -448.80 | 0.524 | -0.489 | 0.756 | -3.574 | 460.55 | -23.00 | 1 | 205 |
| validation | cap_2 | 1078 | 756 | 322 | 70.1% | 602.75 | -1159.20 | -556.45 | 0.520 | -0.516 | 0.797 | -3.600 | 573.06 | -23.00 | 2 | 45 |
| validation | cooldown_60s_cap_1 | 854 | 600 | 254 | 70.3% | 410.02 | -844.02 | -434.00 | 0.486 | -0.508 | 0.683 | -3.323 | 441.65 | -23.00 | 1 | 269 |
| validation | cooldown_120s_cap_1 | 841 | 582 | 259 | 69.2% | 386.95 | -816.51 | -429.57 | 0.474 | -0.511 | 0.665 | -3.153 | 437.21 | -15.31 | 1 | 282 |
| validation | cooldown_300s_cap_1 | 605 | 416 | 189 | 68.8% | 280.45 | -613.14 | -332.69 | 0.457 | -0.550 | 0.674 | -3.244 | 339.74 | -15.31 | 1 | 518 |
| holdout | baseline | 804 | 538 | 266 | 66.9% | 415.82 | -846.21 | -430.39 | 0.491 | -0.535 | 0.773 | -3.181 | 439.56 | -29.18 | 4 | 0 |
| holdout | cooldown_60s | 694 | 449 | 245 | 64.7% | 305.48 | -630.40 | -324.92 | 0.485 | -0.468 | 0.680 | -2.573 | 332.89 | -29.18 | 3 | 110 |
| holdout | cooldown_120s | 665 | 428 | 237 | 64.4% | 277.52 | -602.15 | -324.63 | 0.461 | -0.488 | 0.648 | -2.541 | 332.60 | -29.18 | 2 | 139 |
| holdout | cooldown_180s | 577 | 376 | 201 | 65.2% | 257.90 | -516.13 | -258.23 | 0.500 | -0.448 | 0.686 | -2.568 | 265.30 | -29.18 | 3 | 227 |
| holdout | cooldown_300s | 464 | 304 | 160 | 65.5% | 206.29 | -429.26 | -222.98 | 0.481 | -0.481 | 0.679 | -2.683 | 228.86 | -29.18 | 2 | 340 |
| holdout | cap_1 | 660 | 458 | 202 | 69.4% | 344.40 | -625.57 | -281.18 | 0.551 | -0.426 | 0.752 | -3.097 | 289.14 | -29.18 | 1 | 144 |
| holdout | cap_2 | 775 | 527 | 248 | 68.0% | 410.09 | -770.45 | -360.36 | 0.532 | -0.465 | 0.778 | -3.107 | 369.53 | -29.18 | 2 | 29 |
| holdout | cooldown_60s_cap_1 | 617 | 411 | 206 | 66.6% | 275.22 | -548.87 | -273.65 | 0.501 | -0.444 | 0.670 | -2.664 | 281.61 | -29.18 | 1 | 187 |
| holdout | cooldown_120s_cap_1 | 620 | 402 | 218 | 64.8% | 260.20 | -548.75 | -288.55 | 0.474 | -0.465 | 0.647 | -2.517 | 296.51 | -29.18 | 1 | 184 |
| holdout | cooldown_300s_cap_1 | 445 | 294 | 151 | 66.1% | 203.16 | -428.14 | -224.98 | 0.475 | -0.506 | 0.691 | -2.835 | 230.87 | -29.18 | 1 | 359 |

## XAUUSD BUY / SELL attribution

| Window | Variant | BUY trades | BUY net | BUY PF | BUY expectancy | SELL trades | SELL net | SELL PF | SELL expectancy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | baseline | 583 | -307.27 | 0.502 | -0.527 | 540 | -307.70 | 0.504 | -0.570 |
| validation | cap_1 | 456 | -220.96 | 0.523 | -0.485 | 462 | -227.84 | 0.525 | -0.493 |
| validation | cooldown_60s | 517 | -251.11 | 0.484 | -0.486 | 466 | -261.41 | 0.466 | -0.561 |
| validation | cooldown_300s | 324 | -187.46 | 0.414 | -0.579 | 319 | -160.01 | 0.493 | -0.502 |
| validation | cooldown_60s_cap_1 | 432 | -195.37 | 0.516 | -0.452 | 422 | -238.63 | 0.458 | -0.565 |
| holdout | baseline | 396 | -297.30 | 0.395 | -0.751 | 408 | -133.08 | 0.625 | -0.326 |
| holdout | cap_1 | 346 | -197.90 | 0.465 | -0.572 | 314 | -83.28 | 0.675 | -0.265 |
| holdout | cooldown_60s | 350 | -222.21 | 0.402 | -0.635 | 344 | -102.71 | 0.603 | -0.299 |
| holdout | cooldown_300s | 230 | -159.37 | 0.375 | -0.693 | 234 | -63.61 | 0.635 | -0.272 |
| holdout | cooldown_60s_cap_1 | 320 | -189.77 | 0.419 | -0.593 | 297 | -83.87 | 0.623 | -0.282 |

## Holdout by timeframe

| Variant | M1 trades/net/PF | M5 trades/net/PF | M15 trades/net/PF | M30 trades/net/PF | H1 trades/net/PF |
|---|---|---|---|---|---|
| baseline | 593 / -318.67 / 0.340 | 131 / -87.09 / 0.532 | 39 / -20.71 / 0.721 | 25 / -26.74 / 0.637 | 16 / 22.82 / 1.782 |
| cooldown_60s | 587 / -314.68 / 0.341 | 64 / -53.21 / 0.469 | 21 / 6.81 / 1.293 | 6 / 13.33 / — | 16 / 22.82 / 1.782 |
| cooldown_120s | 582 / -313.27 / 0.342 | 49 / -36.40 / 0.506 | 15 / -1.61 / 0.931 | 5 / 10.93 / — | 14 / 15.71 / 1.539 |
| cooldown_180s | 494 / -259.62 / 0.351 | 47 / -25.98 / 0.592 | 17 / 1.37 / 1.059 | 5 / 10.93 / — | 14 / 15.06 / 1.516 |
| cooldown_300s | 399 / -226.98 / 0.331 | 38 / -20.82 / 0.589 | 10 / 4.26 / 1.418 | 4 / 8.07 / — | 13 / 12.50 / 1.429 |
| cap_1 | 510 / -265.21 / 0.364 | 90 / -22.79 / 0.765 | 29 / -8.86 / 0.815 | 15 / -7.14 / 0.794 | 16 / 22.82 / 1.782 |
| cap_2 | 577 / -306.26 / 0.349 | 121 / -66.67 / 0.589 | 39 / -20.71 / 0.721 | 22 / 10.46 / 1.301 | 16 / 22.82 / 1.782 |
| cooldown_60s_cap_1 | 530 / -272.56 / 0.362 | 51 / -30.50 / 0.560 | 17 / 0.32 / 1.014 | 3 / 6.26 / — | 16 / 22.82 / 1.782 |
| cooldown_120s_cap_1 | 548 / -289.63 / 0.349 | 41 / -19.13 / 0.628 | 13 / -5.20 / 0.777 | 3 / 6.26 / — | 15 / 19.15 / 1.656 |
| cooldown_300s_cap_1 | 379 / -218.05 / 0.329 | 37 / -22.10 / 0.564 | 11 / -8.84 / 0.620 | 4 / 8.07 / — | 14 / 15.94 / 1.546 |

## Holding time

Holdout duration buckets for the frozen validation candidate (`cap_1`). No time-based exit was added.

| Bucket | Trades | Win rate | Net P/L | PF | Expectancy |
|---|---:|---:|---:|---:|---:|
| <1m | 384 | 82.0% | 107.93 | 1.727 | 0.281 |
| 1-5m | 194 | 54.6% | -193.86 | 0.220 | -0.999 |
| 5-15m | 62 | 40.3% | -125.15 | 0.131 | -2.019 |
| 15-60m | 18 | 61.1% | -42.82 | 0.226 | -2.379 |
| >60m | 2 | 50.0% | -27.27 | 0.065 | -13.633 |

## Walk-forward decision

The validation freeze is `cap_1` because it had the strongest available XAUUSD validation PF and expectancy among the fixed candidates. On the XAUUSD holdout it improved PF from 0.491 to 0.551, expectancy from -0.535 to -0.426, and max drawdown from 439.56 to 289.14. The result remains negative and is based on one symbol, so it does not satisfy the multi-symbol support rule.

**Conclusion:** improvement replicated on the available XAUUSD holdout, but evidence is insufficient to promote a production default. Production defaults remain unchanged.

## Required next step

Acquire non-overlapping genuine MT5 history for BTCUSD and EURUSD, rerun the frozen candidate set, and forward-test `cap_1` as an optional DEMO setting only if the multi-symbol validation and holdout criteria pass.
