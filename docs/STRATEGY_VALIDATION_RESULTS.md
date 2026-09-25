# Strategy Validation Results

## Labels

- **Discovery:** 2026-08-11 through the fixed early chronological boundary.
- **Validation:** next chronological segment, with 31-bar purge.
- **Final historical segment:** 2026-09-04 to 2026-09-10 UTC; retrospective OOS because it was previously inspected.
- **Forward DEMO:** 2026-09-18 to 2026-09-22; excluded from historical selection and used only as qualitative corroboration.

## Validation decision table

| Item | Discovery | Validation | Final historical segment | Decision |
|---|---|---|---|---|
| Full baseline | Negative PF/expectancy | PF 0.503, exp -0.548 | PF 0.491, exp -0.535 | Reject as positive edge. |
| Time Wheel entry increment | Mixed | +0.0709 expectancy vs technical-only | -0.0768 | Not validated. |
| Wheel exit increment | Per-trade uplift in isolated arms | Same directional observation | Worse aggregate P/L/DD | Not validated. |
| `cap_1` | Best of fixed risk set | PF 0.524, exp -0.489 | PF 0.551, exp -0.426, DD 289.14 | Relative improvement only; not accepted. |
| Cooldown-only variants | Negative | Negative | Negative | Not accepted. |
| Combined cap + cooldown | Negative | Negative | Negative | Not accepted. |

## Required next evidence

No improvement is genuinely out-of-sample validated to the required standard. A valid next experiment needs new, non-overlapping MT5 XAUUSD history not inspected in this audit, a protocol frozen before results, and one candidate at a time. Minimum acceptance: materially improved PF, non-negative expectancy, controlled drawdown, sufficient trades across more than one market period, and no dependence on one outlier day.

## Production decision

Keep all production defaults unchanged. Keep auto trading disabled during research. `cap_1` may be considered only as a future DEMO-only research configuration after the new-history protocol passes; it is not approved for production.
