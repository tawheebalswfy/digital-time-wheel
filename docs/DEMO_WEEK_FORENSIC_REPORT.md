# Demo Week Forensic Report

Source: `ReportHistory-52960017.html` (196 closed Positions rows). This is retrospective analysis of one demo report, not forward validation.

## Verified baseline

| Trades | Winners | Losers | Win rate | Gross profit | Gross loss | Net profit (report profit) | Commission | Swap | Net after costs | PF | Avg win | Avg loss | Expectancy | Max loss | Max win | Max DD |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 196 | 158 | 38 | 80.61% | 355.07 | -360.87 | -5.80 | -15.36 | -2.35 | -23.51 | 0.936 | 2.17 | -9.62 | -0.12 | -58.56 | 16.52 | 135.67 |

Maximum consecutive wins by realized net result: 31; maximum consecutive losses: 4.

The MT5 summary reports 196 trades, 159 winning trades, 37 losing trades, gross profit 348.28, gross loss -371.91, net -23.63 and PF 0.94. Recalculation from all 196 position rows yields 158 positive rows and 38 negative rows when `Profit + Commission + Swap` is classified as realized net. The one-row difference is a report accounting/classification discrepancy and is retained rather than silently corrected.

## Symbol breakdown

| Symbol | Trades | Win rate | Net P/L | PF | Expectancy | Avg win | Avg loss | Largest loss | Largest win |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | 4 | 100.0% | 2.90 | — | 0.72 | 0.72 | — | 0.34 | 1.84 |
| XAUUSD | 192 | 80.2% | -26.41 | 0.93 | -0.14 | 2.20 | -9.62 | -58.56 | 16.52 |

## BUY / SELL attribution

| Symbol | Direction | Trades | Win rate | Net P/L | PF | Expectancy | Avg loss | Max loss |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD | BUY | 0 | — | 0.00 | — | — | — | — |
| BTCUSD | SELL | 4 | 100.0% | 2.90 | — | 0.72 | — | 0.34 |
| XAUUSD | BUY | 106 | 84.0% | 58.51 | 1.48 | 0.55 | -7.24 | -17.59 |
| XAUUSD | SELL | 86 | 75.6% | -84.92 | 0.65 | -0.99 | -11.55 | -58.56 |

## Largest losses

| Position | Open | Symbol | Side | Entry | SL | TP | Exit | Net P/L | Planned R:R | Duration |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1938757473 | 2026.09.17 04:00:03 | XAUUSD | SELL | 4285.05 | 4343.47 | 4271.13 | 4343.53 | -58.56 | 0.24 | 655.6m |
| 1938757226 | 2026.09.17 04:00:03 | XAUUSD | SELL | 4284.79 | 4316.66 | 4275.00 | 4316.56 | -31.85 | 0.31 | 35.2m |
| 1938756816 | 2026.09.17 04:00:02 | XAUUSD | SELL | 4284.74 | 4307.71 | 4276.00 | 4308.18 | -23.52 | 0.38 | 7.0m |
| 1936139781 | 2026.09.16 13:00:02 | XAUUSD | SELL | 4339.06 | 4360.75 | 4335.00 | 4359.95 | -20.97 | 0.19 | 195.3m |
| 1934769195 | 2026.09.15 23:00:03 | XAUUSD | BUY | 4298.36 | 4281.59 | 4300.52 | 4281.44 | -17.59 | 0.13 | 235.6m |
| 1937677913 | 2026.09.16 21:30:48 | XAUUSD | BUY | 4312.43 | 4297.88 | 4326.00 | 4297.66 | -14.85 | 0.93 | 1.8m |
| 1941444667 | 2026.09.17 21:15:03 | XAUUSD | BUY | 4365.04 | 4351.53 | 4367.00 | 4350.70 | -14.42 | 0.15 | 18.9m |
| 1936139502 | 2026.09.16 13:00:01 | XAUUSD | SELL | 4339.05 | 4353.81 | 4336.00 | 4353.16 | -14.19 | 0.21 | 89.0m |
| 1934769062 | 2026.09.15 23:00:02 | XAUUSD | BUY | 4298.21 | 4287.24 | 4300.00 | 4286.89 | -11.99 | 0.16 | 182.2m |
| 1932258801 | 2026.09.15 04:04:43 | XAUUSD | SELL | 4297.70 | 4309.76 | 4290.03 | 4309.52 | -11.90 | 0.64 | 57.1m |

## Largest wins

| Position | Symbol | Side | Net P/L | Planned R:R |
|---:|---|---|---:|---:|
| 1937391894 | XAUUSD | BUY | 16.52 | 4.78 |
| 1932258847 | XAUUSD | SELL | 12.99 | 0.24 |
| 1932258823 | XAUUSD | SELL | 8.96 | 0.39 |
| 1937012326 | XAUUSD | BUY | 7.54 | 0.17 |
| 1938502149 | XAUUSD | BUY | 5.47 | 0.15 |
| 1936959728 | XAUUSD | BUY | 5.42 | 0.18 |
| 1938294131 | XAUUSD | SELL | 5.28 | 0.13 |
| 1930966158 | XAUUSD | SELL | 4.92 | 0.15 |
| 1931685131 | XAUUSD | SELL | 4.84 | 0.16 |
| 1931794874 | XAUUSD | SELL | 4.67 | 0.16 |

## Loss concentration

| Worst losses included | Combined net P/L | Share of total negative net P/L |
|---:|---:|---:|
| 1 | -58.56 | 16.0% |
| 3 | -113.93 | 31.2% |
| 5 | -152.49 | 41.7% |
| 10 | -219.84 | 60.1% |

## Entry clusters

Timeframe cannot be positively reconstructed from this HTML report; its comments identify DTW demo signals but do not carry timeframe or signal IDs. Clusters below are same-symbol, same-direction open timestamps within the stated window.

| Window | Clusters | Largest entries | Largest combined net loss |
|---|---:|---:|---:|
| 5s | 34 | 4 | -113.93 |
| 30s | 33 | 4 | -113.93 |
| 60s | 34 | 4 | -113.93 |

## Risk/reward and costs

- Planned R:R is available for all 196 rows with positive SL distance; median and mean are reported in the machine-readable artifact.
- Total commission: -15.36; total swap: -2.35; costs: -17.71.
- Before costs (raw Profit column): -5.80; after costs: -23.51.
- The strategy is already negative before costs; costs are not the primary cause of the loss.
- The dominant structural signature is a high hit rate paired with materially larger average losses than wins.

## Holding time and time of day

| Duration | Trades | Win rate | Net P/L | PF | Expectancy |
|---|---:|---:|---:|---:|---:|
| <1 minute | 50 | 88.0% | 59.81 | 5.44 | 1.20 |
| 1–5 minutes | 60 | 93.3% | 86.58 | 4.08 | 1.44 |
| 5–15 minutes | 54 | 70.4% | -34.53 | 0.69 | -0.64 |
| 15–60 minutes | 20 | 70.0% | -39.40 | 0.54 | -1.97 |
| >60 minutes | 12 | 50.0% | -95.97 | 0.26 | -8.00 |

The negative tail is concentrated in trades held 5 minutes or longer, especially over 60 minutes. Hour 04 has the most negative net result (-108.21), followed by hour 13 (-38.62); these are descriptive observations from a small sample, not causal session filters.

## Strategy-side traceback

The SQLite execution history positively links 19 report tickets to persisted symbol, timeframe, signal ID, strategy version, direction, SL and TP fields. The remaining report rows are UNMATCHED in the local database. The HTML report does not contain Time Wheel state, technical-confirmation state, or signal reasoning, so those fields are not inferred.

## Attribution limits and proposed controls

The report positively supports a risk/exposure problem, especially where same-direction entries cluster. It does not prove timeframe, signal age, Time Wheel state, technical confirmation, or causality. No strategy formula change is justified by this report alone.

| Rank | Candidate | Evidence | Action |
|---:|---|---|---|
| 1 | Same-symbol/same-direction cluster cap or cooldown | Directly observable clustered opens and asymmetric loss magnitude | Implement only as an execution risk control after replay |
| 2 | Planned R:R floor | SL/TP are present and loss asymmetry is measurable | Dry-run/replay first; do not alter signal generation |
| 3 | Daily loss stop / loss-streak pause | Plausible containment, but this report alone cannot set an unbiased threshold | Forward-test as configurable safety control |
| 4 | Direction filter | Must be evaluated by symbol and direction sample size | Do not implement from this report alone |

## Conclusion

The week is negative before costs, with losses concentrated in a small number of large adverse outcomes relative to small winners. The evidence supports exposure/risk containment as the first research direction, not a change to Time Wheel or technical signal formulas. Any replay comparison on this same week is retrospective and in-sample; it is not evidence of a future edge.
