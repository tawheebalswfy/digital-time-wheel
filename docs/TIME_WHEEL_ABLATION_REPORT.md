# Time Wheel contribution — TW-ENTRY-1 diagnostic

**Conclusion: evidence is inconclusive for independent out-of-sample predictive value.** On the retained final-test segment, adding the current Time Wheel entry logic makes net expectancy **worse by 0.0768 quote-price units per trade**. The validation expectancy increment was +0.0709, so its favorable direction did not persist in the final test. The original final period was already inspected, and its small number of represented dates limits inference. No production setting was changed.

## Experiment scope

This user-requested entry-family ablation superseded the queued payoff-eligibility experiment for this session. The only experimental factor is entry logic. All arms use the same genuine MT5 M1 data, costs, target/stop construction, next-open execution, holding period, and evaluation rules. **B means technical-only entries; C means wheel-only entries. Shared exits still contain both wheel-derived and technical levels.** Thus this experiment cannot establish the contribution of wheel-derived exits or compare entirely wheel-free versus entirely technical-free systems.

A and D are exactly the same current combined strategy. D references A’s result files; it is a duplicate control, not another independent experiment. B uses the existing technical vote weights normalized over 40 active points. C uses existing wheel-dependent vote weights normalized over 60 active points and removes technical directional confirmation. Both retain threshold 55. Active-family normalization avoids mechanically disabling B, whose votes otherwise cannot reach 55 out of 100. No parameter search, target change, cost search, indicator addition, or win-rate optimization was performed.

Rules were archived before new-arm results in the [frozen protocol](experiments/TW-ENTRY-1-20260910T143913330642Z/TIME_WHEEL_ABLATION_PROTOCOL.md) and [registration](experiments/TW-ENTRY-1-20260910T143913330642Z/registration.json).

## Data and chronological split

Dataset: `bc6555d92c6833e68b00e9bfb27f4dca516a6998d996349596783e37b6e0b288`; 30,170 retained MT5 XAUUSD M1 candles. Content SHA-256: `103c37e49d4e8901dd4963a3db78dd32fa9721ae570b6f473b4834c615cda2a4`. Frozen baseline strategy SHA-256: `56ed93b6d6d518e947dc2ff6f4390a6071422ca0eaaea0ff84e888691d32875b`.

The original 80% final-test boundary is unchanged. The earlier checkpoint had no validation set; this experiment subdivides its development portion into train and validation, with 31-bar purges. It does not rewrite the original stored backtest. All portfolios start flat at 10,000 quote units; prior history is used only for causal feature warmup. Rules were frozen before train, validation, and test; no fitting or selection occurred between segments.

| Segment | Bar indices (end exclusive) | First signal UTC | Last valuation UTC |
|---|---|---|---|
| train | [78, 18071) | 2026-08-11T15:23:00+00:00 | 2026-08-28T16:32:00+00:00 |
| validation | [18102, 24105) | 2026-08-28T17:04:00+00:00 | 2026-09-04T02:15:00+00:00 |
| test | [24136, 30170) | 2026-09-04T02:47:00+00:00 | 2026-09-10T14:03:00+00:00 |

The first final-test bar opens **4 September 2026 02:46 UTC**; its signal is stamped **02:47 UTC**. Both validation and test are retrospective diagnostics on already available history, not newly untouched holdouts. The saved data gaps and broker-offset limitations from the baseline validation remain; no candles were generated or filled.

## Final-test comparison

| Metric | A: baseline | B: technical entries | C: wheel entries | D: combined |
|---|---:|---:|---:|---:|
| Trades | 717 | 1,059 | 1,011 | 717 |
| Net win rate | 64.71% | 66.01% | 65.48% | 64.71% |
| Average net win | 0.4499 | 0.4575 | 0.4575 | 0.4499 |
| Average net loss | -2.5160 | -2.4175 | -2.3936 | -2.5160 |
| Net profit factor | 0.3279 | 0.3675 | 0.3626 | 0.3279 |
| Gross expectancy / trade | -0.1966 | -0.1198 | -0.1267 | -0.1966 |
| Net expectancy / trade | -0.5966 | -0.5198 | -0.5267 | -0.5966 |
| Net P&L | -427.7947 | -550.4648 | -532.4832 | -427.7947 |
| Maximum marked drawdown | 437.3611 | 550.8327 | 542.1874 | 437.3611 |
| Maximum drawdown % | 4.3716 | 5.5081 | 5.4218 | 4.3716 |
| Mean MAE | 1.6168 | 1.5363 | 1.5558 | 1.6168 |
| Maximum MAE | 26.9500 | 14.8500 | 26.9500 | 26.9500 |
| Mean MFE | 1.3676 | 1.3775 | 1.4172 | 1.3676 |
| Maximum MFE | 10.0300 | 10.9700 | 9.9900 | 10.0300 |
| Sharpe | N/A | N/A | N/A | N/A |
| Sortino | N/A | N/A | N/A | N/A |
| Represented UTC dates | 6 | 6 | 6 | 6 |

All P&L, expectancy, drawdown, MAE, and MFE amounts are quote-price units for one unit of exposure, not broker-account returns. Win rate, mean win/loss, and profit factor are after the identical 0.40 round-trip deduction. MAE/MFE use the existing full-bar convention, including the exit bar whose intrabar order is unknown. The engine’s raw Sharpe/Sortino values are retained in full result files but are withheld here because this short, dependent daily sample cannot support meaningful annualized-ratio interpretation.

## Incremental contribution: combined minus technical-only

Positive expectancy/P&L differences favor D. Positive drawdown or MAE differences indicate more adverse movement. These are differences of strategy means with different entry sets and occupancy, not paired trades.

| Metric delta (D − B) | Train | Validation | Final test |
|---|---:|---:|---:|
| Trades | -967 | -349 | -342 |
| Net win rate | 0.06 pp | 2.60 pp | -1.29 pp |
| Average net win | 0.0005 | -0.0007 | -0.0077 |
| Average net loss | -0.0709 | -0.0431 | -0.0985 |
| Net profit factor | -0.0103 | 0.0421 | -0.0396 |
| Gross expectancy / trade | -0.0200 | 0.0709 | -0.0768 |
| Net expectancy / trade | -0.0200 | 0.0709 | -0.0768 |
| Net P&L | 382.8385 | 240.8218 | 122.6700 |
| Maximum marked drawdown | -394.8488 | -249.4193 | -113.4716 |
| Maximum drawdown % | -3.9441 | -2.4894 | -1.1366 |
| Mean MAE | 0.0317 | -0.0839 | 0.0805 |
| Maximum MAE | 23.0600 | -11.3300 | 12.1000 |
| Mean MFE | -0.0176 | 0.0318 | -0.0099 |
| Maximum MFE | -2.1800 | 3.8700 | -0.9400 |

The final-test exploratory 95% paired-block resampling interval for the net-expectancy difference is **[-0.1957, -0.0034]**. This uses the frozen two-date circular blocks, 10,000 draws, and seed 20260910. Trade P&L/counts are attributed to entry dates for the expectancy estimate; the same sampled dates are used for both arms. Only six represented test dates and previously inspected history prevent a reliable independent-edge significance claim. Block resampling preserves local dependence within blocks but does not remove dependence at longer scales or solve data reuse. [CMU time-series bootstrap notes](https://stat.cmu.edu/~cshalizi/dst/20/lectures/16/lecture-16.html).

### Common-date marked P&L

| UTC date | B: technical entries | D: combined | D − B |
|---|---:|---:|---:|
| 2026-09-04 | -91.3207 | -105.1030 | -13.7824 |
| 2026-09-06 | -9.9372 | -7.8176 | 2.1196 |
| 2026-09-07 | -125.9682 | -86.3150 | 39.6532 |
| 2026-09-08 | -118.4375 | -92.2615 | 26.1759 |
| 2026-09-09 | -98.8861 | -64.7557 | 34.1304 |
| 2026-09-10 | -105.9152 | -71.5420 | 34.3732 |

A strategy that takes fewer losing trades can improve total P&L while worsening expectancy per trade. The two measures must be considered separately; neither is optimized here.

## Fixed five-minute directional diagnostic

One predeclared 300-second close-to-close horizon, exact endpoints only, with outcomes stored separately from original forecasts. The common-opportunity mean assigns zero to neutral decisions; actionable-only means condition on each arm’s own signals. These overlapping outcomes are descriptive, not a tradable P&L series or independent samples.

| Final-test arm | Available opportunities | Actionable opportunities | Mean signed bps / common opportunity | Mean signed bps / actionable signal |
|---|---:|---:|---:|---:|
| A | 6009 | 1242 | -0.0984 | -0.4759 |
| B | 6009 | 2662 | 0.0494 | 0.1115 |
| C | 6009 | 1965 | -0.0330 | -0.1010 |
| D | 6009 | 1242 | -0.0984 | -0.4759 |

D − B on the same final-test opportunity grid: **-0.1478 basis points per opportunity**. This supplemental metric removes target/stop mechanics from the outcome calculation, while still reflecting different entry/abstention decisions. No other horizon was tried.

## Training comparison

| Metric | A: baseline | B: technical entries | C: wheel entries | D: combined |
|---|---:|---:|---:|---:|
| Trades | 2,180 | 3,147 | 2,991 | 2,180 |
| Net win rate | 68.67% | 68.61% | 67.27% | 68.67% |
| Average net win | 0.4590 | 0.4585 | 0.4507 | 0.4590 |
| Average net loss | -2.4778 | -2.4069 | -2.5695 | -2.4778 |
| Net profit factor | 0.4060 | 0.4163 | 0.3605 | 0.4060 |
| Gross expectancy / trade | -0.0611 | -0.0411 | -0.1378 | -0.0611 |
| Net expectancy / trade | -0.4611 | -0.4411 | -0.5378 | -0.4611 |
| Net P&L | -1005.2052 | -1388.0437 | -1608.6768 | -1005.2052 |
| Maximum marked drawdown | 1018.2501 | 1413.0989 | 1615.7168 | 1018.2501 |
| Maximum drawdown % | 10.1821 | 14.1262 | 16.1565 | 10.1821 |
| Mean MAE | 1.6162 | 1.5845 | 1.6857 | 1.6162 |
| Maximum MAE | 45.4200 | 22.3600 | 45.4200 | 45.4200 |
| Mean MFE | 1.4906 | 1.5082 | 1.4770 | 1.4906 |
| Maximum MFE | 13.5800 | 15.7600 | 15.5200 | 13.5800 |
| Sharpe | N/A | N/A | N/A | N/A |
| Sortino | N/A | N/A | N/A | N/A |
| Represented UTC dates | 16 | 16 | 16 | 16 |

## Validation comparison

| Metric | A: baseline | B: technical entries | C: wheel entries | D: combined |
|---|---:|---:|---:|---:|
| Trades | 708 | 1,057 | 974 | 708 |
| Net win rate | 70.34% | 67.74% | 70.74% | 70.34% |
| Average net win | 0.4973 | 0.4980 | 0.4808 | 0.4973 |
| Average net loss | -2.7821 | -2.7390 | -2.7832 | -2.7821 |
| Net profit factor | 0.4239 | 0.3818 | 0.4177 | 0.4239 |
| Gross expectancy / trade | -0.0754 | -0.1463 | -0.0742 | -0.0754 |
| Net expectancy / trade | -0.4754 | -0.5463 | -0.4742 | -0.4754 |
| Net P&L | -336.5660 | -577.3878 | -461.9194 | -336.5660 |
| Maximum marked drawdown | 336.5660 | 585.9853 | 466.3862 | 336.5660 |
| Maximum drawdown % | 3.3657 | 5.8551 | 4.6625 | 3.3657 |
| Mean MAE | 1.6968 | 1.7806 | 1.7270 | 1.6968 |
| Maximum MAE | 12.1600 | 23.4900 | 20.8500 | 12.1600 |
| Mean MFE | 1.5782 | 1.5464 | 1.5446 | 1.5782 |
| Maximum MFE | 12.1500 | 8.2800 | 12.1500 | 12.1500 |
| Sharpe | N/A | N/A | N/A | N/A |
| Sortino | N/A | N/A | N/A | N/A |
| Represented UTC dates | 7 | 7 | 7 | 7 |

## Verification and reproducibility

- The isolated simulator reproduced the original full-training result and original final-test result exactly after excluding the separately archived forecast arrays. All 6,033 original final-test forecast hashes matched.
- A = D in every segment. All 18 real-data prefix checks passed across the three active entry families and six timestamps.
- Independent artifact verification checked 90,081 original forecast hashes and 13,844 trades, including costs, interval bounds, target/stop consistency, nonoverlap, equity reconciliation, and marked drawdown.
- All recorded database-table fingerprints and existing source fingerprints remain unchanged. Production defaults, data, original backtest records, and frontend were not modified.
- Eight new research correctness tests passed. Full regression: 43/45 passed; the two previously documented WebSocket cleanup tests recurred (one CancelledError, one active-count failure). No transport fix was included in this diagnostic.

[Full comparison JSON](experiments/TW-ENTRY-1-20260910T143913330642Z/comparison.json) · [Metrics CSV](experiments/TW-ENTRY-1-20260910T143913330642Z/metrics.csv) · [Artifact hashes](experiments/TW-ENTRY-1-20260910T143913330642Z/artifact_hashes.json) · [Independent verification](experiments/TW-ENTRY-1-20260910T143913330642Z/verification.json). Each active arm/segment also has `*-result.json.gz` with trades, equity, raw metrics, and daily attribution, plus `*-signals.jsonl.gz` with every immutable original forecast, its hash, and separate five-minute outcome. The frozen protocol, runner, helper, tests, environment versions, and code hashes are archived alongside them.

Reproduce from the project root (creates a new result directory):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_research_ablation.py -v
.\.venv\Scripts\python.exe scriptsesearch_ablation.py
.\.venv\Scripts\python.exe scriptseport_ablation.py <new-result-directory>
```

No arm is promoted. This completes the diagnostic requested for the retained dataset; independent predictive value would require a separately frozen evaluation on genuinely uninspected data. Repeating selection on the same historical sample cannot manufacture a fresh holdout. [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).
