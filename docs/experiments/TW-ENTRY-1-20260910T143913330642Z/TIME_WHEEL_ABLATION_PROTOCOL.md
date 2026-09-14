# Controlled experiment TW-ENTRY-1

Specified before calculating new arm results. This user-requested diagnostic takes priority over the previously proposed B0/R1 payoff-eligibility experiment; that experiment remains unexecuted.

## Scope and fixed arms

The only experimental factor is the **entry signal family**. Existing target construction, invalidation, execution, costs, and evaluation are fixed across all arms. In particular, the common exit generator still includes wheel-derived levels and technical price levels. Therefore “technical-only” and “wheel-only” below describe entry decisions, not pure end-to-end strategies. This experiment isolates the incremental entry contribution conditional on the current exits; it cannot identify the contribution of wheel-derived exits.

- **A — immutable baseline:** existing `signals.analyze` and backtest behavior.
- **B — technical-only entries:** use only the existing structure, support/resistance, momentum, and Fibonacci directional votes. Their saved weights are 15, 10, 10, and 5. Score each direction using its supporting weight divided by the active family's total weight (40). Ties are neutral. Require the unchanged threshold 55; do not require wheel direction, harmonics, or digital gates.
- **C — wheel-only entries:** use only the existing wheel-dependent votes: wheel (30), geometry (20), volatility (5), and gates (5), normalized by their active total (60). Require the unchanged threshold 55 and agreement with the existing numerical wheel direction. Remove technical directional confirmation. The volatility vote is assigned the wheel direction by existing code; its nondirectional ATR validity condition stays unchanged. ATR also remains part of the common exits.
- **D — current combined:** exactly A, reported as an explicit duplicate control rather than independent corroboration.

Active-family score normalization keeps the same 0–100 score convention. Simply zeroing the removed votes while retaining a 100-point denominator would make B's maximum 40 fall below threshold 55, mechanically eliminating every B trade. No weights, threshold, indicator settings, or wheel parameters are fitted. This normalization is a declared ablation convention, not a claim that standalone B/C existed as production strategies.

When an ablated direction differs from the baseline's direction, call the same existing target generator with that direction and the same bar/configuration. The rule is fixed; prices need not match between different entry timestamps or opposite directions. Signals are resimulated sequentially with their own position occupancy. Do not filter the saved baseline trades to emulate a new strategy.

## Data and boundaries

Use only retained MT5 XAUUSD M1 dataset `bc6555d92c6833e68b00e9bfb27f4dca516a6998d996349596783e37b6e0b288`, 30,170 candles, content hash `103c37e49d4e8901dd4963a3db78dd32fa9721ae570b6f473b4834c615cda2a4`.

The corrected final-test boundary stays at index 24,136: first bar open 4 September 2026 02:46 UTC, first signal 02:47 UTC. The previous checkpoint had no separate validation set. Subdivide its earlier development portion using a fixed 60/20/20 chronological layout, with 31-bar purges before each later segment:

| Segment | Evaluated bar indices, end exclusive |
|---|---|
| Train | [78, 18071) |
| Purge | [18071, 18102) |
| Validation | [18102, 24105) |
| Purge | [24105, 24136) |
| Final test | [24136, 30170) |

Index 78 is the existing warmup. Earlier history may initialize causal features; trades and forward evaluations cannot cross segment ends. The last included bar supplies an exit/valuation endpoint, not a new entry signal, exactly as in the existing engine. Portfolios start flat at 10,000 quote units in every segment. The original baseline training run remains unchanged in SQLite; the new train/validation split is for this experiment only.

All arm definitions and split indices are frozen before any new arm result is evaluated. Run train, then validation, then test without fitting or selecting a model. The final period was inspected in the preceding checkpoint: it remains the original chronological test segment, but is not an untouched independent holdout for this research question.

## Fixed execution and reporting

Use the existing next-bar-open, immediate-next-bar requirement, single-position, stop-first ambiguity, adverse stop-gap fill, target-1 exit, 30-bar maximum hold, and marked-equity evaluation. Charge spread 0.30 + 2 × slippage 0.05 + fee 0 = 0.40 per trade. No cost grid, indicator search, win-rate objective, or parameter optimization.

Report every arm on every segment: trades, net win rate, mean net win/loss, net profit factor, gross/net expectancy, net P&L, maximum marked drawdown, mean/max MAE and MFE. Preserve the engine's raw Sharpe/Sortino values for reproducibility but withhold them from interpreted results because this short data span cannot establish statistically meaningful annualized ratios.

Compute D minus B for all requested numeric metrics. Different arms have different trades; the expectancy difference is a difference of strategy means, not a paired-trade estimate. Also report daily marked-P&L differences on a common UTC-date grid to expose exposure effects.

For descriptive uncertainty, use a paired circular block bootstrap over represented UTC dates, block length 2, seed 20260910, 10,000 draws, percentile endpoints 2.5/97.5. Pair the same sampled dates across B and D. Recompute net expectancy from trade P&L/count sums attributed to entry date; use marked daily P&L for the separate daily-P&L effect. These are exploratory resampling intervals, not reliable significance claims with only approximately six test dates, unverified stationarity, and previously inspected data.

As an exit-independent diagnostic, use one fixed 300-second horizon on all scored bar-close opportunities that have an exact endpoint within the segment. Record signed return in basis points, assigning zero to neutral decisions, and separately summarize actionable-only observations. No horizon search. Overlapping outcomes are dependent; report descriptively without an independent-signal test. Keep outcomes separate from original forecast payloads.

## Preservation and evidence

The harness must open SQLite read-only and use an isolated function binding of the existing simulator, never patch a running module or change production files/settings. Verify A against the saved original training/test results and verify A=D. Add focused tests for entry-family independence, unchanged exits, no lookahead, engine parity, and bootstrap determinism. Record protocol/code/environment hashes, exact indices, signal audits, trades, equity, full results, comparison tables, and before/after logical database/source fingerprints. Archive protocol and code with each run; never overwrite an earlier run.

The conclusion must distinguish the observed sample effect from independent predictive evidence. No production promotion follows from this diagnostic.
