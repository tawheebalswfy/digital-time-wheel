# V6 XAU Timeframe Discovery Protocol

XAUUSD only. Offline direct-MT5 CSV research; no production or order APIs. Final holdouts are excluded from discovery. Five fixed coarse archetypes are independently tested per timeframe.

| TF | Source | First UTC | Last UTC | Candles | Duplicates | Invalid OHLC | Gaps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M5 | DIRECT_MT5 | 2025-04-29T14:25:00+00:00 | 2026-09-24T18:20:00+00:00 | 100000 | 0 | 0 | 372 |
| H4 | DIRECT_MT5 | 1998-04-22T00:00:00+00:00 | 2026-09-24T20:00:00+00:00 | 21280 | 0 | 0 | 5334 |
| D1 | DIRECT_MT5 | 1998-04-22T00:00:00+00:00 | 2026-09-24T00:00:00+00:00 | 7508 | 0 | 0 | 1495 |