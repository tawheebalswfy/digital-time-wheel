# V2 Actual Experiment Results

Read-only replay executed from retained genuine MT5 XAUUSD data. M15: 2,013 candles, 2026-08-11 14:15 to 2026-09-10 14:00 UTC; M30: 1,006 candles, 2026-08-11 14:30 to 2026-09-10 14:00; H1: 503 candles, 2026-08-11 15:00 to 2026-09-10 14:00. Each is about 30 calendar days. All data has been inspected in prior research, so results are IN-SAMPLE/retrospective OOS only.

The isolated technical-core entry replay completed with identical technical exits/cost assumptions. Final segment: M15 technical-only: 69 trades, PF 0.517, expectancy -0.891, net -61.49, DD 61.49, avg win 3.13, avg loss -2.65. H1 technical-only: 15 trades, PF 0.593, expectancy -1.478, net -22.16, DD 24.33, avg win 6.46, avg loss -5.45; INSUFFICIENT_SAMPLE. M30 was not represented in the existing isolated-entry harness; V1 final reference is 25 trades, PF 0.637, net -26.74, also LOW_CONFIDENCE.

No technical-core arm has PF>1 or positive expectancy. Staged selection therefore stops before exit/stop/hold/breakeven selection; fitting those grids to a failed entry arm would violate the anti-overfitting protocol.
