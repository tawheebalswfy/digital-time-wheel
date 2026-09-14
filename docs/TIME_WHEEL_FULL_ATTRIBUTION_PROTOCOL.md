# Controlled experiment TW-FULL-EXIT-1

Specified before any results. This is a research-only attribution harness. It does not modify production defaults, the immutable baseline, saved settings, or retained SQLite records.

## Objective

Separate the current Time Wheel's entry contribution from its exit contribution. The preceding TW-ENTRY-1 study shared exits and therefore did not identify this question.

## Dataset, boundaries, costs, and execution

Use only the retained MT5 XAUUSD M1 dataset `bc6555d92c6833e68b00e9bfb27f4dca516a6998d996349596783e37b6e0b288` (30,170 candles; content hash `103c37e49d4e8901dd4963a3db78dd32fa9721ae570b6f473b4834c615cda2a4`). The chronological bars and purges are identical to TW-ENTRY-1:

| Segment | Evaluated indices, end exclusive |
|---|---|
| Train | [78, 18071) |
| Purge | [18071, 18102) |
| Validation | [18102, 24105) |
| Purge | [24105, 24136) |
| Final test | [24136, 30170) |

The first final-test bar opens at 4 September 2026 02:46 UTC; first signal is at 02:47 UTC. Start each simulated portfolio flat at 10,000 quote-price units. Use the existing next-bar-open entry, immediate-next-bar requirement, one open position, stop-first resolution for an ambiguous bar, adverse stop-gap fill, maximum 30-bar hold, full spread 0.30, two slippages of 0.05, fee 0, and one-unit P&L. No parameter, indicator, threshold, cost, or timeframe search is allowed.

## Entry families

Reuse exactly the frozen TW-ENTRY-1 entry definitions without changing the production code:

- **Technical entry T:** existing structure, support/resistance, momentum, and Fibonacci votes, normalized over their active 40 existing weight points; unchanged threshold 55; no wheel direction, harmonics, gates, geometry, or volatility vote.
- **Wheel entry W:** existing wheel, geometry, and gates votes normalized over active 55 existing weight points; unchanged threshold 55 and agreement with existing numerical wheel direction; no technical directional confirmation. The prior entry-only study included the ATR-dependent volatility vote in W. It is excluded here because this fully isolated experiment must not use a technical indicator in a wheel-only strategy.
- **Production E:** existing `signals.analyze` plus existing production exit logic, reproduced exactly as a reference rather than modified.

## Fully independent exit families

Exit families do not use the other family's levels, stop rules, invalidations, or indicators. A candidate is assessed only from the closed signal bar. At the next open it must still be directionally valid: `direction * (target - open) > 0` and `direction * (open - stop) > 0`; otherwise it is a rejected gap/invalid opportunity.

### Technical exit T

Build candidates from only the existing **confirmed** `support`, `resistance`, `swing_high`, `swing_low`, and Fibonacci projections. A long target is the nearest distinct candidate above the signal close; a long stop is the nearest distinct candidate below it. A short target/stop reverse those directions. Candidates must be at least 0.01 quote-price units from the signal close. Keep every source/rationale at the selected price. No wheel price levels, harmonics, gates, Gann levels, ATR target, ATR stop, or any time-wheel state may enter this function.

### Wheel exit W

Build candidates from only existing `wheel_levels` and angular inverse projections at the frozen harmonics. A long target is the nearest distinct level above the signal close; a long stop is the nearest distinct level below it. A short target/stop reverse those directions. Candidates must be at least 0.01 quote-price units from the signal close. Keep every wheel/angle rationale at selected levels. No OHLC technical indicator, support/resistance, swing, Fibonacci, ATR, or technical state may enter this function. The current configured anchor, increment, mapping, harmonics, orientation, clock, and timestamp are the existing Time Wheel inputs, not new parameters.

If either target or stop is absent, do not enter. The definitions are deliberately mechanical rather than selected for profitability.

## Arms

| Arm | Entry family | Exit family |
|---|---|---|
| A | T | T |
| B | W | W |
| C | T | W |
| D | W | T |
| E | Current combined production baseline | Current combined production exits |

E is a reference control, not a fifth independent family. A–D are independently simulated; no saved trade list is filtered.

## Attribution and final conclusion

Report all requested metrics and average holding minutes. Report entry attribution under each fixed exit: D − A (wheel versus technical entries with technical exits) and B − C (wheel versus technical entries with wheel exits). Report exit attribution under each fixed entry: C − A (wheel versus technical exits with technical entries) and B − D (wheel versus technical exits with wheel entries). Positive expectancy/P&L deltas favor the wheel; positive drawdown delta is adverse.

To inspect filtering, evaluate every technical-entry opportunity individually using the technical exit, independently of occupancy. Partition it by whether the existing combined production entry accepts the same direction. Report rejected/accepted opportunity counts, gross/net expectancy, and the number of profitable versus losing counterfactual opportunities. This is a descriptive diagnostic, not a causal matched-trade estimate.

The final conclusion uses the final-test segment only. Training and validation are reported for transparency and are not used to select a model. The final period was already inspected in prior research and contains only six represented UTC dates, so it is out-of-sample relative to the frozen train/validation split but not an untouched independent holdout. The experiment is M1-only by the user-required same-dataset condition; it cannot make a claim about stronger value on other timeframes. No such claim may be inferred from the M1 result.

Archive source/database fingerprints, exact signals, rejected opportunities, trades, equity, metrics, hashes, and tests. Run all rules before reviewing results. No production promotion follows this experiment.
