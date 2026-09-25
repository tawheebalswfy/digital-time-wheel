# V7 Regime Definitions

- **STRONG_TREND**: ADX ≥25 and absolute 3-bar slow-EMA slope ≥0.15 ATR.
- **WEAK_TREND**: ADX 15–24 not qualifying as strong.
- **RANGE_LOW_VOL**: ADX <15 and causal normalized-ATR lower rolling third.
- **RANGE_NORMAL_VOL**: ADX <15 and causal normalized ATR between rolling thirds.
- **HIGH_VOL_EXPANSION**: normalized ATR at/above upper rolling third and a causal 20-bar range break.
- **TRANSITION**: all remaining bars; no trade tested.

Rolling quantiles use only completed prior bars.
