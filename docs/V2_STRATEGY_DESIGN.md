# DIGITAL_TIME_WHEEL_V2_RESEARCH Design

V1_BASELINE is frozen in `CURRENT_STRATEGY_BASELINE.md`; no V1 code, profile, defaults, or execution settings were changed. V2 is an isolated research specification, not an enabled strategy version.

## Universe and components

Initial V2 research excludes M1. Primary timeframes are M15, M30, H1; M5 is diagnostic, H4 is `INSUFFICIENT_SAMPLE`. Components are modular: technical core (existing EMA/ADX/RSI/ATR/structure only), Time Wheel role, trend context, volatility context, fixed-R exit, stop cap, maximum hold, and cap_1.

## Frozen staged candidates

Entry arms: A technical core only; B technical + Wheel confirmation; C technical with Wheel veto; D Wheel trigger + technical confirmation. Exit arms: existing target plus 0.5/0.75/1/1.25/1.5R target with 1R stop. Holding arms: none/5/10/15/30/60 minutes. Stop arms: current invalidation, ATR cap, structure capped by ATR, maximum risk distance. Breakeven is tested only after MFE proves a meaningful fraction of losers reached +0.5R.

No continuous threshold search, new indicator, or production mutation is permitted. A V2 profile is created only after a frozen candidate has PF>1 and positive expectancy in validation and a genuinely unseen holdout.
