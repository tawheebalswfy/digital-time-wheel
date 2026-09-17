# Execution Linkage Audit

## Previous failure mode

The platform persisted the signal ID, symbol, timeframe, and request JSON, but the MT5 response was stored mainly as an unstructured result payload. The adapter exposed legacy `ticket` and `deal` keys and attempted a best-effort position lookup. Close reconciliation then depended on those legacy keys. The report therefore matched only 9 of 196 positions by the available persisted position tickets (4.59%); the remaining historical records are retained as unresolved.

The principal loss was durable attribution, not a signal or strategy change. The repair does not rewrite legacy evidence or infer missing timeframe values.

## Current lifecycle

1. The closed-candle signal is persisted with a stable symbol/timeframe/event identity.
2. The execution controller creates one durable `execution_orders` reservation.
3. A compact non-sensitive broker comment is added before the request is sent.
4. The exact request and linkage fields are persisted before the broker call.
5. The MT5 response captures order and deal tickets immediately. A bounded deal-history lookup uses the returned IDs to obtain `position_id` on hedging accounts; a magic/comment position lookup is only fallback evidence.
6. Close reconciliation matches position ID first, then returned order/deal IDs, and persists close deal/order, time, price, realized profit, commission, swap, and reason.
7. Restart reconciliation reads durable linkage and never claims positions without strategy ownership metadata.

## Ownership

System-owned positions require the stable magic number `20260910` and a `DTW|...` comment prefix. Manual positions and other EAs remain external and are never assigned a signal or execution record.

## Legacy handling

Rows without reliable MT5 linkage remain explicitly unresolved (`POSITION UNKNOWN` or their existing state). No ticket, timeframe, candle identity, or signal is fabricated. A pre-migration SQLite backup is retained at `runtime/timewheel.sqlite3.pre_linkage_backup_20260917`.
