# DIGITAL_TIME_WHEEL_V3_ENTRY_RESEARCH

Research-only causal entry study. V1 and V2 were not read, modified, or executed. This runner imports no execution controller and sends no MT5 order. It evaluates a signal only at a completed bar, assumes next-bar-open entry, and measures raw directional movement at 1, 2, 3, 5, and 10 completed bars. No stop, target, holding-time, cost, or position-cap selection occurred.

## Historical availability

| Timeframe | Source | First UTC | Last UTC | Candles | Calendar days |
| --- | --- | --- | --- | --- | --- |
| M15 | MT5 | 2026-08-11T14:15:00+00:00 | 2026-09-10T13:45:00+00:00 | 2013 | 27 |
| M30 | MT5 | 2026-08-11T14:30:00+00:00 | 2026-09-10T13:30:00+00:00 | 1006 | 27 |
| H1 | MT5 | 2026-08-11T15:00:00+00:00 | 2026-09-10T13:00:00+00:00 | 503 | 27 |

A bounded read-only request for 2026-03-01 through 2026-09-22 was attempted against the connected MT5 terminal. It did not save bars, alter the database, or call an order API.

| Timeframe | Returned | First UTC | Last UTC | Result |
| --- | --- | --- | --- | --- |
| M15 | 0 | — | — | MT5 returned no rates: (-1, 'Terminal: Call failed') |
| M30 | 0 | — | — | MT5 returned no rates: (-1, 'Terminal: Call failed') |
| H1 | 0 | — | — | MT5 returned no rates: (-1, 'Terminal: Call failed') |

The terminal connected but `copy_rates_range` returned `(-1, Terminal: Call failed)` for M15, M30, and H1. The available retained data therefore remains about 30 calendar days and has already been inspected in V1/V2. The chronological partitions below are explicitly **retrospective IN-SAMPLE**, not independent unseen validation.

## Protocol

- Windows: first 60% development, next 20% validation, last 20% retrospective holdout; signals within ten bars of a boundary are excluded from that window.
- Candidate selection: greatest development 5-bar directional expectancy among candidates with at least 30 signals.
- Minimum labels: <30 INSUFFICIENT_SAMPLE; 30–99 LOW_CONFIDENCE; >=100 USABLE_FOR_COMPARISON.
- Existing features only: EMA structure and 3-bar slow-EMA slope, ADX/+DI/-DI, RSI, ATR. ATR regime uses only the prior 100 completed bars.
- Time Wheel is recorded but is not mandatory in the base V3 entry arm.
