# DIGITAL_TIME_WHEEL_V4_LONG_HISTORY_RESEARCH

Offline research only: files are genuine `DIRECT_MT5` CSVs; this program imports no MT5 module, execution controller, or order API. Entries are known at a completed bar close and use the next contiguous bar open. Splits are chronological 60/20/20; ten bars are purged at each entry-quality boundary. Final holdout was not used for candidate, exit, holding-time, or breakeven selection. Fixed research cost is 0.40 quote-price units. Trade tests use one non-overlapping position and conservative stop-first resolution. Holding exits use the first subsequent bar open at or after the wall-clock deadline.

## Splits

| TF | Window | First UTC | Last UTC | Bars |
| --- | --- | --- | --- | --- |
| M15 | development | 2022-07-04T10:00:00+00:00 | 2025-01-15T23:00:00+00:00 | 60000 |
| M15 | validation | 2025-01-15T23:15:00+00:00 | 2025-11-19T02:30:00+00:00 | 20000 |
| M15 | holdout | 2025-11-19T02:45:00+00:00 | 2026-09-24T18:15:00+00:00 | 20000 |
| M30 | development | 2018-04-11T04:00:00+00:00 | 2023-05-09T14:30:00+00:00 | 60000 |
| M30 | validation | 2023-05-09T15:00:00+00:00 | 2025-01-16T01:00:00+00:00 | 20000 |
| M30 | holdout | 2025-01-16T01:30:00+00:00 | 2026-09-24T18:00:00+00:00 | 20000 |
| H1 | development | 1998-04-22T00:00:00+00:00 | 2022-02-16T05:00:00+00:00 | 40870 |
| H1 | validation | 2022-02-16T06:00:00+00:00 | 2024-06-06T05:00:00+00:00 | 13624 |
| H1 | holdout | 2024-06-06T06:00:00+00:00 | 2026-09-24T18:00:00+00:00 | 13624 |

Eight fixed, interpretable technical entries were evaluated independently: EMA_ADX20, EMA_ADX25, STRONG_ADX30, SLOPE_ADX25, RSI_MOMENTUM, PULLBACK, NORMAL_ATR_TREND, LOW_ATR_TREND. ATR regime uses prior data only. Time Wheel arms only filter a frozen technical candidate; they are not a source of entry direction.
