# DIGITAL_TIME_WHEEL_V5_CONCEPT_DISCOVERY

Offline, read-only study using only direct-MT5 CSVs. Five fixed, distinct technical archetypes were tested; no parameter sweep, no MT5 import, no order API. Signal is at completed-bar close, entry next contiguous-bar open, and the holdout is absent from all discovery/selection loops. Time Wheel is tested only after a concept passes the development/validation entry gates.

| TF | Split | First UTC | Last UTC | Bars |
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

Concepts: TREND_CONTINUATION, PULLBACK_CONTINUATION, BREAKOUT, MEAN_REVERSION, VOLATILITY_EXPANSION.
