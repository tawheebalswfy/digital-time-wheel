# New Forward-Test Analysis — Durable Execution Linkage

## Scope, sources, and method

This is a read-only analysis of `reee.html` and `timewheel-new-test.sqlite3`. The database was opened through SQLite's read-only URI mode. No runtime database, strategy, formula, execution setting, MT5 order, or auto-trading state was changed.

The MT5 report is a new, distinct export, not the older forensic report: it was generated **2026-09-22 14:28** for demo account 52960017 and contains 58 closed XAUUSD positions. The prior reference period had 196 closed trades and is used only for the limited comparison stated below.

### Defensible new-test window

The exact code-deployment timestamp is not stored as experiment metadata (the `experiments` table is empty), so it cannot be proven independently. The safest defensible window is therefore the full MT5 export whose entry comments all use the new format and whose position tickets all have a one-to-one SQLite match:

- First MT5 open: **2026-09-18 01:45:01**
- Last MT5 close: **2026-09-22 16:46:17**
- Matching SQLite `created_at` range: **2026-09-17T22:45:00.896791+00:00** to **2026-09-22T13:45:00.697852+00:00**
- Trades: 58 closed; no current open position is shown (report margin and floating P/L are both zero).
- Symbol: XAUUSD only.

The three-hour difference between the beginning/end of the `created_at` range and the MT5 report clock is consistent with a UTC-versus-report-clock offset. It was not used for matching; tickets were used.

## SQLite structure inspected

The execution/history table is `execution_orders` (249 rows). It has `id` as its primary key and `signal_id TEXT UNIQUE NOT NULL REFERENCES signals(id)`. Relevant durable-linkage columns are `symbol`, `timeframe`, `candle_time`, `direction`, `strategy_version`, `magic_number`, `mt5_order_ticket`, `mt5_deal_ticket_open`, `mt5_position_ticket`, `mt5_deal_ticket_close`, `mt5_order_ticket_close`, `mt5_comment`, entry/exit prices and times, P/L, costs, and `final_status`.

Relevant indexes are `idx_execution_orders_mt5_position (mt5_position_ticket)`, `idx_execution_orders_signal_scope (symbol,timeframe,signal_id)`, `idx_execution_orders_symbol`, and `idx_execution_orders_symbol_timeframe`. SQLite also supplies unique indexes for primary/unique keys. `signals`, `signal_results`, and `wheel_states` are the related signal/history tables; there is no separate execution-history table. `experiments`, `backtests`, `datasets`, and `candles` are empty in this snapshot.

## Matching and linkage coverage

Matching was done in priority order. For every MT5 position, `mt5_position_ticket` was found first (and agreed with `mt5_order_ticket` / legacy `position_ticket` where populated). No time-price-only match was made.

| Classification | MT5 closed trades | Share |
|---|---:|---:|
| MATCHED_EXACT | 58 | 100.00% |
| MATCHED_STRONG | 0 | 0.00% |
| UNMATCHED | 0 | 0.00% |
| AMBIGUOUS | 0 | 0.00% |

This is 100.00% ticket-proven coverage (58/58), materially above the former 4.59% linkage coverage. It measures execution linkage, not trading quality.

| Persisted field on the 58 exact matches | Populated | Coverage |
|---|---:|---:|
| signal_id | 58 | 100.00% |
| timeframe | 58 | 100.00% |
| candle_time | 0 | 0.00% |
| symbol | 58 | 100.00% |
| direction | 0 | 0.00% |
| strategy_version | 0 | 0.00% |
| magic_number | 0 | 0.00% |
| mt5_order_ticket | 58 | 100.00% |
| mt5_deal_ticket_open | 58 | 100.00% |
| mt5_position_ticket | 58 | 100.00% |
| mt5_deal_ticket_close | 1 | 1.72% |
| mt5_order_ticket_close | 1 | 1.72% |
| mt5_comment | 58 | 100.00% |
| entry_price | 58 | 100.00% |
| open_time | 58 | 100.00% |
| close_time | 1 | 1.72% |
| realized_profit | 1 | 1.72% |
| commission | 1 | 1.72% |
| swap | 1 | 1.72% |
| final_status | 58 | 100.00% (but 57 are stale `POSITION UNKNOWN`) |

### MT5 comment verification

All **58/58** entry positions and all 58 matched database rows contain exactly `DTW|XAUUSD-M15|M15`. This conforms to `DTW|<identifier>|<TIMEFRAME>`; the timeframe is recoverable as M15 in 58/58 cases. There is no observed truncation or broker alteration. Exit deals in the report have the expected broker-generated `[tp ...]` / `[sl ...]` comments; those are not strategy entry comments.

## Performance by true timeframe

Only M15 has ticket-proven matched trades. “Net” below is MT5 position profit plus commission and swap; gross profit/loss is before costs. All figures are USD.

| Timeframe | Trades | W / L / BE | Win rate | Gross profit | Gross loss | Net P/L | PF | Expectancy | Avg win | Avg loss | Payoff | Largest win / loss | Avg hold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M1 | 0 | — | — | — | — | — | — | — | — | — | — | — | — |
| M5 | 0 | — | — | — | — | — | — | — | — | — | — | — | — |
| M15 | 58 | 49 / 9 / 0 | 84.48% | 109.39 | -103.50 | 5.89 | 1.06 | 0.10 | 2.19 | -11.28 | 0.19 | 5.85 / -15.78 | 1:04:48 |
| M30 | 0 | — | — | — | — | — | — | — | — | — | — | — | — |
| H1 | 0 | — | — | — | — | — | — | — | — | — | — | — | — |
| H4 | 0 | — | — | — | — | — | — | — | — | — | — | — | — |
| D1 | 0 | — | — | — | — | — | — | — | — | — | — | — | — |

There is no cross-timeframe ranking: M15 is both the only observed and therefore the only measured timeframe. Its 58-trade sample is informative but remains a short forward window.

### Symbol × timeframe

| Symbol / timeframe | Trades | Net P/L | PF | Expectancy | Win rate |
|---|---:|---:|---:|---:|---:|
| XAUUSD M15 | 58 | 5.89 | 1.06 | 0.10 | 84.48% |

No other symbol/timeframe combination was traded in this report.

### Buy versus sell (within M15)

| Side | Trades | Net P/L | PF | Expectancy | Win rate | Avg win | Avg loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| BUY | 24 | -5.06 | 0.89 | -0.21 | 79.17% | 2.25 | -9.55 |
| SELL | 34 | 10.95 | 1.20 | 0.32 | 88.24% | 2.16 | -13.45 |

The measured sample shows profitable sells and unprofitable buys. This should not be generalized beyond this single M15-only 58-trade period.

## Multi-timeframe clusters and duplicate execution

There are **no same-symbol, same-direction opening clusters** within 5 seconds, 30 seconds, or 60 seconds. Consequently:

- LEGITIMATE_MULTI_TIMEFRAME clusters: **0**
- TRUE_DUPLICATE clusters: **0**
- UNRESOLVED clusters: **0**

The database independently shows zero duplicate `signal_id` values and zero repeated `mt5_position_ticket`, `mt5_order_ticket`, `mt5_deal_ticket_open`, `mt5_deal_ticket_close`, or `mt5_order_ticket_close` values. `signal_id` has a database UNIQUE constraint. For this new 58-trade window, the proven true-duplicate rate is **0/58 (0.00%)**. Because all 58 new rows have `candle_time` NULL, the stronger same-symbol/timeframe/candle/direction duplicate check cannot prove a positive duplicate; it also cannot provide additional independent assurance.

## Top loss attribution

All ten largest losses are M15, so the losses are concentrated in the only measured timeframe. There was no simultaneous same-direction opening cluster within 60 seconds for any of these trades; with no MTF clusters, simultaneous exposure from other timeframes is zero in the defined cluster sense.

| MT5 position | Open time | Symbol | Side | Signal ID | Entry | SL | TP | Close | Net | Duration |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 1943984119 | 2026-09-18 17:30:03 | XAUUSD | SELL | XAUUSD-M15-255e93d491442305edaf5261 | 4342.97 | 4358.53 | 4341.00 | 4358.67 | -15.78 | 0:21:08 |
| 1948577108 | 2026-09-21 18:00:03 | XAUUSD | SELL | XAUUSD-M15-5f75b9b0317aefb0603d2f12 | 4339.32 | 4354.58 | 4336.00 | 4354.63 | -15.39 | 0:35:37 |
| 1949047603 | 2026-09-21 20:45:04 | XAUUSD | SELL | XAUUSD-M15-c3248c144707dfaba68fbdbc | 4339.31 | 4353.93 | 4338.00 | 4353.90 | -14.67 | 1:54:41 |
| 1951253316 | 2026-09-22 10:30:03 | XAUUSD | BUY | XAUUSD-M15-ee864fb60d88d32072e38fbc | 4315.35 | 4302.58 | 4318.00 | 4302.63 | -12.80 | 0:21:45 |
| 1947292376 | 2026-09-21 12:15:00 | XAUUSD | BUY | XAUUSD-M15-331707f99f0b0cbd14eb12ce | 4353.78 | 4342.32 | 4355.00 | 4341.95 | -11.91 | 0:17:26 |
| 1945647227 | 2026-09-21 01:30:03 | XAUUSD | BUY | XAUUSD-M15-cdb53f1b9d3211b279742c6e | 4376.09 | 4365.24 | 4378.00 | 4365.32 | -10.85 | 1:41:15 |
| 1949795194 | 2026-09-22 03:15:01 | XAUUSD | BUY | XAUUSD-M15-fb1158b5a9e3fdcb937a8ea1 | 4370.19 | 4360.30 | 4372.00 | 4359.76 | -10.51 | 0:03:25 |
| 1949518911 | 2026-09-22 01:45:07 | XAUUSD | SELL | XAUUSD-M15-7b282df482660cf728d16af5 | 4353.43 | 4361.29 | 4351.00 | 4361.31 | -7.96 | 0:06:03 |
| 1945846446 | 2026-09-21 03:11:20 | XAUUSD | BUY | XAUUSD-M15-198fce055ab546858f05f94b | 4365.46 | 4363.94 | 4374.00 | 4363.87 | -1.67 | 0:02:25 |
| 1949735625 | 2026-09-22 03:00:04 | XAUUSD | BUY | XAUUSD-M15-1441c017192b8819ae6dc92a | 4369.79 | 4358.73 | 4370.00 | 4370.26 | 0.39 | 0:01:58 |

The tenth row is included because there are only nine negative-net trades; it is the smallest positive net trade. The report itself classifies nine loss trades.

## Holding time

| Holding bucket | Trades | Net P/L | PF | Expectancy |
|---|---:|---:|---:|---:|
| <1 minute | 6 | 11.20 | — (no losses) | 1.87 |
| 1–5 minutes | 26 | 36.52 | 4.00 | 1.40 |
| 5–15 minutes | 9 | 13.15 | 2.65 | 1.46 |
| 15–60 minutes | 12 | -37.16 | 0.34 | -3.10 |
| >60 minutes | 5 | -17.82 | 0.30 | -3.56 |

Within M15, all profits in the first three holding buckets are positive, while the two longer buckets are negative. This is an observed association, not evidence to alter the strategy.

## SL/TP geometry

For BUY, planned risk was entry−SL and reward TP−entry; for SELL, risk was SL−entry and reward entry−TP. All 58 matched M15 trades had usable entry, SL and TP values.

| Timeframe | Avg planned SL distance | Avg planned TP distance | Avg planned R:R | Avg winner | Avg loser |
|---|---:|---:|---:|---:|---:|
| M15 | 12.07 | 2.28 | 0.27 | 2.19 | -11.28 |

The planned reward is much smaller than planned risk in M15, and realized average loser is about 5.14 times realized average winner. Since no other timeframe is present, no concentration comparison across timeframes is possible; the poor loss geometry is present in the only observed timeframe.

## Cost impact

| Measure | USD |
|---|---:|
| Gross P/L before commission and swap | 10.11 |
| Commission | -4.64 |
| Swap | 0.42 |
| Final net P/L | 5.89 |
| Net cost (commission + swap) | -4.22 |
| Average net cost per trade | -0.07 |

All cost impact is M15 because it is the only traded timeframe. The test is positive before costs and remains positive after costs; costs reduced the result by 4.22 (41.7% of pre-cost gross P/L).

## Data-integrity checks and limitations

| Check | Result |
|---|---|
| MT5 ticket linkage | 58 exact one-to-one matches; no ambiguity |
| Entry price / entry ticket agreement | 58/58 agreement |
| Successful execution with NULL position ticket | 0 across the snapshot states inspected |
| Duplicate signal IDs | 0 (also prevented by UNIQUE constraint) |
| Duplicate MT5 ticket IDs | 0 for all inspected ticket fields |
| Close record without open linkage | 0 |
| New rows missing `candle_time`, `direction`, `strategy_version`, `magic_number` | 58 each |
| New MT5-closed trades still `POSITION UNKNOWN` in SQLite | 57/58 |
| New rows missing close deal/order/time/P&L/cost fields | 57/58 each |
| MT5-vs-SQLite realized P/L comparison possible | 1 row; raw P/L agrees at -14.59 |
| Cost comparison on that row | SQLite commission is -0.04 while the MT5 position commission is -0.08; database closure value is incomplete for the full position |
| Impossible timestamp | 1 row: ticket 1949047603 has SQLite close `2026-09-21T19:39:45+00:00`, earlier than its SQLite open `2026-09-21T20:45:04+00:00`; MT5 reports close 2026-09-21 22:39:45 |
| Stale/orphaned execution evidence | 57 stale lifecycle rows in the new window; no ticket-orphaned MT5 trade |

`open_time` values agree with the report when punctuation/ISO formatting is normalized. The single populated close timestamp has a three-hour offset and becomes earlier than its open timestamp; it is therefore unusable as a duration source. All performance durations in this document come from the MT5 report. The database snapshot cannot currently support a complete closed-trade reconciliation despite excellent entry linkage.

## Comparison with the previous demo

| Metric | Previous demo (reference supplied) | New report | Interpretation |
|---|---:|---:|---|
| Closed trades | 196 | 58 | Samples/periods are not comparable in size |
| Net P/L | about -23.63 | 5.89 | Directionally better, but not a comparable-performance claim |
| PF | about 0.94 | 1.06 | Directionally better, but only this short M15-only run |
| Expectancy | about -0.12 | 0.10 | Directionally better, not sufficient to establish improvement |
| Linkage match coverage | 4.59% | 100.00% exact ticket match | Material, directly demonstrated linkage improvement |

## Verdict

**Durable linkage verdict: PASS (entry-level linkage).** The stated PASS standard requires at least 95% of new system trades with provable timeframe, signal, and MT5-ticket linkage. The result is 58/58 (100.00%), with all three fields populated and each report position linked by ticket to exactly one persisted execution record.

This is not a PASS for full lifecycle capture: close ticket, close timestamp, close P/L, costs, and final closed state are absent for 57/58 MT5-closed positions, and the one close timestamp is impossible. The implementation demonstrably solved entry linkage but has not demonstrably solved durable closure-state recording.

### Highest-confidence next step

Without changing strategy logic or execution settings, perform a further read-only post-run reconciliation after a subsequent export/snapshot to verify whether MT5-closed positions receive durable close tickets, close timestamps, P/L, costs, and `CLOSED` status. Preserve the present ticket-first matching rule and do not infer missing candle/direction metadata from time or price.
