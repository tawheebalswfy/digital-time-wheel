# V3 Time Wheel Attribution

For each timeframe, the development-selected technical candidate was replayed unchanged under three Time Wheel roles: none (base V3), confirmation (Wheel must agree), and veto (only an opposite Wheel value rejects). This is attribution, not an accepted entry rule.

## M15: development-selected `TC_ADX30`


| Wheel role | Window | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- | --- |
| none | development | 227 | USABLE_FOR_COMPARISON | 1.602 | 0.485 |
| none | validation | 174 | USABLE_FOR_COMPARISON | 2.735 | 0.540 |
| none | holdout_retrospective | 36 | LOW_CONFIDENCE | -4.017 | 0.361 |
| confirmation | development | 26 | INSUFFICIENT_SAMPLE | -1.117 | 0.423 |
| confirmation | validation | 27 | INSUFFICIENT_SAMPLE | 5.623 | 0.556 |
| confirmation | holdout_retrospective | 7 | INSUFFICIENT_SAMPLE | -1.387 | 0.429 |
| veto | development | 183 | USABLE_FOR_COMPARISON | 1.635 | 0.481 |
| veto | validation | 153 | USABLE_FOR_COMPARISON | 3.296 | 0.549 |
| veto | holdout_retrospective | 30 | LOW_CONFIDENCE | -3.452 | 0.400 |


## M30: development-selected `TC_ADX20`


| Wheel role | Window | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- | --- |
| none | development | 265 | USABLE_FOR_COMPARISON | 1.510 | 0.494 |
| none | validation | 133 | USABLE_FOR_COMPARISON | 3.541 | 0.586 |
| none | holdout_retrospective | 77 | LOW_CONFIDENCE | -3.595 | 0.390 |
| confirmation | development | 40 | LOW_CONFIDENCE | 3.365 | 0.600 |
| confirmation | validation | 22 | INSUFFICIENT_SAMPLE | 8.348 | 0.682 |
| confirmation | holdout_retrospective | 13 | INSUFFICIENT_SAMPLE | 3.962 | 0.692 |
| veto | development | 226 | USABLE_FOR_COMPARISON | 2.092 | 0.504 |
| veto | validation | 115 | USABLE_FOR_COMPARISON | 4.861 | 0.609 |
| veto | holdout_retrospective | 61 | LOW_CONFIDENCE | -1.628 | 0.459 |


## H1: development-selected `TC_ADX25`


| Wheel role | Window | Signals | Label | 5-bar expectancy | Accuracy |
| --- | --- | --- | --- | --- | --- |
| none | development | 74 | LOW_CONFIDENCE | 5.191 | 0.595 |
| none | validation | 73 | LOW_CONFIDENCE | 10.641 | 0.644 |
| none | holdout_retrospective | 31 | LOW_CONFIDENCE | -10.411 | 0.387 |
| confirmation | development | 11 | INSUFFICIENT_SAMPLE | 4.282 | 0.636 |
| confirmation | validation | 15 | INSUFFICIENT_SAMPLE | 20.650 | 0.800 |
| confirmation | holdout_retrospective | 6 | INSUFFICIENT_SAMPLE | 0.173 | 0.333 |
| veto | development | 63 | LOW_CONFIDENCE | 7.125 | 0.635 |
| veto | validation | 62 | LOW_CONFIDENCE | 13.972 | 0.710 |
| veto | holdout_retrospective | 24 | INSUFFICIENT_SAMPLE | -7.010 | 0.375 |


A role is not treated as beneficial merely because it raises an in-sample average while shrinking the sample. The base technical and veto arms are negative in every final retrospective segment. M30 confirmation is positive (+3.962) in that segment, but has only 13 signals (INSUFFICIENT_SAMPLE) after being only 40 signals in development; it is not stable evidence. The study therefore finds no demonstrated incremental Time Wheel entry value.
