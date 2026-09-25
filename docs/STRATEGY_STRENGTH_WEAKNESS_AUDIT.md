# Strategy Strength / Weakness Audit

## Evidence and protocol

Only the retained genuine-MT5 XAUUSD datasets are used: M1 30,170 bars, M5 6,041, M15 2,013, M30 1,006, H1 503, H4 131. Data spans 2026-08-11 to 2026-09-10 UTC; the later September forward DEMO period is excluded. The chronological discovery/validation/final-test protocol used fixed causal warmup and 31-bar purges. The final historical segment was previously inspected, so it is retrospective OOS, not a fresh untouched holdout. H4 cannot satisfy the required warmup/purge split and is unavailable; D1 is insufficient.

## Aggregate baseline and timeframe evidence

The all-timeframe XAUUSD final segment baseline from the frozen cooldown protocol had 804 trades, PF 0.491, expectancy -0.535, net -430.39, and max drawdown 439.56. It is negative before any candidate is selected.

| Final segment timeframe | Trades | Net | PF | Reading |
|---|---:|---:|---:|---|
| M1 | 593 | -318.67 | 0.340 | Worst reliable evidence; losses dominate. |
| M5 | 131 | -87.09 | 0.532 | Negative. |
| M15 | 39 | -20.71 | 0.721 | Negative; small sample. |
| M30 | 25 | -26.74 | 0.637 | Negative; small sample. |
| H1 | 16 | +22.82 | 1.782 | Positive but far too small for a strength claim. |
| H4 | — | — | — | Insufficient causal split. |

## Entry and Time Wheel attribution

The isolated M1 final-test experiment compares the full current production logic with technical-only and Wheel-only entries under identical costs and exits. Production/full: 717 trades, PF 0.3279, expectancy -0.5966, net -427.79, drawdown 437.36. Technical-only entry: PF 0.3675, expectancy -0.5198. Wheel-only entry: PF 0.3626, expectancy -0.5267.

The combined Time Wheel entry had a -0.0768 expectancy delta versus technical-only entry in final test. Validation had a +0.0709 delta, which did not persist. Therefore Time Wheel entry has **no demonstrated incremental predictive value**. Isolated Wheel exits improved per-trade expectancy in fixed-entry comparisons, but worsened aggregate P/L and drawdown; they are not a validated exit improvement.

## Technical-filter contribution

The available ablation is family-level, not individual-indicator-level. Existing technical logic without Wheel entry had better final M1 PF/expectancy than full combined entry, but remained materially negative. It therefore supplies comparatively useful information, not a positive standalone strategy. There is no evidence to remove or add individual EMA/RSI/ADX/ATR/MACD/Bollinger filters; that unrun granular ablation is explicitly not inferred.

## Entry, exit, and geometry verdicts

Five-minute forward directional evidence for the full M1 strategy was -0.4759 bp per actionable signal in final test; technical-only was +0.1115 bp. This supports an **entry-quality verdict of no demonstrated full-system edge**, with technical-only direction less bad but not a deployable positive result.

Exit quality is also weak. The engine's final M1 production average winner was 0.4499 against average loser -2.5160 (payoff about 0.18), and the forward DEMO M15 run independently showed planned R:R about 0.27. The repeated high-win-rate/negative-expectancy pattern identifies asymmetric loss geometry as the dominant measurable failure. MFE/MAE evidence does not support changing targets yet because diagnostic R variants have not been frozen on independent data.

## Holding time and direction

Frozen all-timeframe holdout attribution for the predeclared `cap_1` research variant: <1m had 384 trades, PF 1.727, expectancy +0.281; 1–5m had PF 0.220, expectancy -0.999; 5–15m PF 0.131, expectancy -2.019; 15–60m PF 0.226, expectancy -2.379; >60m PF 0.065, expectancy -13.633. This corroborates the forward DEMO observation that long holds are harmful, but it does not show that a time exit is causal; it may be a marker of failed trades.

Final aggregate baseline BUY expectancy was -0.751 and SELL -0.326. Both are negative; SELL is less negative in this segment. In validation both were close and negative (BUY -0.527, SELL -0.570), so a directional production filter is not supported.

## Regime/session/feature limits

The existing frozen artifacts establish structure/technical/Wheel attribution but do not contain pre-registered, independent regime-by-ADX/ATR/session threshold selection. Given only roughly one month and six final-test dates, any newly discovered hour, ADX, RSI, or ATR cutoff would be data-mined. No harmful hour or regime is promoted. A future study may use descriptive grouped statistics on discovery, freeze one rule, then test once on new unseen MT5 history.

## Ranked strengths and weaknesses

Strengths (with limits): (1) M1 sub-minute outcomes are positive in the risk-filter study; (2) H1 final segment is positive but only 16 trades; (3) Wheel entries reduce exposure/drawdown in isolated comparisons; (4) technical-only entry is less negative than full combined M1; (5) durable signal identity enables future clean attribution.

Weaknesses: (1) negative PF/expectancy across all adequately sampled timeframes; (2) loss magnitude overwhelms frequent small wins; (3) M1 is the clearest negative contributor; (4) longer holding buckets are sharply negative; (5) Wheel entry did not improve final-test expectancy and is not selective enough as a bad-trade filter.

## Conclusion

There is no production-positive edge established in the retained data. Time Wheel concept preservation is appropriate for continued measurement, but evidence does not justify making it a stronger entry gate, weakening technical confirmation, changing timeframe enablement, or changing risk geometry in production.
