# Cooldown / Cluster Walk-Forward Validation Protocol

## Objective

Measure only execution-risk filters around the existing signals and exits. No Time Wheel formula, technical indicator, signal threshold, target, invalidation, or entry timing was changed.

## Candidate set

- Baseline: 0 seconds, no same-direction cap
- Cooldowns: 60, 120, 180, 300 seconds
- Caps: 1 or 2 simultaneous same-symbol/same-direction positions
- Combined: 60 + cap 1, 120 + cap 1, 300 + cap 1

## Data and chronology

The saved genuine MT5 XAUUSD M1 dataset covers 2026-08-11 through 2026-09-10 UTC and was resampled causally to M5, M15, M30 and H1. The forensic report starts 2026-09-13 UTC, so no validation window overlaps it.

| Window | UTC range | Use |
|---|---|---|
| Discovery | 2026-08-11 to 2026-08-31 | Candidate inspection only |
| Validation | 2026-08-31 to 2026-09-06 | Freeze candidate |
| Final holdout | 2026-09-06 to 2026-09-11 | Confirmation only |

Signals use the existing causal backtester, next-bar-open entry, existing target/invalidation, full configured costs, chronological ordering, and no randomization. Filter acceptance is chronological: an entry is blocked when the same symbol/direction is inside the selected cooldown or has reached the selected active-position cap. Blocked entries are counted.

## Symbol availability limitation

The local database has no non-overlapping historical datasets for BTCUSD or EURUSD. Direct read-only MT5 history requests for the required old period returned no bars. They are therefore reported as unavailable rather than replaced with synthetic data or the forensic week. No cross-symbol claim is made.

## Decision rule

A candidate is supported only when PF and expectancy improve against baseline in both validation and holdout, drawdown does not materially worsen, and the result is not dependent on one symbol or one day. Since only XAUUSD is available here, no candidate qualifies for production promotion even where its XAUUSD replay improves.
