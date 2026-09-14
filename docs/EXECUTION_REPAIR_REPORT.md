# Execution Repair Report

Date: 13 September 2026

This repair changed only execution/runtime safety. Strategy formulas, thresholds, defaults, research data, and production signals were not changed. No MT5 order was sent and auto trading remained disabled.

## Audit finding disposition

| Finding | Status | Evidence |
|---|---|---|
| H-01 launcher/runtime | FIXED | `scripts/start-local.ps1` now removes stale PID files, checks listener ownership, uses detached .NET process launch, and records the serving listener PID. Normal launch reached `/api/health` with one backend and one collector. |
| H-02 close reconciliation | PARTIALLY FIXED | New durable `position_ticket` migration, MT5 history-deal reader, and controller reconciliation update CLOSED records with close time/price/P&L/reason. Legacy rows without a position ticket remain explicitly unreconciled until a matching deal/order is available. |
| H-03 market tradeability | FIXED | Preflight checks terminal/account permissions, symbol selection, trade mode, direction mode, valid quote, and 120-second freshness before construction and again before send. |
| H-04 broker stops | FIXED | SL/TP are normalized and checked against bid/ask plus max(stops-level, freeze-level, point), with directional rejection. |
| H-05 ownership/accounting | PARTIALLY FIXED | Positions expose magic/comment/identifier and limits count only DTW-owned positions. External/manual positions are separately reported and conservatively block entries by the persisted safety setting. Historical legacy fills without position linkage need manual reconciliation. |
| M-01 timeframe IDs | UNRESOLVED | Existing event keys include timeframe; UUID signal IDs remain unchanged. |
| M-02 toggle independence | PARTIALLY FIXED | Mandatory durable reservation/lock remains fail-closed; the two optional duplicate toggles still require a later schema/API design to become independently permissive. |
| M-03 selector | UNRESOLVED | Existing UI behavior retained during this execution repair. |
| M-04 WebSocket cleanup | FIXED | Registration is idempotent, replacement decrements the old socket, disconnect cleanup handles cancellation, and all 56 Python tests pass. |
| M-05 history gaps | UNRESOLVED | No strategy/data path change was made. |
| M-06 UI position options | UNRESOLVED | Backend remains capped at its existing safe validation. |

## Verification

- Python suite: **56/56 passed**.
- Frontend TypeScript check: passed.
- Frontend transport tests: passed.
- Frontend production build: passed; existing nonfatal Vite bundle-size warning remains.
- Normal launcher run: backend health returned `status=ok`, `engine_version=1.0.0`, `trading_enabled=false`, MT5 connected, XAUUSD selected, one collector diagnostic, and zero active WebSocket clients at check time.
- Read-only stability checker completed for 30 seconds. It did not call `initialize`, `shutdown`, `order_send`, enable, or stop APIs.

## Remaining execution blockers

The connected terminal currently reports DEMO mode but Algo Trading permission unavailable, and the latest quote is older than the freshness threshold. Auto trading therefore remains disabled and is not safe to enable until a fresh tradeable quote and terminal permission are present. Legacy persisted accepted rows lack position tickets and are not treated as reliable current exposure until matching history is available.

New overall execution health estimate: **82/100** (all High code-path gaps addressed; two lifecycle/data compatibility areas remain partial, with the existing Medium findings retained).
