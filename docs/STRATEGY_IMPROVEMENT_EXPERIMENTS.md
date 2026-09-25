# Strategy Improvement Experiments

## Governance

Production is unchanged. All results below are research-only, use genuine MT5 XAUUSD history, retain chronological discovery/validation/final evaluation, and exclude the later forward DEMO run. The historical final segment is retrospective OOS only; no candidate is called production-ready.

## Existing fixed candidate set

The pre-existing cooldown/exposure experiment tested one execution-risk rule at a time: 60/120/180/300-second same-symbol-direction cooldowns, one/two-position caps, and predeclared combinations. This is not a strategy rewrite and does not alter Wheel formulas or signals.

| Candidate | Validation PF / expectancy | Final PF / expectancy | Final max DD | Result |
|---|---:|---:|---:|---|
| Baseline | 0.503 / -0.548 | 0.491 / -0.535 | 439.56 | Negative reference. |
| 60s cooldown | 0.475 / -0.521 | 0.485 / -0.468 | 332.89 | Lower loss/DD, no PF improvement. |
| 180s cooldown | 0.477 / -0.497 | 0.500 / -0.448 | 265.30 | Lower loss/DD, still negative. |
| One-position cap (`cap_1`) | 0.524 / -0.489 | 0.551 / -0.426 | 289.14 | Best validation candidate; replicated relative improvement, still negative. |
| 60s cooldown + cap_1 | 0.486 / -0.508 | 0.501 / -0.444 | 281.61 | Worse than cap_1 on PF/expectancy. |

`cap_1` is the strongest **research candidate**, not a validated production candidate: it improved final PF, expectancy, and drawdown relative to the baseline but failed the positive-expectancy/PF>1 success criteria.

## Diagnostic exit candidates not promoted

Fixed 0.5R/0.75R/1.0R/1.25R/1.5R target variants and 15/30/45/60 minute hard exits remain unrun against a newly frozen, genuinely unseen history interval. Existing evidence makes them justified diagnostics—not accepted improvements—because the retained final period is already inspected and holding time may be an outcome marker rather than a causal control.

## Candidate backlog (maximum five)

1. `cap_1` exposure cap: research-only; supported by validation/final relative DD and expectancy improvement; risk is still-negative expectancy.
2. 15/30/45/60-minute maximum-hold diagnostic: exit-only; supported by adverse duration buckets; risk is curve fitting/cutting eventual winners.
3. Fixed R-target diagnostic grid: exit-only; supported by poor realized/planned payoff; risk is target/stop selection on reused data.
4. Technical-only versus full-entry re-test on new history: entry attribution only; supported by final M1 comparison; risk is loss of Wheel concept measurement and nonstationarity.
5. M1 exclusion study: timeframe-selection research only; supported by largest adequate-sample losses; risk is removing trades based on one month.

No session, direction, ADX, RSI, ATR, or new-indicator filter qualifies because no pre-registered out-of-sample evidence supports a threshold.

## Combination rule

Do not combine candidates until each individually has positive/controlled validation and genuinely unseen holdout evidence. The existing `cap_1 + cooldown` combination was weaker than `cap_1`, so no combination is accepted.
