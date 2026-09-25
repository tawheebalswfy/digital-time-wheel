# V3 Validation Results

## Frozen per-timeframe selections

| TF | Frozen on development | Dev n | Dev exp | Validation n | Validation exp | Final n | Final exp | Final accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M15 | TC_ADX30 | 227 | 1.602 | 174 | 2.735 | 36 | -4.017 | 0.361 |
| M30 | TC_ADX20 | 265 | 1.510 | 133 | 3.541 | 77 | -3.595 | 0.390 |
| H1 | TC_ADX25 | 74 | 5.191 | 73 | 10.641 | 31 | -10.411 | 0.387 |


All three development selections are positive in development and validation but negative in the final chronological segment. This rejects them as stable entry candidates and blocks exit research.

## M15 validation diagnostics (TC_ADX30)


### BUY / SELL

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| BUY | 70 | LOW_CONFIDENCE | 2.483 | 0.514 |
| SELL | 104 | USABLE_FOR_COMPARISON | 2.905 | 0.558 |


### Trend regime

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| strong | 174 | USABLE_FOR_COMPARISON | 2.735 | 0.540 |


### Volatility regime

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| high | 93 | LOW_CONFIDENCE | 2.650 | 0.505 |
| low | 44 | LOW_CONFIDENCE | 5.832 | 0.682 |
| normal | 37 | LOW_CONFIDENCE | -0.734 | 0.459 |


### Final retrospective BUY / SELL

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| BUY | 11 | INSUFFICIENT_SAMPLE | -9.003 | 0.091 |
| SELL | 25 | INSUFFICIENT_SAMPLE | -1.824 | 0.480 |


### Validation robustness

| Adjustment | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| all | 174 | 2.735 | 0.540 |
| without_best_trade | 173 | 2.491 | 0.538 |
| without_worst_trade | 173 | 2.961 | 0.543 |
| without_best_day | 133 | 2.179 | 0.534 |
| without_worst_day | 167 | 2.853 | 0.545 |


### Final retrospective-segment robustness

| Adjustment | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| all | 36 | -4.017 | 0.361 |
| without_best_trade | 35 | -4.572 | 0.343 |
| without_worst_trade | 35 | -3.292 | 0.371 |
| without_best_day | 15 | -12.499 | 0.067 |
| without_worst_day | 21 | 2.040 | 0.571 |


### Validation monthly results

| Month | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| 2026-08 | 42 | 3.116 | 0.500 |
| 2026-09 | 132 | 2.614 | 0.553 |


## M30 validation diagnostics (TC_ADX20)


### BUY / SELL

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| BUY | 59 | LOW_CONFIDENCE | 6.298 | 0.644 |
| SELL | 74 | LOW_CONFIDENCE | 1.342 | 0.541 |


### Trend regime

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| strong | 125 | USABLE_FOR_COMPARISON | 4.020 | 0.608 |
| weak | 8 | INSUFFICIENT_SAMPLE | -3.941 | 0.250 |


### Volatility regime

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| high | 41 | LOW_CONFIDENCE | 0.349 | 0.537 |
| low | 45 | LOW_CONFIDENCE | 7.146 | 0.667 |
| normal | 47 | LOW_CONFIDENCE | 2.873 | 0.553 |


### Final retrospective BUY / SELL

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| BUY | 20 | INSUFFICIENT_SAMPLE | -8.583 | 0.250 |
| SELL | 57 | LOW_CONFIDENCE | -1.845 | 0.439 |


### Validation robustness

| Adjustment | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| all | 133 | 3.541 | 0.586 |
| without_best_trade | 132 | 3.167 | 0.583 |
| without_worst_trade | 132 | 3.940 | 0.591 |
| without_best_day | 97 | 1.488 | 0.557 |
| without_worst_day | 108 | 5.146 | 0.639 |


### Final retrospective-segment robustness

| Adjustment | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| all | 77 | -3.595 | 0.390 |
| without_best_trade | 76 | -3.986 | 0.382 |
| without_worst_trade | 76 | -3.146 | 0.395 |
| without_best_day | 74 | -4.554 | 0.365 |
| without_worst_day | 54 | -2.341 | 0.426 |


### Validation monthly results

| Month | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| 2026-08 | 35 | -0.447 | 0.486 |
| 2026-09 | 98 | 4.965 | 0.622 |


## H1 validation diagnostics (TC_ADX25)


### BUY / SELL

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| BUY | 21 | INSUFFICIENT_SAMPLE | 21.370 | 0.762 |
| SELL | 52 | LOW_CONFIDENCE | 6.308 | 0.596 |


### Trend regime

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| strong | 73 | LOW_CONFIDENCE | 10.641 | 0.644 |


### Volatility regime

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| high | 32 | LOW_CONFIDENCE | 4.640 | 0.594 |
| low | 20 | INSUFFICIENT_SAMPLE | 33.881 | 0.850 |
| normal | 21 | INSUFFICIENT_SAMPLE | -2.348 | 0.524 |


### Final retrospective BUY / SELL

| Group | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- |
| BUY | 4 | INSUFFICIENT_SAMPLE | -49.705 | 0.000 |
| SELL | 27 | INSUFFICIENT_SAMPLE | -4.589 | 0.444 |


### Validation robustness

| Adjustment | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| all | 73 | 10.641 | 0.644 |
| without_best_trade | 72 | 9.872 | 0.639 |
| without_worst_trade | 72 | 11.795 | 0.653 |
| without_best_day | 53 | 2.798 | 0.509 |
| without_worst_day | 58 | 16.115 | 0.707 |


### Final retrospective-segment robustness

| Adjustment | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| all | 31 | -10.411 | 0.387 |
| without_best_trade | 30 | -11.615 | 0.367 |
| without_worst_trade | 30 | -7.769 | 0.400 |
| without_best_day | 30 | -11.606 | 0.367 |
| without_worst_day | 20 | -7.419 | 0.400 |


### Validation monthly results

| Month | Signals | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- |
| 2026-08 | 21 | -2.228 | 0.429 |
| 2026-09 | 52 | 15.838 | 0.731 |


All 1/2/3/5/10-bar, MFE/MAE results, daily records, and final-segment monthly results are retained in `docs/V3_ENTRY_RESEARCH_RESULTS.json`. The retained history is under 30 calendar days, so monthly summaries are descriptive only.
