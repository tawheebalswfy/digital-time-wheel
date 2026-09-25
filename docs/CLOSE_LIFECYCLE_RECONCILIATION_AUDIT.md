# Close Lifecycle Reconciliation Audit

## Scope and safety

This repair changes only the execution-record lifecycle. It does not change strategy formulas, Time Wheel logic, signal generation, SL/TP computation, volume/risk defaults, or timeframe selection. Reconciliation only calls position/history read APIs; it has no `order_send` path. The controller remains disabled by default, including after restart.

Before migration/reconciliation, the active database was copied to:

`runtime/timewheel.sqlite3.pre_close_fix_20260922_184138`

`timewheel-new-test.sqlite3` was not opened for writing or changed.

## Root cause and old behavior

The old reconciler examined only rows in `POSITION OPEN`. If the position disappeared but a closing deal was not returned in that first history query, it changed the row to `POSITION UNKNOWN`. Subsequent reconciliation skipped that state entirely. This explains why a transient/late history observation could leave a real MT5 close permanently unrecorded.

The old path also:

- considered only entry codes 1 and 2, omitting `DEAL_ENTRY_OUT_BY` (3);
- did not use a live position's `identifier` alongside its ticket for hedge-mode recovery;
- omitted MT5 deal `symbol` and `magic` from the adapter output, so they could not be checked;
- summed only exit-deal costs, omitting the opening deal's commission/swap; and
- accepted a normalized close timestamp without rejecting it when it preceded a persisted open timestamp.

## MT5 relationship model

In a hedging account, order ticket, deal ticket, and position identifier are distinct values. The durable mapping is:

1. `mt5_order_ticket`: opening order ticket.
2. `mt5_deal_ticket_open`: opening fill/deal ticket.
3. `mt5_position_ticket`: the position identifier (`DEAL_POSITION_ID`), used as the primary closure bridge.
4. `mt5_deal_ticket_close`: closing deal ticket.
5. `mt5_order_ticket_close`: closing order ticket carried by that deal.

The repaired reconciler selects a candidate close only when `DEAL_POSITION_ID == mt5_position_ticket`. Symbol, magic (when present), and volume are additional ownership/consistency checks. It does not close a row by nearby timestamp, price, symbol, or volume alone. The persisted row must itself be DTW-owned (`mt5_comment` begins `DTW`); manual and other-EA positions are not claimed.

## Fixed lifecycle

At periodic status/poll reconciliation and after restart when MT5 is connected (the background poll path is throttled to one bounded recovery pass every 30 seconds):

1. Read owned live positions and index both `ticket` and `identifier`.
2. Consider persisted DTW rows in either `POSITION OPEN` or `POSITION UNKNOWN` with a stored position identifier.
3. If still live, retain/reset `POSITION OPEN`.
4. Otherwise make one bounded MT5 history-deals query for the candidate set, capped to the last seven days and bounded by execution open/created time.
5. Match deals by `DEAL_POSITION_ID`, then validate ownership.
6. Treat `DEAL_ENTRY_OUT`, `DEAL_ENTRY_INOUT`, and `DEAL_ENTRY_OUT_BY` as closure semantics. `DEAL_ENTRY_IN` is never a closing deal.
7. Update the original execution row only, persisting close deal/order tickets, UTC close time/price, gross realized profit from close deals, and position-level commission/swap from all linked deals exactly once. Mark it `CLOSED`.
8. If evidence is insufficient, retain `POSITION UNKNOWN` so a later bounded pass can retry. No duplicate execution row is made.

`realized_profit` remains MT5 gross deal profit. `commission` and `swap` are stored separately, so callers derive net as `realized_profit + commission + swap`; no opening commission is double-counted.

## Timestamp handling

The adapter converts MT5 broker wall-clock epochs to internal UTC exactly once at ingestion. Its `history_deals` query converts canonical UTC boundaries to the configured broker offset at the MT5 API boundary. Close timestamps are stored as UTC ISO strings.

`Database.close_execution` validates both values before writing. A malformed, naive, or backwards close timestamp is rejected and logged; it neither fabricates a time nor swaps timestamps. This protects legacy rows whose old `open_time` may have been stored with inconsistent offset labeling.

## Active database reconciliation result

The safe reconciliation was executed against `runtime/timewheel.sqlite3` with MT5 connected read-only for positions/history. The controller reported `enabled=False`; no orders were sent.

| Metric | Before | After |
|---|---:|---:|
| CLOSED | 0 | 0 |
| POSITION UNKNOWN | 15 | 15 |
| Unresolved (`POSITION OPEN` + `POSITION UNKNOWN`) | 23 | 23 |
| Exact close-linked rows | 0 | 0 |

The active database contains 23 execution rows and none of the 58 forward-test position-ticket range (`1941742735`–`1952913273`). Therefore the active database cannot reconcile that separate report window; the prior read-only snapshot analysis remains 58/58 exact entry-linked but must not be modified. No close evidence was found for the active database's 23 rows in this safe pass.

Post-pass integrity counts in the active database: duplicate position tickets 0; duplicate close-deal tickets 0; duplicate signal IDs/successful executions 0; `close_time < open_time` 0; CLOSED without close deal 0; CLOSED without timeframe 0; close without position linkage 0; duplicate execution rows 0. No wrong-symbol close was persisted because no closure was claimed.

## Test coverage

`tests/test_close_lifecycle_reconciliation.py` uses fakes only and covers normal close, `DEAL_POSITION_ID`, opening-versus-closing semantics, hedge identifier recovery, `OUT_BY`, close tickets/time/P&L/cost persistence, immutable original signal/timeframe, restart retry, still-open retention, external ownership rejection, impossible timestamps, no duplicate row, and absence of any order-send method.
