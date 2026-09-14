# Full Time Wheel attribution — TW-FULL-EXIT-1

**Final-test conclusion:** the Time Wheel has **no demonstrated standalone value** in this M1 diagnostic. Wheel exits improve per-trade expectancy under both fixed entry families, but worsen total P&L and drawdown. Wheel entries reduce exposure and drawdown, while their per-trade expectancy effect is mixed and negligible-to-negative. The production baseline remains the least-loss / lowest-drawdown reference here, but it is still negative. No production defaults changed.

## Design

This fully separates the exit families that were shared in the prior experiment. A–D use the same MT5 XAUUSD M1 dataset, chronological split, cost of 0.40, next-open entry, stop-first ambiguity rule, adverse stop-gap fill, one-position constraint, and 30-bar maximum hold. E is the immutable current production baseline. The [frozen protocol](TIME_WHEEL_FULL_ATTRIBUTION_PROTOCOL.md) defines every rule before results.

- **T entry:** structure, support/resistance, momentum, and Fibonacci only.
- **W entry:** Time Wheel state, geometry, and gates only. No ATR/volatility technical indicator is used.
- **T exit:** confirmed support/resistance, swings, and Fibonacci only; no wheel, harmonics, gates, Gann, or ATR.
- **W exit:** wheel levels and angular harmonic projections only; no technical field, indicator, swing, Fibonacci, support/resistance, or ATR.

The test starts at the corrected 4 September 2026 02:46 UTC bar. Train `[78,18071)`, validation `[18102,24105)`, and test `[24136,30170)` preserve the prior 31-bar purges. The final conclusion below uses test only; train/validation are retained in the artifact for transparency. This is retrospective OOS relative to the frozen split, but the period was inspected in prior work and has only six represented UTC dates.

## Final-test metrics

| Metric | A: T/T | B: W/W | C: T/W | D: W/T | E: production |
|---|---:|---:|---:|---:|---:|
| Trades | 1,134 | 1,323 | 1,407 | 1,021 | 717 |
| Win rate | 19.31% | 13.68% | 16.84% | 21.84% | 64.71% |
| Average winner | 0.8536 | 0.2317 | 0.2589 | 1.0676 | 0.4499 |
| Average loser | -0.8930 | -0.6568 | -0.6693 | -1.0087 | -2.5160 |
| Profit factor | 0.2288 | 0.0559 | 0.0784 | 0.2957 | 0.3279 |
| Gross expectancy | -0.1557 | -0.1352 | -0.1129 | -0.1552 | -0.1966 |
| Net expectancy | -0.5557 | -0.5352 | -0.5129 | -0.5552 | -0.5966 |
| Net P&L | -630.1691 | -708.1200 | -721.6600 | -566.8954 | -427.7947 |
| Max drawdown | 630.4270 | 708.1200 | 721.6600 | 577.4952 | 437.3611 |
| Mean MAE | 1.1911 | 1.0418 | 0.9965 | 1.2637 | 1.6168 |
| Max MAE | 26.2600 | 26.9500 | 13.3700 | 26.9500 | 26.9500 |
| Mean MFE | 1.0939 | 1.0431 | 1.0579 | 1.2360 | 1.3676 |
| Max MFE | 10.9700 | 7.2200 | 10.9700 | 26.2600 | 10.0300 |
| Average holding minutes | 1.5864 | 1.0695 | 1.0796 | 1.7816 | 1.2204 |

Sharpe and Sortino are retained in the compressed full results but omitted from interpretation: six dependent daily observations are not statistically meaningful for annualized ratios. MAE/MFE are full-bar excursions using the inherited exit-bar caveat.

## Attribution from final test only

| Fixed comparison | Net expectancy delta | Net P&L delta | Drawdown delta | Reading |
|---|---:|---:|---:|---|
| W entry vs T entry, technical exits: D − A | 0.0005 | 63.2737 | -52.9318 | Near-zero per-trade gain; fewer trades and lower drawdown. |
| W entry vs T entry, wheel exits: B − C | -0.0223 | 13.5400 | -13.5400 | Worse expectancy; fewer trades and lower drawdown. |
| W exit vs T exit, technical entries: C − A | 0.0428 | -91.4909 | 91.2330 | Better expectancy per trade, worse aggregate loss/drawdown. |
| W exit vs T exit, wheel entries: B − D | 0.0200 | -141.2246 | 130.6248 | Better expectancy per trade, worse aggregate loss/drawdown. |

### Answers to the requested attribution questions

1. **Does the Time Wheel improve entries?** No consistent final-test evidence. It adds +0.0005 expectancy with technical exits but −0.0223 with wheel exits.
2. **Does it improve exits?** Per trade, yes in both fixed-entry comparisons (+0.0428 and +0.0200). Aggregate P&L and drawdown worsen because wheel exits increase the number of trades.
3. **Does it reduce drawdown?** Wheel entries do in both comparisons (−52.93 and −13.54). Wheel exits do not (+91.23 and +130.62).
4. **Does it filter bad trades?** Not convincingly. The combined entry accepted 379 technical counterfactuals with −0.7513 expectancy and filtered 1,968 with −0.5055 expectancy. It removed many losing trades, but retained an even worse per-opportunity subset.
5. **Does it remove profitable trades too aggressively?** It removed 428 profitable technical counterfactuals alongside 1,540 losers; its filtered set had a 21.75% profitable rate versus 19.00% for accepted same-direction opportunities. That is evidence of indiscriminate filtering in this sample, not clean bad-trade removal.
6. **Is its value stronger on certain timeframes?** Not assessed. The required common dataset/split is M1-only; higher-timeframe datasets cannot be used to support a claim here.

## Required separate statements

- **Time Wheel entry value:** inconclusive and not positive on final test; risk-filter behavior lowers exposure/drawdown but does not consistently improve expectancy.
- **Time Wheel exit value:** improves expectancy per trade in this sample, but has negative aggregate risk/P&L consequences under both entry families.
- **Time Wheel risk-filter value:** entries reduce drawdown, while exits increase it. The entry filter does not selectively remove worse technical opportunities in the evaluated counterfactuals.

## Reproducibility

All A–D signals, levels, rejects, trades, equity curves, and full raw metrics are in compressed artifacts next to [comparison.json](comparison.json). Source and SQLite logical fingerprints were rechecked after the run; production defaults and stored records are unchanged. Thirteen research tests passed. Re-run with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_research*.py" -q
.\.venv\Scripts\python.exe scripts\research_full_attribution.py
```
