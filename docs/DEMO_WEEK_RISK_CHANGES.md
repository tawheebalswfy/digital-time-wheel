# Demo Week Risk-Change Decision

## Scope

This decision uses only the closed-trade rows in `ReportHistory-52960017.html`. Auto trading remained disabled and no MT5 order was sent. The report does not prove execution timeframe for every trade, so the replay is a retrospective diagnostic rather than forward validation.

## Evidence ranking

| Rank | Candidate control | Evidence strength | Expected effect | Implementation risk | Decision |
|---:|---|---|---|---|---|
| 1 | Same-symbol/same-direction entry cooldown or cluster cap | High for exposure containment: 34 same-direction clusters within 60 seconds; worst cluster was -113.93 | Reduces duplicate/stacked exposure and loss concentration | Can suppress legitimate multi-timeframe entries; timeframe is not present in the HTML | **Replay only; defer production default until forward test** |
| 2 | Planned reward/risk floor | Weak as a production rule: the report contains many profitable trades below 1.0 R:R and the sample is outcome-selected | Would remove both winners and losers | High risk of changing strategy behavior | **Do not implement** |
| 3 | Daily loss stop or loss-streak pause | Plausible containment, but no unbiased threshold can be selected from one week | Limits tail damage | Medium; threshold selection can overfit | **Configurable forward experiment only** |
| 4 | SELL-side filter | XAUUSD SELL was materially negative, but the report does not establish stable directionality | Could reduce losses | High risk of removing profitable sells | **Do not implement** |

## Same-report replay

The replay keeps the first chronological trade in a same-symbol/same-direction cluster and rejects later entries inside the stated window. It is not a live simulation and is in-sample.

| Variant | Trades | Win rate | Net P/L | Profit factor | Expectancy | Max loss |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 196 | 80.6% | -23.51 | 0.936 | -0.12 | -58.56 |
| 60-second same-symbol/direction cooldown | 143 | 79.7% | 17.96 | 1.098 | 0.13 | -23.52 |
| 300-second same-symbol/direction cooldown | 129 | 80.6% | 25.07 | 1.154 | 0.19 | -23.52 |
| Planned R:R floor 0.25 | 50 | 60.0% | -80.65 | 0.508 | -1.61 | -31.85 |

The positive replay result is evidence that exposure clustering is worth a controlled forward experiment. It is not evidence that the strategy has acquired a validated edge.

## Production change implemented

**None.** No strategy formula, signal rule, Time Wheel calculation, execution default, or risk parameter was changed from this single retrospective report. This preserves current behavior while avoiding an in-sample threshold becoming an unvalidated production rule.

The existing backend controls remain available: maximum positions, per-timeframe limits, cooldown, duplicate-signal protection, daily trade limit, and DEMO-only gating.

## Required next validation

Run a pre-registered forward or walk-forward experiment comparing the existing controls with a same-symbol/same-direction cooldown or cluster cap. Keep symbol, timeframe, costs, and entry/exit rules fixed; select no threshold on the final test period. Promote a control only after it reduces drawdown without materially degrading out-of-sample expectancy across multiple symbols and timeframes.
