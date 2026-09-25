# V3 Entry Candidates

Six coarse, interpretable technical candidates were run independently for every timeframe. Values are raw quote-price units per signal after a next-bar-open hypothetical entry; they are not P/L and are not exit-optimized.

## M15


### Development

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 668 | USABLE_FOR_COMPARISON | -0.568 | 0.476 | 14.638 | 14.886 |
| TC_ADX20 | 555 | USABLE_FOR_COMPARISON | -0.015 | 0.486 | 14.649 | 13.910 |
| TC_ADX25 | 366 | USABLE_FOR_COMPARISON | 1.177 | 0.511 | 15.593 | 13.862 |
| TC_ADX30 | 227 | USABLE_FOR_COMPARISON | 1.602 | 0.485 | 15.753 | 13.915 |
| PULLBACK_RSI_40_60 | 38 | LOW_CONFIDENCE | 0.994 | 0.605 | 15.207 | 11.611 |
| NORMAL_ATR_TREND | 512 | USABLE_FOR_COMPARISON | -0.107 | 0.488 | 14.662 | 13.816 |


### Validation

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 272 | USABLE_FOR_COMPARISON | 3.308 | 0.518 | 19.861 | 12.267 |
| TC_ADX20 | 250 | USABLE_FOR_COMPARISON | 3.946 | 0.536 | 20.297 | 11.888 |
| TC_ADX25 | 205 | USABLE_FOR_COMPARISON | 3.163 | 0.527 | 20.201 | 11.606 |
| TC_ADX30 | 174 | USABLE_FOR_COMPARISON | 2.735 | 0.540 | 19.800 | 10.850 |
| PULLBACK_RSI_40_60 | 12 | INSUFFICIENT_SAMPLE | 4.279 | 0.583 | 15.301 | 12.115 |
| NORMAL_ATR_TREND | 176 | USABLE_FOR_COMPARISON | 4.623 | 0.528 | 20.055 | 11.149 |


### Holdout Retrospective

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 212 | USABLE_FOR_COMPARISON | -2.055 | 0.453 | 13.625 | 15.105 |
| TC_ADX20 | 136 | USABLE_FOR_COMPARISON | -0.674 | 0.522 | 15.469 | 14.974 |
| TC_ADX25 | 69 | LOW_CONFIDENCE | -3.672 | 0.406 | 12.577 | 17.436 |
| TC_ADX30 | 36 | LOW_CONFIDENCE | -4.017 | 0.361 | 11.348 | 15.495 |
| PULLBACK_RSI_40_60 | 14 | INSUFFICIENT_SAMPLE | 4.769 | 0.786 | 24.079 | 9.449 |
| NORMAL_ATR_TREND | 129 | USABLE_FOR_COMPARISON | 0.203 | 0.550 | 15.909 | 14.130 |


## M30


### Development

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 309 | USABLE_FOR_COMPARISON | 0.838 | 0.472 | 21.824 | 19.894 |
| TC_ADX20 | 265 | USABLE_FOR_COMPARISON | 1.510 | 0.494 | 22.538 | 19.208 |
| TC_ADX25 | 189 | USABLE_FOR_COMPARISON | 1.488 | 0.508 | 20.920 | 18.438 |
| TC_ADX30 | 144 | USABLE_FOR_COMPARISON | 0.438 | 0.486 | 18.787 | 19.075 |
| PULLBACK_RSI_40_60 | 10 | INSUFFICIENT_SAMPLE | 4.647 | 0.600 | 24.407 | 18.247 |
| NORMAL_ATR_TREND | 248 | USABLE_FOR_COMPARISON | 1.131 | 0.480 | 21.912 | 19.618 |


### Validation

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 140 | USABLE_FOR_COMPARISON | 3.392 | 0.593 | 29.474 | 16.454 |
| TC_ADX20 | 133 | USABLE_FOR_COMPARISON | 3.541 | 0.586 | 27.950 | 16.594 |
| TC_ADX25 | 125 | USABLE_FOR_COMPARISON | 4.020 | 0.608 | 28.218 | 16.334 |
| TC_ADX30 | 113 | USABLE_FOR_COMPARISON | 4.536 | 0.619 | 28.215 | 15.907 |
| PULLBACK_RSI_40_60 | 4 | INSUFFICIENT_SAMPLE | -8.293 | 0.250 | 10.702 | 21.770 |
| NORMAL_ATR_TREND | 113 | USABLE_FOR_COMPARISON | 2.911 | 0.575 | 26.126 | 16.973 |


### Holdout Retrospective

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 109 | USABLE_FOR_COMPARISON | -2.611 | 0.450 | 18.874 | 23.173 |
| TC_ADX20 | 77 | LOW_CONFIDENCE | -3.595 | 0.390 | 16.165 | 23.569 |
| TC_ADX25 | 40 | LOW_CONFIDENCE | -3.449 | 0.425 | 17.120 | 19.863 |
| TC_ADX30 | 19 | INSUFFICIENT_SAMPLE | -6.479 | 0.368 | 15.471 | 22.543 |
| PULLBACK_RSI_40_60 | 7 | INSUFFICIENT_SAMPLE | 6.336 | 0.714 | 22.016 | 26.404 |
| NORMAL_ATR_TREND | 66 | LOW_CONFIDENCE | -3.686 | 0.394 | 16.279 | 24.728 |


## H1


### Development

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 117 | USABLE_FOR_COMPARISON | 2.719 | 0.556 | 33.351 | 28.517 |
| TC_ADX20 | 97 | LOW_CONFIDENCE | 0.406 | 0.505 | 32.812 | 29.855 |
| TC_ADX25 | 74 | LOW_CONFIDENCE | 5.191 | 0.595 | 36.552 | 28.273 |
| TC_ADX30 | 56 | LOW_CONFIDENCE | 0.516 | 0.518 | 31.162 | 33.257 |
| PULLBACK_RSI_40_60 | 1 | INSUFFICIENT_SAMPLE | -31.360 | 0.000 | 6.230 | 38.080 |
| NORMAL_ATR_TREND | 97 | LOW_CONFIDENCE | 0.406 | 0.505 | 32.812 | 29.855 |


### Validation

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 74 | LOW_CONFIDENCE | 10.644 | 0.649 | 46.352 | 21.963 |
| TC_ADX20 | 74 | LOW_CONFIDENCE | 10.644 | 0.649 | 46.352 | 21.963 |
| TC_ADX25 | 73 | LOW_CONFIDENCE | 10.641 | 0.644 | 45.989 | 22.226 |
| TC_ADX30 | 71 | LOW_CONFIDENCE | 10.676 | 0.634 | 45.561 | 22.446 |
| PULLBACK_RSI_40_60 | 0 | INSUFFICIENT_SAMPLE | — | — | — | — |
| NORMAL_ATR_TREND | 74 | LOW_CONFIDENCE | 10.644 | 0.649 | 46.352 | 21.963 |


### Holdout Retrospective

| Candidate | Signals | Label | 5-bar expectancy | 5-bar accuracy | Mean MFE | Mean MAE |
| --- | --- | --- | --- | --- | --- | --- |
| TC_ADX15 | 49 | LOW_CONFIDENCE | -5.890 | 0.449 | 25.045 | 33.027 |
| TC_ADX20 | 45 | LOW_CONFIDENCE | -6.639 | 0.444 | 24.813 | 33.189 |
| TC_ADX25 | 31 | LOW_CONFIDENCE | -10.411 | 0.387 | 19.927 | 37.728 |
| TC_ADX30 | 25 | INSUFFICIENT_SAMPLE | -6.151 | 0.480 | 22.604 | 34.559 |
| PULLBACK_RSI_40_60 | 7 | INSUFFICIENT_SAMPLE | 2.086 | 0.714 | 39.741 | 13.924 |
| NORMAL_ATR_TREND | 45 | LOW_CONFIDENCE | -6.639 | 0.444 | 24.813 | 33.189 |

