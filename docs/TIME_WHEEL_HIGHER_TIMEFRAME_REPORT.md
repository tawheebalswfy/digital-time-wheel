# Higher-timeframe Time Wheel attribution — TW-HIGHER-TF-1

**Final conclusion:** the available evidence does not show that Time Wheel value becomes stronger above M1. M15 shows a larger per-trade wheel-exit uplift than M1, but all M15 isolated variants remain negative with profit factor below one. H1 has too few trades to interpret. H4 cannot meet the frozen causal split. No production default or parameter was changed.

The [frozen protocol](TIME_WHEEL_HIGHER_TIMEFRAME_PROTOCOL.md) preserves the fully isolated T/W entry and exit rules from TW-FULL-EXIT-1. A=T/T, B=W/W, C=T/W, D=W/T, and E=current production logic. All use the retained genuine MT5 data, 0.40 cost, next-bar-open execution, stop-first ambiguity, adverse gap fill, one position, 30-bar maximum hold, 78-bar warmup, and fixed 31-bar purges. Final conclusions below use only the chronological final-test segments.

## M15 final test

Dataset: 2,013 genuine MT5 candles. Test `[1610,2013)`, after fixed chronological train/validation windows and purges. Six represented UTC dates.

| Metric | A: T/T | B: W/W | C: T/W | D: W/T | E: production |
|---|---:|---:|---:|---:|---:|
| Trades | 69 | 103 | 81 | 80 | 59 |
| Win rate | 30.43% | 0.97% | 6.17% | 33.75% | 84.75% |
| Net expectancy | -0.8912 | -0.8446 | -0.7680 | -1.5398 | -0.4541 |
| Profit factor | 0.5170 | 0.0026 | 0.0231 | 0.3143 | 0.7738 |
| Max drawdown | 61.4915 | 86.9900 | 62.2100 | 123.1871 | 43.9226 |
| Average win | 3.1348 | 0.2300 | 0.2940 | 2.0912 | 1.8331 |
| Average loss | -2.6526 | -0.8551 | -0.8379 | -3.3896 | -13.1606 |
| Mean MAE | 4.6517 | 4.4141 | 4.3660 | 5.2846 | 6.7112 |
| Mean MFE | 4.5555 | 4.1380 | 4.3336 | 4.1976 | 5.4236 |

Wheel-entry attribution is adverse: D−A expectancy is **-0.6487** with technical exits, and B−C is **-0.0765** with wheel exits. Wheel-exit attribution is positive per trade: C−A is **+0.1232**, and B−D is **+0.6953**. That uplift does not establish value: the wheel-exit variants lose more aggregate P&L and have equal or greater drawdown. The production reference is also negative, though less negative than every isolated arm.

## H1 final test

Dataset: 503 genuine MT5 candles. Test `[402,503)`, after fixed chronological train/validation windows and purges. Six represented UTC dates, but only 15–29 trades by arm.

| Metric | A: T/T | B: W/W | C: T/W | D: W/T | E: production |
|---|---:|---:|---:|---:|---:|
| Trades | 15 | 29 | 16 | 16 | 15 |
| Win rate | 33.33% | 3.45% | 0.00% | 31.25% | 86.67% |
| Net expectancy | -1.4775 | -0.8666 | -0.8413 | -1.4908 | -0.5627 |
| Profit factor | 0.5932 | 0.0004 | 0.0000 | 0.5451 | 0.8450 |
| Max drawdown | 24.3253 | 25.1300 | 13.4600 | 45.0451 | 30.6163 |
| Average win | 6.4636 | 0.0100 | N/A | 5.7173 | 3.5400 |
| Average loss | -5.4481 | -0.8979 | -0.8413 | -4.7673 | -27.2299 |
| Mean MAE | 10.3560 | 10.7417 | 9.0650 | 14.4263 | 10.7873 |
| Mean MFE | 8.2287 | 9.5021 | 7.0831 | 12.7681 | 13.0207 |

The raw wheel-exit expectancy deltas are positive (+0.6363 and +0.6243), while wheel-entry deltas are negative (-0.0133 and -0.0253). With only 15–29 trades and six dates, this is **insufficient evidence**, not a meaningful H1 finding. Every arm remains negative.

## H4

No valid run. The retained genuine H4 dataset has 131 candles. The existing 78-bar causal warmup equals the 60% boundary (index 78); applying the required 31-bar purge makes the training end index 47, before warmup. Reducing warmup, holding period, or purge would violate the frozen methodology. H4 is ranked unavailable rather than treated as negative evidence.

## Ranking by evidence of Time Wheel contribution

1. **M15** — strongest measured per-trade wheel-exit effect, but still no usable value: all isolated variants lose and drawdown/P&L deteriorate.
2. **M1** — more trade evidence, but wheel-entry contribution is mixed and wheel-exit improvement per trade comes with worse aggregate risk; no demonstrated standalone value.
3. **H1** — apparent wheel-exit uplift, but only 15–29 trades; insufficient for inference.
4. **H4** — unavailable under the frozen causal warmup/split/purge rules.

This is an evidence ranking, not a performance ranking or a parameter-selection step. It does not support claiming a positive Time Wheel edge on any timeframe.

## Reproducibility and preservation

[Full comparison JSON](experiments/TW-HIGHER-TF-1-20260910T150431842360Z/comparison.json) contains training, validation, and test summaries plus all fixed-entry/fixed-exit attribution deltas. The experiment directory holds 30 compressed per-timeframe/segment/arm outputs with signals, selected levels, rejections, trades, equity, and raw metrics. Source and SQLite logical fingerprints were unchanged before/after the run. Fifteen research tests passed.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_research*.py" -q
.\.venv\Scripts\python.exe scripts\research_higher_timeframes.py
```
