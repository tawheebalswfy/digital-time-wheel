# Strategy validation checkpoint — 10 September 2026

## Subsequent fully independent Time Wheel attribution — completed

The shared-exit limitation of the prior entry ablation is addressed by [TIME_WHEEL_FULL_ATTRIBUTION_REPORT.md](TIME_WHEEL_FULL_ATTRIBUTION_REPORT.md). The research-only A–D matrix separates technical/wheel entries from technical/wheel exits, with E retaining the untouched current production baseline. Every variant uses the same retained M1 MT5 dataset, frozen chronological split, 0.40 cost, next-open fill, stop-first assumption, and 30-bar maximum hold.

| Final-test arm | Trades | Net expectancy | Profit factor | Max drawdown |
|---|---:|---:|---:|---:|
| A: technical / technical | 1,134 | -0.5557 | 0.2288 | 630.4270 |
| B: wheel / wheel | 1,323 | -0.5352 | 0.0559 | 708.1200 |
| C: technical / wheel | 1,407 | -0.5129 | 0.0784 | 721.6600 |
| D: wheel / technical | 1,021 | -0.5552 | 0.2957 | 577.4952 |
| E: production baseline | 717 | -0.5966 | 0.3279 | 437.3611 |

Wheel exits lift expectancy per trade under both fixed entry families but increase drawdown and aggregate loss. Wheel entries reduce trade count/drawdown, yet show mixed expectancy effects. The combined production entry filter does not selectively remove worse technical counterfactuals. **Final conclusion: no demonstrated standalone Time Wheel entry, exit, or risk-filter value in this M1 final-test diagnostic.** This is retrospective OOS under the frozen split, not an untouched independent holdout; it contains only six represented UTC dates. Other timeframes were not assessed because the requested common dataset/split is M1-only.

The protocol, full metrics, raw artifacts, and preservation verification are linked in the full attribution report. Thirteen research-specific correctness tests pass; production defaults and the baseline are unchanged.

## Subsequent controlled experiment — completed

The requested Time Wheel entry ablation is complete in [TIME_WHEEL_ABLATION_REPORT.md](TIME_WHEEL_ABLATION_REPORT.md). The verified baseline remains immutable. A and D are identical existing combined controls; B uses technical-only entry decisions, and C uses wheel-only entry decisions. All arms retain the same exits, costs, genuine MT5 dataset, and corrected chronological final-test boundary. A separate validation segment was carved from the earlier development portion; no model was fitted or selected on validation/test outcomes.

| Final-test metric | A: baseline | B: technical entries | C: wheel entries | D: combined |
|---|---:|---:|---:|---:|
| Trades | 717 | 1,059 | 1,011 | 717 |
| Net expectancy | -0.596645 | -0.519797 | -0.526690 | -0.596645 |
| Profit factor | 0.3279 | 0.3675 | 0.3626 | 0.3279 |
| Maximum drawdown | 437.3611 | 550.8327 | 542.1874 | 437.3611 |

Combined minus technical-only net expectancy is **-0.076849 per trade** on the retained final test. The validation difference was +0.070876, so the benefit did not persist. The combined strategy lost less in total because it traded less, despite worse final-test per-trade results. **Evidence is inconclusive for independent out-of-sample predictive value**: this is a diagnostic on a previously inspected period with only six represented test dates, not fresh confirmation of an edge. Shared exits still include wheel-derived levels; this conclusion isolates the entry contribution.

All requested metrics, mean/max MAE and MFE, incremental effects, raw results, reproducibility hashes, and risk-ratio limitations are in the linked experiment report. Eight research tests pass, all baseline parity/preservation checks pass, and the two known WebSocket cleanup failures recurred in the broader 45-test run (43 passed). No platform repair or production-default change was made.

## Earlier baseline validation — retained

The existing MVP and its retained research records survived the restart. The frozen baseline backtest reproduces exactly. Its retained test results do **not** support a profitable strategy: expectancy remains negative even with trading costs removed.

This session added research evidence and documentation. It did not change the platform, strategy formulas, live settings, MT5 profile, database records, or existing tests.

## Evidence and reproduction

- [Machine-readable evidence](validation/20260910T142537938267Z/evidence.json): dataset checks, full-result hashes, database/source fingerprints, split dates, cost sensitivity, and trade breakdowns.
- [Read-only validation runner](../scripts/validate-checkpoint.py).
- Original retained backtest ID: `41ba0ea5-4b9d-4c09-8c2d-7947da46385b`, created `2026-09-10T14:04:43.623330+00:00`.
- M1 dataset ID: `bc6555d92c6833e68b00e9bfb27f4dca516a6998d996349596783e37b6e0b288`.
- M1 content SHA-256: `103c37e49d4e8901dd4963a3db78dd32fa9721ae570b6f473b4834c615cda2a4`.
- Strategy SHA-256: `56ed93b6d6d518e947dc2ff6f4390a6071422ca0eaaea0ff84e888691d32875b`.

From the project root:

```powershell
.\.venv\Scripts\python.exe scripts\validate-checkpoint.py
```

The runner opens SQLite with `mode=ro` and `query_only`, imports the existing research engine without importing the API or initializing MT5, and writes a new timestamped evidence directory. It fails if replay hashes differ or retained rows/source files change during the run. Use an idle database for the preservation check: a running live collector legitimately appends ticks and signals. Logical row fingerprints cover the retained tables; they do not assert identical physical SQLite/WAL file bytes.

## Post-restart state

| Check | Observed result |
|---|---|
| Git status | `fatal: not a git repository`; no `.git` in this working directory or its parent chain. No repository was created or reset. |
| Local services | Ports 8000 and 5173 were not listening. MT5 terminal was absent from the initial process inventory. Services were not started in this research session. |
| Retained SQLite | `PRAGMA quick_check`: `ok`; every logical table fingerprint unchanged during validation. |
| Saved feed | XAUUSD, auto-connect enabled, fixed broker offset +03:00 retained. |
| Saved strategy | Independent baseline, Asia/Aden, anchor 4400, increment 1, threshold 55, 30-bar maximum hold retained. |
| Retained records | 7 datasets, 1 backtest, 0 walk-forward experiments, 14 live signals, 804 ticks, 2 strategy versions. |
| Dataset integrity | All seven content hashes and dataset IDs verified, OHLC/order checks passed, retained raw-to-normalized epoch corrections matched. |
| Signal integrity | All 14 live-signal chain links verified. All 30,059 retained backtest forecast-original hashes verified. |
| Backtest reproduction | Entire train and test payloads match exactly, including forecasts, evaluations, trades, metrics, and equity. |
| Causality spot checks | Full signal matches prefix-only calculation at four real-data indices, including both sides of the split. |
| Existing Python suite | 37/37 passed in 9.361 seconds. The two WebSocket failures noted in the old checkpoint did not recur. |
| Frontend | Transport test, TypeScript check, and production build passed. Existing nonfatal bundle-size warning remains. |

Live bid/ask, wheel animation, WebSocket market delivery, and new MT5 history retrieval were verified in the earlier session, **not reverified after this restart**. Successful offline validation does not substitute for those live checks.

## Dataset and split correction

| Timeframe | Retained genuine-MT5-provenance candles |
|---|---:|
| M1 | 30,170 |
| M5 | 6,041 |
| M15 | 2,013 |
| M30 | 1,006 |
| H1 | 503 |
| H4 | 131 |
| D1 | 21 |

M1 coverage starts at **11 August 2026 14:04 UTC** and ends at **10 September 2026 14:03 UTC**, using an exclusive candle-close endpoint. The saved 80/20 split is index **24,136**, with a **31-bar training purge**. The training simulation ends at 4 September 02:15 UTC. The first test bar opens at **4 September 02:46 UTC**, and the first test forecast is stamped **4 September 02:47 UTC**.

The old `CURRENT_STATUS.md` statement that testing began on 28 August 08:20 UTC was incorrect. The persisted run and actual candle timestamps establish the corrected date; neither the dataset nor the saved split was edited.

The M1 sequence has 22 unrepresented intervals. Several are weekend-length, and one runs from 7 September 18:30 to 22:02 UTC. Session closures versus missing feed history have not been independently classified. No gap was filled or synthesized. The six UTC dates represented in test equity are too little evidence for robust annualized-risk or regime-stability claims.

Hash verification authenticates consistency with the saved local records, not independent broker accuracy. MetaQuotes documents UTC bar times and notes that terminal chart history/max-bars settings bound availability. This project's evidence-backed +03:00 decoding remains specific to its saved connection. [MetaQuotes history documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).

## Frozen baseline results

All P&L figures below are quote-price units for the existing one-unit simulation, not broker-account returns.

| Metric | Original training segment | Original test segment |
|---|---:|---:|
| Trades | 2,890 | 717 |
| Net win rate | 69.13% | 64.71% |
| Net profit factor | 0.4128 | 0.3279 |
| Net expectancy/trade | -0.4619 | -0.5966 |
| Net P&L | -1,334.8012 | -427.7947 |
| Maximum marked drawdown | 1,335.1912 | 437.3611 |
| Average net win | 0.4697 | 0.4499 |
| Average net loss | -2.5484 | -2.5160 |
| Gross expectancy before costs | -0.0619 | -0.1966 |
| Gross profit factor | 0.9104 | 0.7473 |
| Median proposed reward/risk at entry | 0.2389 | 0.2525 |

These are reproduced results from a previously inspected test segment. They are not a new independent out-of-sample discovery.

## What explains the negative result

The engine sorts target candidates by distance and exits at target 1. Its invalidation uses `max(1.5 * ATR, increment)`. In the test trades, mean target distance is **0.7910**, while mean stop distance is **3.0755**. The observed mean net loss is about 5.59 times the mean net win. Holding those observed payoffs constant would require about **84.83%** wins to break even, compared with the measured 64.71%. This is descriptive payoff arithmetic, not a forecast of achievable win rate.

Of 717 test trades, 535 exit at a target and 182 at a stop. **71 target exits have nonpositive net P&L after costs**. Thus the target-hit rate and profitable-trade rate differ. Both BUY and SELL groups have negative expectancy (-0.6492 and -0.5367 respectively); all six entry-date groups also lose money. The JSON contains the full retrospective breakdown, including the first rationale attached to each selected target cluster. Cluster rationales may overlap, so these are not independent source-attribution experiments.

The saved round-trip deduction is spread 0.30 + two slippages of 0.05 + fee 0 = **0.40 per trade**, or **286.80** over the test ledger. However, gross P&L is already **-140.9947**. Reducing costs alone cannot make these same trades profitable at any nonnegative fixed cost.

| Total deduction per trade | Test expectancy | Test profit factor |
|---|---:|---:|
| 0.00 | -0.1966 | 0.7473 |
| 0.20 | -0.3966 | 0.5215 |
| 0.40 — saved setting | -0.5966 | 0.3279 |
| 0.80 | -0.9966 | 0.0909 |

This sensitivity calculation changes deductions on the same saved trades. It does not reprice historical bid/ask paths, change fills, or model variable spread, financing, contract size, or latency.

## Research decision and next checkpoint

Keep the frozen baseline as a reproducible negative control. No candidate was promoted and no live strategy setting was changed. Platform functionality passed the retained-data checks; profitability validation did not pass.

The initially proposed next study is defined in [STRATEGY_VALIDATION_PROTOCOL.md](STRATEGY_VALIDATION_PROTOCOL.md): compare the baseline with one explicitly defined reward/risk eligibility rule. The user's subsequent request prioritized the Time Wheel entry ablation completed above; the payoff study remains unexecuted. The original test data has already influenced this diagnosis and must not be relabeled as fresh validation for a new rule. Repeated strategy selection on the same history creates selection bias; this session does not estimate a probability of backtest overfitting. [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).
