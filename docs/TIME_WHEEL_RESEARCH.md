# Independent Time Wheel research specification

This is an independent, falsifiable research implementation. None of the following formulas is attributed to the recorded product. The video evidence report is the primary record of what was actually observed.

## KNOWN MATHEMATICS

- For a nonnegative integer n: digital root is 0 for n=0, otherwise 1+(n-1) mod 9. Negative values use absolute magnitude. Decimal prices are quantized to configurable precision (default 2) before reduction of the resulting integer. Integer-only reduction is a separate selectable policy. Trailing zeros are harmless; rounding across an integer boundary is not.
- Date digits use YYYYMMDD in an explicit timezone (UTC default). Time digits use HHMMSS. Timezone is stored in every strategy version; historical timestamps remain UTC.
- Angle normalization is modulo 360, sector index floor(angle/10), display number index+1. Root labels repeat 1–9 over displayed sectors. Angular root uses a configurable quantization (integer degree default). Rounded degree displays must never feed calculations.
- Circular separation is min(|a-b| mod 360,360-(|a-b| mod 360)). Directed separation (price-time) mod 360 distinguishes 90 from 270. Harmonics 0 and 360 are the same geometry, though both may appear in the input list.
- Time cycles: angle = 360 * ((elapsed_seconds mod cycle_seconds)/cycle_seconds), with cycles 86400,43200,21600,10800,3600,1800,900,300,60. Elapsed seconds use local wall-clock time since midnight unless an explicit UTC anchor time is supplied. Anchored cycles use elapsed absolute UTC seconds. DST changes therefore affect wall-clock and anchored models differently.
- Fibonacci percentages are ratios used to project a chosen interval; their existence does not imply forecasting ability.

## TIME NUMEROLOGY MODELS

| Model | Definition | Caveat |
|---|---|---|
| A | root(HH+MM+SS) | Digit-sum congruence makes A and B identical |
| B | root(all HHMMSS digits) | Not an independent hypothesis from A |
| C | root(seconds since midnight) | Different units imply different root patterns |
| D | root(whole minutes since midnight) | Discards seconds |
| E | root(quantized selected cycle angle) | Angle root policy is explicit |
| F | root(quantized 12-hour angle) | Same as E if selected cycle is 12h |
| G | root(quantized 24-hour angle) | Same as E if selected cycle is 24h |
| H | root(custom arithmetic expression) | Safe AST evaluator; h,m,s,p,date and elapsed only; bounded arithmetic, no Python eval |

## PRICE MAPPINGS — MATHEMATICS, NOT ESTABLISHED SIGNALS

All receive direction sign d (+1 clockwise, -1 counterclockwise) and starting rotation r. Final angle=(r+d*raw) mod 360.

| Model | Raw angle | Units |
|---|---|---|
| Linear modulo | price / price_range * 360 | price_range is one full revolution |
| 36-level modulo | floor(price/increment) mod 36 * 10 | Discrete absolute price bins |
| Square root | (sqrt(price)-sqrt(anchor_price))*180 | Positive prices and anchors only; square-root units per half turn |
| Increment | price/increment*10 | Continuous absolute price increments |
| Anchor | (price-anchor_price)/increment*10 | Continuous relative increments |

Inverse levels enumerate nearby revolutions around current price; modulo angles alone cannot identify a unique absolute price. Square-root inverse projections require a nonnegative transformed root. Display increments and visual rotation are not evidence of causal forecasts.

## EXPERIMENTAL HYPOTHESES

1. Small distance to selected harmonics may identify event times. Tolerance defaults to 5 degrees. Strength levels count closeness and enabled root equalities. A harmonic has no proven directional meaning.
2. The explicit experimental directional convention uses sin(directed price-time angle) to assign a numerical tilt. Gates modulate eligibility; they do not establish a market edge. Exact conjunction/opposition has no sine direction. All directional assumptions are visible in score explanations and strategy versions.
3. Digital gates independently test price/time equality, price/angle equality, time/angle equality, complementary roots (sum=9), sum root in 3/6/9, all participating roots in 3/6/9, repeated price digits and simultaneous cycle boundaries. Disabled gates do not contribute.
4. Technical indicators confirm numerical direction. Combined BUY/SELL requires a non-neutral wheel signal and at least one confirming technical component. Default weights are 30,20,15,10,10,5,5,5 for wheel,geometry,structure,support_resistance,momentum,fibonacci,volatility,gates. Scores are normalized evidence weights, **not calibrated probabilities**.
5. Targets are ranked, directionally valid candidates from inverse wheel levels, enabled angular projections, past confirmed swings/support/resistance, Fibonacci extensions, ATR multiples, optional Gann projections and gate-qualified wheel levels. Each target stores formula, inputs, source and distance. No special market target is embedded in this engine.
6. The 3/6/9 module is a conditional outcome study, compared against unconditional outcomes with sample counts and uncertainty. Research assistant statements derive only from measured results.

## CAUSALITY AND VALIDATION

- Only closed bars generate permanent signals. Live ticks animate the wheel, but do not rewrite closed-bar predictions.
- A pivot with left/right strength k becomes available k bars after the pivot. Multi-timeframe resampling includes only completed intervals and rejects incomplete aggregates.
- Signal at bar close; simulated execution at next bar open. Fees, full spread and slippage are configurable in quote-price units. Stop wins if stop and target are both touched in one bar. Gaps beyond stop fill at the adverse open. Nonoverlapping trades are the default.
- Walk-forward selection sees training only, purges the holding horizon from training boundaries and freezes the winner for the next test segment. Results show training/test separately. No global optimization on held-out outcomes.
- Forward horizons use wall-clock durations, never positional row counts. Missing exact endpoint bars are reported unavailable. No weekend-gap substitution.
- Sharpe/Sortino use daily marked equity returns; assumptions and undefined denominators are explicit. Backtests are unlevered one-unit quote-P&L studies, not broker-specific lot-return simulations.
- Synthetic fixtures may test correctness only. They cannot establish predictive value. Real-data evidence requires documented provider, period, timezone, content hash, strategy hash, cost assumptions, sample size and OOS results.
- Strategy selection across many parameters creates multiple-testing risk. OOS degradation warnings are heuristic, not a statistical guarantee against overfitting.

## Source documentation checked during implementation

- [MetaTrader Python API](https://www.mql5.com/en/docs/python_metatrader5)
- [MT5 UTC bar semantics](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py)
- [Lightweight Charts v5 migration](https://tradingview.github.io/lightweight-charts/docs/migrations/from-v4-to-v5)

## Important user-supplied arithmetic example

14:32:15 maps to 218.0625 degrees on a 24-hour cycle. Its integer-degree digital root is root(218)=2. Applying two-decimal quantization instead gives root(21806)=8. The app exposes this choice rather than treating inconsistent conventions as interchangeable.
