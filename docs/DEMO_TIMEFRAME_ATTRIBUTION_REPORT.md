# Demo Timeframe Attribution Report

Source: `ReportHistory-52960017.html` plus persisted execution records. Auto trading remained disabled; no order was sent. Timeframe is never inferred for unmatched rows.

## Match coverage

- MT5 trades: **196**
- Matched by persisted ticket and symbol: **9**
- Unmatched: **187**
- Match coverage: **4.59%**

Coverage is too low for reliable whole-week timeframe conclusions. The matched subset is descriptive only.

## Matched performance by timeframe

| Timeframe | Trades | Wins | Losses | Win rate | Gross profit | Gross loss | Net P/L | PF | Expectancy | Avg win | Avg loss | Payoff | Largest win | Largest loss | Max DD | Win streak | Loss streak | Avg R:R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H1 | 6 | 6 | 0 | 100.0% | 24.73 | 0.00 | 24.73 | — | 4.12 | 4.12 | — | — | 4.92 | 1.84 | 0.00 | 6 | 0 | 0.21 |
| M15 | 2 | 2 | 0 | 100.0% | 0.70 | 0.00 | 0.70 | — | 0.35 | 0.35 | — | — | 0.36 | 0.34 | 0.00 | 2 | 0 | 0.27 |
| M30 | 1 | 1 | 0 | 100.0% | 0.36 | 0.00 | 0.36 | — | 0.36 | 0.36 | — | — | 0.36 | 0.36 | 0.00 | 1 | 0 | 0.16 |

## Symbol + timeframe

| Symbol/timeframe | Trades | Win rate | Net P/L | PF | Expectancy | Avg duration (min) | Median duration (min) | Avg SL | Avg TP | Avg R:R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD H1 | 1 | 100.0% | 1.84 | — | 1.84 | 241.02 | 241.02 | 360.68 | 182.22 | 0.51 |
| BTCUSD M15 | 2 | 100.0% | 0.70 | — | 0.35 | 6.17 | 6.17 | 141.94 | 38.28 | 0.27 |
| BTCUSD M30 | 1 | 100.0% | 0.36 | — | 0.36 | 6.52 | 6.52 | 226.96 | 35.61 | 0.16 |
| XAUUSD H1 | 5 | 100.0% | 22.89 | — | 4.58 | 11.65 | 8.32 | 30.50 | 4.55 | 0.15 |

## BUY / SELL by timeframe

| Timeframe | Side | Trades | Win rate | PF | Expectancy | Net P/L | Avg win | Avg loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| H1 | BUY | 0 | — | — | — | 0.00 | — | — |
| H1 | SELL | 6 | 100.0% | — | 4.12 | 24.73 | 4.12 | — |
| M15 | BUY | 0 | — | — | — | 0.00 | — | — |
| M15 | SELL | 2 | 100.0% | — | 0.35 | 0.70 | 0.35 | — |
| M30 | BUY | 0 | — | — | — | 0.00 | — | — |
| M30 | SELL | 1 | 100.0% | — | 0.36 | 0.36 | 0.36 | — |

## Cluster classification

| Category | Clusters | Trades represented |
|---|---:|---:|
| LEGITIMATE_MULTI_TIMEFRAME | 1 | 2 |
| PROVEN_DUPLICATE_SAME_TIMEFRAME | 0 | 0 |
| UNRESOLVED | 33 | 86 |

### Proven matched cluster

| Open time | Symbol | Direction | Tickets | Timeframes | Signal IDs | Combined P/L | Classification |
|---|---|---|---|---|---|---:|---|
| 2026.09.14 00:30:02 | BTCUSD | SELL | 1928455618, 1928455627 | M15, M30 | BTCUSD-M15-196728d4-8cde-46e6-a5db-11d081268161, BTCUSD-M30-f079f7ee-667f-487c-98cc-237670384a4e | 0.72 | LEGITIMATE_MULTI_TIMEFRAME |

No same-timeframe same-signal duplicate was proven. The 33 remaining clusters are unresolved because their tickets have no persisted timeframe/signal linkage.

## True duplicate rate

- Matched trades: 9
- Proven duplicate trades: 0
- Legitimate multi-timeframe matched trades: 2
- Unresolved clusters: 33 (86 clustered trades)
- Proven duplicate rate among matched trades: 0.00%

The unresolved cluster count must not be treated as duplicate execution.

## Large losses

The major XAUUSD losses from the report are UNMATCHED in the local execution database. Their originating timeframe cannot be determined without guessing. No timeframe is assigned to them.

| Report loss | Symbol | Direction | Ticket | Timeframe |
|---:|---|---|---:|---|
| -58.56 | XAUUSD | SELL | 1938757473 | UNMATCHED |
| -31.85 | XAUUSD | SELL | 1938757226 | UNMATCHED |
| -23.52 | XAUUSD | SELL | 1938756816 | UNMATCHED |
| -20.97 | XAUUSD | SELL | 1936139781 | UNMATCHED |
| -17.59 | XAUUSD | BUY | 1934769195 | UNMATCHED |
| -14.85 | XAUUSD | BUY | 1937677913 | UNMATCHED |
| -14.42 | XAUUSD | BUY | 1941444667 | UNMATCHED |
| -14.19 | XAUUSD | SELL | 1936139502 | UNMATCHED |
| -11.99 | XAUUSD | BUY | 1934769062 | UNMATCHED |
| -11.90 | XAUUSD | SELL | 1932258801 | UNMATCHED |

## Multi-timeframe exposure

| Distinct matched timeframes in cluster | Events | Trades | Combined P/L | Avg event P/L | Worst event |
|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 2 | 0.72 | 0.72 | 0.72 |

## Holding-time and exit geometry

Holding-time buckets cannot be fully attributed by timeframe for unmatched rows. In the matched subset, H1 includes the 241-minute BTCUSD trade; XAUUSD H1 matched trades have average duration 11.65 minutes. Matched H1 average planned R:R is 0.21, M15 0.27, and M30 0.16. These samples are too small to establish systematic timeframe-level exit geometry.

## Ranking and conclusion

The matched subset ranks H1 highest by net P/L (+24.73), followed by M15 (+0.70) and M30 (+0.36), but H1 has only six matched trades and no losses. No timeframe can be called worst from this coverage. The largest losses are overwhelmingly unmatched, so their timeframe attribution is unknown.

**Highest-confidence next experiment:** repair/preserve durable ticket-to-execution linkage for every order, then repeat this attribution on a complete report. Do not add cooldowns, caps, timeframe disabling, SL/TP changes, or production defaults based on this incomplete linkage.
