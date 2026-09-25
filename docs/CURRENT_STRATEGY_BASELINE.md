# Current Strategy Baseline (Frozen for Research)

## Scope

This records the production strategy and execution defaults as inspected on 2026-09-22. It is a descriptive freeze for research; no strategy or execution setting was changed. Auto trading remains disabled.

## Time Wheel and entry decision

The strategy derives a Time Wheel state from price and timestamp using the configured continuous time model A, anchor price 4400, increment 1, 360-degree price range, clockwise direction, zero decimal wheel angle, 5-degree tolerance, and the configured harmonic set (0, 30, 45, 60, 90, 120, 135, 180, 225, 240, 270, 300, 315, 360). Enabled Wheel gates are `price_time`, `all_369`, and `angular`; `enable_369` is true and Gann is disabled.

The Wheel supplies numerical direction, geometry, and gate components. A final BUY/SELL requires all of the following:

1. Wheel numerical direction is non-neutral.
2. The weighted BUY/SELL score agrees with that Wheel direction.
3. At least one existing technical confirmation (structure, support/resistance, momentum, or Fibonacci) agrees with Wheel direction.
4. The winning score is at least the fixed threshold 55.

The weights are Wheel 30, geometry 20, structure 15, support/resistance 10, momentum 10, Fibonacci 5, volatility 5, and gates 5. Ties and any failed condition produce NEUTRAL.

## Existing technical confirmations

Indicators are EMA(12/26), SMA(20), RSI(14), ADX/+DI/-DI(14), ATR(14), MACD histogram (12/26/9), and Bollinger Bands(20, 2). Momentum votes are EMA fast/slow, price/SMA, RSI above 55 or below 45, MACD histogram sign, ADX>20 DI sign, and price/Bollinger midline sign. Structure is delayed-confirmed swing structure using strength 3: HH+HL is bullish, LH+LL bearish, else ranging. Support/resistance are trailing 20-bar extrema. Fibonacci is based only on confirmed swings (or explicitly timestamped manual anchors).

## Risk, exits, and simulation assumptions

The trade entry is next-bar open after a closed-bar signal. The production invalidation is `entry - direction × max(1.5 × ATR, increment)`. Eligible target candidates are Wheel levels, angular harmonics, confirmed support/resistance/swing levels, Fibonacci levels, ATR multiples 1/2/3, and gated digital levels; candidates are clustered within 0.1 ATR and the nearest eligible cluster becomes target 1. The live executor preserves this strategy invalidation and target 1.

Research simulation uses one non-overlapping position, target/stop evaluation on each bar, stop-first resolution when both are touched, adverse stop-gap fill, no substituted overnight/weekend entry, a 30-bar maximum hold, and cost of spread 0.30 + two 0.05 slippages + fee 0.00 quote-price units. It does not simulate broker financing, leverage, lot sizing, or currency conversion.

## Timeframes and execution controls

The engine supports M1, M5, M15, M30, H1, H4, D1; current saved execution selection is M5/M15/M30/H1. Duplicate protection is one durable execution per `signal_id`; the execution table has `signal_id UNIQUE`. Live controls are fixed lot 0.01, maximum 5 owned positions, maximum 1 per timeframe, 100 trades/day, no cooldown, no maximum-spread filter, opposite directions blocked, and external positions block new execution. There is no explicit session exclusion or separate volatility guard beyond the existing ATR component/validity checks.

## Freeze statement

All subsequent audit comparisons retain the above as baseline. Research variants must be isolated and must not change production defaults without explicit approval.
