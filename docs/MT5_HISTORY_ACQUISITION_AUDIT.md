# MT5 History Acquisition Audit

## Scope and safety

This is read-only MT5 data diagnostics. The runner contains no order API call, does not import the execution controller, and does not change any strategy or terminal setting. It called only `symbol_select`, `symbol_info`, `copy_rates_range`, `copy_rates_from`, and `copy_rates_from_pos`.

## Exact observed failure

The exact MT5 error for **every** direct XAUUSD rate request was `(-1, 'Terminal: Call failed')`. It occurred for all three APIs, including `copy_rates_from_pos(..., 0, 1)`, which requests only the newest single bar. Therefore the evidence rules out a six-month range size, date-window construction, pagination, and selected-symbol issue. The MT5 Python API exposes no more specific cause than code `-1`; the strongest provable diagnosis is that this terminal's rate/history service is failing to supply XAUUSD bars at the API boundary.

Terminal: connected=True; server=ICMarketsSC-Demo; build=6182; `maxbars`=100000; XAUUSD `symbol_select`=True; visible=True; Market Watch path=Commodities\Metals\XAUUSD.

## API arguments and results

The complete call-by-call evidence, including exact UTC datetimes, MT5 timeframe constants, row counts, and immediate `last_error()` values, is in `docs/MT5_HISTORY_ACQUISITION_RAW.json`. Every 7/30/60/90/180/365-day range and matching `copy_rates_from` request returned zero rows. The 365-day process also attempted bounded 30-day `copy_rates_range` chunks; all failed identically.

| TF | Max successful direct range (days) | Downloaded bars | First | Last | Duplicates | Non-interval gaps | Invalid OHLC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M15 | 0 | 0 | — | — | 0 | 0 | 0 |
| M30 | 0 | 0 | — | — | 0 | 0 | 0 |
| H1 | 0 | 0 | — | — | 0 | 0 | 0 |

## Position pagination and lower-timeframe alternative

The position-index alternative failed on page 0 for M15, M30, H1, M1, and M5 with the same error. Thus no deeper M1/M5 history is presently available from this terminal, and causal M15/M30/H1 resampling cannot extend coverage. No synthetic or resampled bars were created.

## Retained genuine MT5 fallback export

No newly downloaded data exists. To provide a fixed research-only data location without overwriting anything, the previously retained datasets whose metadata source is `MT5` were copied from SQLite read-only into new CSV files. These are not represented as a successful fresh download.

| TF | First UTC | Last UTC | Candles | Duplicates | Non-interval gaps | Invalid OHLC | Zero volume | CSV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M15 | 2026-08-11T14:15:00+00:00 | 2026-09-10T13:45:00+00:00 | 2013 | 0 | 22 | 0 | 0 | C:\Users\PC\Documents\Codex\2026-09-09\you-are-a-senior-quantitative-trading\outputs\digital-time-wheel-xau\data\history\XAUUSD_M15_RETAINED_MT5_20260922T182525Z.csv |
| M30 | 2026-08-11T14:30:00+00:00 | 2026-09-10T13:30:00+00:00 | 1006 | 0 | 22 | 0 | 0 | C:\Users\PC\Documents\Codex\2026-09-09\you-are-a-senior-quantitative-trading\outputs\digital-time-wheel-xau\data\history\XAUUSD_M30_RETAINED_MT5_20260922T182525Z.csv |
| H1 | 2026-08-11T15:00:00+00:00 | 2026-09-10T13:00:00+00:00 | 503 | 0 | 22 | 0 | 0 | C:\Users\PC\Documents\Codex\2026-09-09\you-are-a-senior-quantitative-trading\outputs\digital-time-wheel-xau\data\history\XAUUSD_H1_RETAINED_MT5_20260922T182525Z.csv |

The non-interval gaps are expected session/weekend gaps pending a broker-session calendar; none is silently filled.

## Terminal configuration finding and required manual action

`terminal_info().maxbars` is 100,000, sufficient for the target bar counts (roughly 35k M15, 17.5k M30, 8.8k H1 for one year). Read-only checks found no `MaxBars` line in the terminal INI files. This is not evidence of a max-bars cap.

Required manual terminal action: in the same ICMarketsSC-Demo terminal, open **XAUUSD M1**, press **Home** (or scroll fully left) and wait for the chart to finish downloading history; then open **F2 / History Center**, select XAUUSD, and download/synchronize bars. Confirm Tools → Options → Charts keeps Max bars in chart at least 100,000, restart/re-login the terminal if needed, and rerun this audit. This action is required because even a one-bar API request currently fails; code-side batching cannot repair absent/unavailable terminal history.

## Conclusion

Neither six nor twelve months was achieved. The only usable coverage remains the retained 2026-08-11 through 2026-09-10 UTC MT5 data. Do not begin V4 research until the terminal returns at least six months of direct rates or genuinely deeper lower-timeframe rates suitable for causal resampling.
