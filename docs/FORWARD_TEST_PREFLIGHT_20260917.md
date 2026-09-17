# Forward-Test Execution-Linkage Preflight — FT-20260917-A

Date: 2026-09-17

Scope: verification only. No MT5 order was sent and auto trading was not enabled.

## Result

**Linkage preflight: PASS for schema and mocked lifecycle tests.**

The backend process was not running during this check (`127.0.0.1:8000` unavailable), so a live runtime readiness check must be repeated after normal startup before any DEMO test. This is an operational blocker, not a linkage-test failure.

## Schema verification — PASS

The active `runtime/timewheel.sqlite3` execution table contains every required field:

`id`, `signal_id`, `symbol`, `timeframe`, `candle_time`, `direction`, `strategy_version`, `magic_number`, `mt5_order_ticket`, `mt5_deal_ticket_open`, `mt5_position_ticket`, `mt5_deal_ticket_close`, `mt5_order_ticket_close`, `mt5_comment`, `volume`, `entry_price`, `stop_loss`, `take_profit`, `open_time`, `close_time`, `realized_profit`, `commission`, `swap`, `final_status`.

There are 23 existing records. Eight remain without a position ticket and are left unresolved; no legacy timeframe or ticket was fabricated.

## Signal identity — PASS

Mock verification confirms:

- Same symbol/timeframe/closed-candle event returns the same deterministic ID.
- XAUUSD M1 and M5 IDs differ.
- XAUUSD M15 and M30 IDs differ.
- A different candle timestamp produces a different ID.

Format: `<SYMBOL>-<TIMEFRAME>-<event-key-hash>`. The event key includes provider, dataset, symbol, timeframe, strategy version, and candle timestamp.

## Multi-timeframe execution identity — PASS

Mock M1, M5, M15, M30, and H1 BUY signals for XAUUSD at the same wall-clock moment receive independent signal IDs. They are all accepted as distinct reservations. A second attempt using the exact same signal ID is rejected by the durable unique reservation.

## Mocked open persistence — PASS

Mock order responses persisted order ticket, opening deal ticket, position ticket, compact comment, volume, fill price, SL, TP, symbol, timeframe, and signal ID in dedicated columns.

## Mocked close reconciliation — PASS

Mock close history updates close deal ticket, close order ticket when provided, close time, realized profit, commission, swap, and `final_status=CLOSED`. Original signal ID, timeframe, and position ticket remain unchanged.

## Restart recovery — PASS

Reloading the SQLite database restores the same execution ID, signal ID, symbol, timeframe, position ticket, and status. Reconciliation uses position ticket first, then order/deal identifiers and ownership metadata. It does not create a second execution row.

## External-position isolation — PASS

Mock manual and other-EA positions are classified external. Only the stable DTW magic/comment combination is system-owned.

## Ownership metadata

- Stable magic number: `20260910`
- Comment format: `DTW|<first-10-signal-id-characters>|<TIMEFRAME>`
- Maximum emitted length: 31 characters
- Comment contains no credentials or sensitive data.

## Intended DEMO baseline

The active persisted feed symbol is XAUUSD. The XAUUSD profile records:

| Setting | Value |
|---|---|
| Selected timeframes | M1, M5, M15, M30, H1 |
| Fixed lot | 0.01 |
| Maximum trades/day | 100 |
| Maximum simultaneous positions | 1 |
| Maximum positions/timeframe | 1 |
| Cooldown | Disabled |
| Maximum spread | Disabled |
| Duplicate signal protection | Enabled |
| One trade per unique signal | Enabled |
| Opposite direction | Blocked |
| Stop loss | Existing strategy invalidation |
| Take profit | Existing strategy target 1 |
| Auto trading | Disabled after restart; not enabled during preflight |

The global persisted settings currently differ from the XAUUSD profile; the runtime must load and display the active XAUUSD profile after startup before the forward test begins.

## Tests

- Full Python unittest suite: **65 passed**
- Execution-linkage and duplicate tests: **13 passed** in the focused run
- Frontend tests: **PASS**
- TypeScript check: **PASS**
- Python compileall: **PASS**
- Real `order_send`: **not called**

## Remaining blocker before DEMO forward-test

Start the backend normally and repeat the read-only runtime readiness check. Confirm MT5 DEMO account, fresh quote/history, active XAUUSD profile, and `trading_enabled=false`. Do not enable auto trading until that check passes.
