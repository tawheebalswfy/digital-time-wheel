# V9 Forward Shadow Protocol

Prospective start is **2026-09-25T00:00:00+00:00**. This program observes only XAUUSD H1 and D1 bars through MT5 `initialize`, `terminal_info`, `symbol_select`, and `copy_rates_from_pos`; it contains no trade-placement API and creates no positions.

Only the most recently closed candle is eligible to create a signal on a collector run. Earlier bars are used solely as indicator warm-up and are excluded from V9 performance. Signals are append-only and deduplicated by candidate plus entry timestamp. Outcomes are reconciled only after each subsequent candle has closed.

Frozen rules: EMA 12/26, ADX/ATR/RSI 14; ADX >= 25; absolute three-bar slow-EMA slope >= 0.15 ATR; one non-overlapping virtual position per candidate; maximum 30 bars. H1 uses trend continuation with a structural stop and 1.25R target. D1 uses pullback continuation with a structural stop and 1.5R target. These are V9 preregistered shadow exits, not V8-validated exits. Time Wheel attributes state only and never permits or vetoes a signal.
