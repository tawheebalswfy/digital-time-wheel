# Demo Timeframe Attribution Protocol

## Scope

This is an attribution-only analysis of `ReportHistory-52960017.html` joined to the local execution database. No strategy, Time Wheel, signal, execution default, or account state was changed. No MT5 order was sent.

## Matching rule

A report position is MATCHED only when its MT5 position ticket equals a persisted `position_ticket` and the persisted symbol agrees. Timeframe and signal ID are copied from that execution record. Open time, price, volume, comment, and direction are used as consistency evidence but never to guess a timeframe. All other rows are UNMATCHED.

## Cluster rule

Entries are grouped by symbol, direction, and open-time proximity of 60 seconds. A cluster is **LEGITIMATE_MULTI_TIMEFRAME** only when matched records prove different timeframes. It is **PROVEN_DUPLICATE_SAME_TIMEFRAME** only when every member is matched and the same timeframe and signal ID/candle identity are proven. All other clusters are **UNRESOLVED**.

## Metrics

Net P/L is report Profit + Commission + Swap. Profit factor is undefined when a group has no losses; it is never represented as a finite number. Drawdown and streaks are calculated in close-time order. SL/TP distances use the direction-aware entry-to-invalidation and entry-to-target distances from the report.

## Coverage rule

Timeframe conclusions are partial unless match coverage is high and each group has adequate sample size. This report therefore treats the matched timeframe results as descriptive only and does not infer the timeframe of the 187 unmatched trades.
