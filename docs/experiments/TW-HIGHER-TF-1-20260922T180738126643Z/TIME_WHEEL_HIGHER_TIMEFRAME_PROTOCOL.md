# Controlled experiment TW-HIGHER-TF-1

Frozen before results. This extends TW-FULL-EXIT-1 to the existing genuine MT5 M15, H1, and H4 datasets only. Production defaults, baseline records, and the M1 experiment are unchanged.

## Inherited isolated logic

Use the exact T/W entry and T/W exit families from [TIME_WHEEL_FULL_ATTRIBUTION_PROTOCOL.md](TIME_WHEEL_FULL_ATTRIBUTION_PROTOCOL.md): A=T/T, B=W/W, C=T/W, D=W/T, E=current production logic. Wheel-only entries use Time Wheel state, geometry, and gates only; technical-only exits use confirmed support/resistance, swings, and Fibonacci only; wheel-only exits use wheel levels and angular projections only. No cross-family exit levels, ATR stops/targets, added indicators, or parameter search.

## Data and split

| Timeframe | Dataset ID | Candles | Chronological evaluated intervals |
|---|---|---:|---|
| M15 | `9b42086946a9ceab1a8fde7c889d931cf6fddbde30e24436272c988f49796612` | 2,013 | train [78,1176), validation [1207,1579), test [1610,2013) |
| H1 | `aa9dd4bc95536d041bec47fbbec7e6b317a0f1db6309c84629cbac792470ef43` | 503 | train [78,270), validation [301,371), test [402,503) |
| H4 | `4dda02867ad6c17b1956a685009b3ac86294c9e2c9af2778dab1560be582f03e` | 131 | not runnable under frozen rules |

The M15/H1 indices use the same 60/20/20 chronological structure, fixed 31-bar purges, and existing 78-bar causal warmup as the M1 full attribution. The 31-bar purge and 30-bar maximum holding period are measured in each timeframe's bars, exactly as existing backtests do. Entry is at the immediate next timeframe-bar open; stops/targets use that bar's high/low and stop-first ambiguity; costs remain 0.40 quote-price units per trade.

H4 is an insufficiency finding, not a failed model: its 60% boundary is index 78, which equals the existing warmup. The training window would end at index 47 after its 31-bar purge, before any causal trade can be evaluated. Reducing warmup, purge, or holding horizon would change the frozen methodology, so no H4 result will be fabricated.

## Final conclusion and ranking

Training and validation are reported without selection. Final assessment uses only each timeframe's test interval. The test samples are short, especially H1 (101 bars) and H4 (unavailable); results are retrospective out-of-sample under this split but not untouched independent holdouts. Rank M1/M15/H1/H4 by consistency and direction of final-test wheel entry/exit contribution, placing unavailable/insufficient evidence last. Do not claim timeframe superiority from a single positive metric or from training/validation.
