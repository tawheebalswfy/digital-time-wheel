# V8 Candidate Specifications
## M30_STRONG_TREND_TREND_CONTINUATION

- **timeframe**: M30
- **regime**: STRONG_TREND
- **regime_rule**: ADX >=25; absolute 3-bar slow-EMA slope >=0.15 ATR.
- **entry_rule**: EMA fast/slow alignment, signed slow-EMA slope, and +DI/-DI agree; close lies beyond fast EMA in trend direction.
- **indicators**: V7 defaults: EMA 12/26, ADX/ATR/RSI period 14; no changes.
- **exposure**: one non-overlapping position (V7 simulator)
- **holding**: V7 default maximum 30 bars; no separate frozen holding study
- **stop**: No V7 exit was frozen for this candidate; V8 diagnostics use V7 structural invalidation.
- **targets**: Diagnostic-only 1.0R, 1.25R, and 1.5R; not tuned and not eligible for OOS confirmation.
## H1_STRONG_TREND_TREND_CONTINUATION

- **timeframe**: H1
- **regime**: STRONG_TREND
- **regime_rule**: ADX >=25; absolute 3-bar slow-EMA slope >=0.15 ATR.
- **entry_rule**: EMA fast/slow alignment, signed slow-EMA slope, and +DI/-DI agree; close lies beyond fast EMA in trend direction.
- **indicators**: V7 defaults: EMA 12/26, ADX/ATR/RSI period 14; no changes.
- **exposure**: one non-overlapping position (V7 simulator)
- **holding**: V7 default maximum 30 bars; no separate frozen holding study
- **stop**: No V7 exit was frozen for this candidate; V8 diagnostics use V7 structural invalidation.
- **targets**: Diagnostic-only 1.0R, 1.25R, and 1.5R; not tuned and not eligible for OOS confirmation.
## H4_STRONG_TREND_PULLBACK_CONTINUATION

- **timeframe**: H4
- **regime**: STRONG_TREND
- **regime_rule**: ADX >=25; absolute 3-bar slow-EMA slope >=0.15 ATR.
- **entry_rule**: Same trend alignment; BUY RSI 40–55 with close <= fast EMA +0.3 ATR, or SELL RSI 45–60 with close >= fast EMA -0.3 ATR.
- **indicators**: V7 defaults: EMA 12/26, ADX/ATR/RSI period 14; no changes.
- **exposure**: one non-overlapping position (V7 simulator)
- **holding**: V7 default maximum 30 bars; no separate frozen holding study
- **stop**: No V7 exit was frozen for this candidate; V8 diagnostics use V7 structural invalidation.
- **targets**: Diagnostic-only 1.0R, 1.25R, and 1.5R; not tuned and not eligible for OOS confirmation.
## D1_STRONG_TREND_PULLBACK_CONTINUATION

- **timeframe**: D1
- **regime**: STRONG_TREND
- **regime_rule**: ADX >=25; absolute 3-bar slow-EMA slope >=0.15 ATR.
- **entry_rule**: Same trend alignment; BUY RSI 40–55 with close <= fast EMA +0.3 ATR, or SELL RSI 45–60 with close >= fast EMA -0.3 ATR.
- **indicators**: V7 defaults: EMA 12/26, ADX/ATR/RSI period 14; no changes.
- **exposure**: one non-overlapping position (V7 simulator)
- **holding**: V7 default maximum 30 bars; no separate frozen holding study
- **stop**: No V7 exit was frozen for this candidate; V8 diagnostics use V7 structural invalidation.
- **targets**: Diagnostic-only 1.0R, 1.25R, and 1.5R; not tuned and not eligible for OOS confirmation.
