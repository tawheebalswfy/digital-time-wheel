# Execution Linkage Schema

The mutable `execution_orders` table retains its existing columns and now adds nullable durable linkage columns. Existing records were migrated in place and preserved.

| Column | Meaning |
|---|---|
| `id` | Execution ID, generated before broker submission |
| `signal_id` | Unique persisted signal identity |
| `symbol`, `timeframe` | Direct execution scope columns |
| `candle_time` | Signal closed-candle timestamp when supplied |
| `direction` | BUY/SELL request direction |
| `strategy_version` | Strategy version hash used by the signal |
| `magic_number` | Stable ownership magic (`20260910`) |
| `mt5_order_ticket` | Opening MT5 order ticket |
| `mt5_deal_ticket_open` | Opening fill deal ticket |
| `mt5_position_ticket` | Hedging position identifier; legacy `position_ticket` remains for compatibility |
| `mt5_deal_ticket_close` | Closing deal ticket |
| `mt5_order_ticket_close` | Closing order ticket when supplied |
| `mt5_comment` | Exact broker comment |
| `volume`, `entry_price`, `stop_loss`, `take_profit` | Request/fill values |
| `open_time`, `close_time` | Broker/normalized lifecycle timestamps when known |
| `realized_profit`, `commission`, `swap` | Close-side financial values |
| `final_status` | Durable lifecycle status mirroring state |

Indexes cover symbol, symbol/timeframe/signal scope, and MT5 position ticket. JSON request/result payloads remain for complete audit detail; core ownership and attribution queries use dedicated columns.

## Signal identity

The event key includes provider, dataset, symbol, timeframe, strategy version, and closed-candle timestamp. New signal IDs are deterministic in the form:

`<SYMBOL>-<TIMEFRAME>-<event-key-hash>`

The existing UNIQUE constraint on `signal_id` remains the one-execution reservation guard. Independent M15 and M30 signals have different identities and are both allowed.
