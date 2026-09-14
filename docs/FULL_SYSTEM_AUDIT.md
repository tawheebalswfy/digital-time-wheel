# DIGITAL TIME WHEEL XAU — Full System Audit

Audit date: 13 September 2026  
Scope: read-only source, runtime, SQLite, retained MT5 evidence, research artifacts, and test verification. No MT5 order was sent and no strategy or parameter was changed.

## Executive assessment

Overall health score: **58/100**.

The research core is preserved and the saved genuine-MT5 evidence is internally coherent. The mathematical, signal, historical-validation, and frontend transport foundations are in reasonable condition. The system is not currently operational because port 8000 has no listener, and the DEMO execution layer is not safe to enable until the execution-accounting and broker-preflight findings below are resolved.

Finding counts: **0 Critical, 5 High, 6 Medium, 2 Low**.

### CRITICAL

No critical finding was observed. The source contains one backend `order_send` path, guarded by MT5 DEMO-mode verification and an explicit in-memory enable state. No live-account route was found. Because the backend was down, this conclusion is source and retained-evidence based rather than a live enable test.

### HIGH

#### H-01 — Backend is unavailable and the launcher is not reliably recoverable

**Description:** At audit time no process listened on port 8000 and no Python backend process was running. The recorded launcher attempt failed with PowerShell `Start-Process: Item has already been added. Key in dictionary: 'Path'`.

**Evidence:** `netstat` showed no 8000 listener; `runtime/backend.stderr.log` contains the startup failure; `scripts/start-local.ps1` is the only local supervisor path.

**Impact:** Live feed, REST, WebSocket, and execution are unavailable until manually recovered. Trading execution is fail-closed while down. Research validity is unaffected for retained artifacts.

**Recommended fix:** Diagnose the launcher/environment failure and add a bounded startup health check. Do not auto-enable execution during recovery.

#### H-02 — Execution records are never reconciled after a position closes

**Description:** `execution_orders` has nullable `close_payload` and `Database.close_execution`, but no service or controller path calls `close_execution`. The audit database contains 8 execution rows, all state `POSITION OPEN`, with no close payload, despite the runtime having no currently open positions in the last observed status.

**Impact:** Position limits, cooldown decisions, last-order state, closing price/time, close reason, and P&L become stale. This can block valid entries indefinitely or misstate exposure. It directly affects trading execution and auditability.

**Recommended fix:** Add a read-only MT5 history-deal reconciliation loop keyed by position/deal ticket before changing capacity state. Preserve the original attempt record.

#### H-03 — Required market-open and symbol-trade-mode preflight checks are absent

**Description:** `ExecutionController.consider` checks connection, DEMO status, positions, cooldown, spread, and SL/TP construction, but `MT5Adapter.build_order` does not verify symbol trade mode, session availability, or an explicit market-open condition immediately before send.

**Impact:** Closed-market or non-tradable-symbol attempts reach `order_send` and rely on broker rejection. This is an execution safety gap, though it does not create a live-account path.

**Recommended fix:** Read symbol trade mode/session state and reject unless the symbol is currently tradable; recheck immediately before `order_send`.

#### H-04 — Stop-level validation uses the entry side instead of broker bid/ask reference prices

**Description:** `build_order` validates BUY/SELL SL and TP distances relative to the constructed entry price. MT5 stop-level validation is side-specific and normally references current Bid/Ask. The request can therefore pass the local check while violating the broker’s actual protective-distance rule.

**Impact:** Protective SL/TP may be rejected or an order may be accepted with broker behavior different from the local validation. This directly affects execution safety.

**Recommended fix:** Validate BUY stops against the broker-required Bid/Ask references and SELL stops against the corresponding side, using symbol digits, point, and stop/freeze levels.

#### H-05 — Open-position and per-timeframe accounting is not lifecycle-safe

**Description:** Total positions are read from all XAUUSD positions, while per-timeframe capacity is inferred from execution rows whose state remains `POSITION OPEN`. There is no ownership or close reconciliation, and persisted rows do not contain a reliable MT5 position-to-timeframe mapping after restart.

**Impact:** Manual/other-EA positions conservatively consume capacity, while stale system rows can permanently consume per-timeframe slots. Multiple-timeframe execution cannot be trusted for exposure accounting. This affects trading execution.

**Recommended fix:** Keep manual/other-EA positions separate from system ownership, identify system positions by magic/order/deal linkage, and reconcile open/closed state before applying limits.

### MEDIUM

#### M-01 — Signal UUID does not itself include timeframe

The deterministic event key includes provider, dataset, symbol, timeframe, strategy version, and signal timestamp, so duplicate prevention distinguishes M1 from M15. However, `Database.log_signal` assigns a random UUID (`str(uuid.uuid4())`) as `signal_id`; the timeframe is only in payload/event key. This is a traceability mismatch with the stated signal-ID contract. It does not currently cause cross-timeframe duplicate collisions.

#### M-02 — Duplicate-protection settings are persisted but not behaviorally independent

`duplicate_signal_protection` and `one_trade_per_unique_signal` are stored and shown, but `reserve_execution` always enforces the database `UNIQUE(signal_id)` constraint. The settings do not independently control behavior. This is safer than allowing duplicates, but the UI/backend configuration can claim a disabled option while the backend still blocks it.

#### M-03 — Frontend execution selector is DOM-mutated around a single React select

`frontend/app/page.tsx` still renders a single controlled `select` using `execution.timeframe`; a `useEffect` hides it and injects checkbox DOM nodes. The save payload uses `selected_timeframes`, but the control is not a normal React-controlled multi-select. Re-render, accessibility, or hot-reload behavior can diverge from the displayed state.

#### M-04 — Full Python suite has two repeatable WebSocket cleanup failures

`python -m unittest discover -s tests -q` ran 56 tests: 54 passed and 2 failed: `test_websocket_reconnect_cleans_up_and_does_not_poll` and `test_websocket_same_client_replaced_once`, both reporting `connections['active']` remaining nonzero. The frontend transport test passes. This is a real lifecycle/concurrency signal that needs investigation.

#### M-05 — MT5 history conversion does not enforce alignment/gap checks

`MT5Adapter._convert` calls `validate_bars(..., require_alignment=False)`, and the history path does not independently reject missing intervals or duplicate timeframe bars. The retained evidence confirms genuine OHLC datasets and ordering, but the live retrieval path is less strict than the CSV path. This affects data-quality confidence and research validity if a broker response is incomplete.

#### M-06 — Frontend exposes position values rejected by backend validation

The frontend injects `20` and `50` into the maximum-open-positions select, but `ExecutionSettings.max_positions` is validated with `le=10`. Saving either value is rejected by the backend. This is a settings UI/backend mismatch; it does not bypass the actual risk limit.

**Recommended fix:** Either remove unsupported UI options or extend backend validation only after an explicit broker/account exposure review.

### LOW

#### L-01 — Local process inventory shows several stale Node processes

The audit found multiple Node processes, while no frontend listener was confirmed in the same snapshot. Their ownership was not established. This is a resource-hygiene concern, not evidence of duplicate MT5 collectors.

#### L-02 — Vite production output retains a nonfatal bundle-size warning

The build warns that a JavaScript chunk exceeds 500 kB. The build succeeds and this does not affect trading or research correctness.

## Acceptance matrix

| Component | Status | Evidence |
|---|---|---|
| Backend startup/runtime | FAIL CURRENTLY UNAVAILABLE | No port-8000 listener; launcher error in `runtime/backend.stderr.log` |
| Backend lifespan/collector | PASS BY SOURCE / RETAINED RUN | `main.py` has one lifespan collector; retained stability run had one MT5 initialization and zero lifecycle churn |
| REST endpoints | PASS BY TESTS; NOT LIVE NOW | API tests pass; live endpoint unavailable at audit time |
| WebSocket transport | PARTIAL | Frontend transport test passes; 2 Python cleanup tests fail |
| MT5 live feed | NOT REVERIFIED | Retained 181-second evidence shows valid changing Bid/Ask and zero stale/error samples |
| MT5 history | PASS RETAINED / NOT LIVE NOW | Seven genuine datasets retained; latest stability JSON incorrectly reports `history_available:false` despite prior final history verification |
| Timezone normalization | PASS | `+03:00` broker correction, Asia/Aden analysis, UTC canonical timestamps; raw timestamps retained; future check follows normalization |
| Time Wheel | PASS BY TESTS/EVIDENCE | 36 sectors, 10-degree geometry, roots/mappings/boundaries covered by tests and retained live evidence |
| Multi-timeframe analysis | PASS RETAINED | M1/M5/M15/M30/H1/H4/D1 snapshots/signals were retained in validation evidence |
| Signal generation | PASS | Closed-bar observation architecture, deterministic event keys, immutable signal chain |
| Signal audit | PASS | SQLite hash-chain verification and immutable triggers |
| Target/stop generation | PASS LOGICALLY; EXECUTION GAP | Directional target/invalidation checks exist; broker side-specific stop-level reference needs correction |
| Backtester | PASS RETAINED | Causal warmup, next-bar entry, stop-first, costs, purges, reproducible frozen baseline |
| Research Lab | PASS RETAINED | Attribution artifacts and reports retained; no profitability claim supported |
| DEMO execution gating | PASS BY SOURCE/RETAINED STATUS | DEMO enum check and explicit enable gate; no live route found |
| Multi-timeframe execution | PARTIAL | Backend iterates selected timeframes and event keys distinguish them; UI is DOM-injected and accounting is not lifecycle-safe |
| Position limits | PARTIAL | Total/per-timeframe checks exist, but stale rows and no ownership reconciliation undermine correctness |
| Duplicate prevention | PASS CONSERVATIVE / CONFIG MISMATCH | SQLite unique signal reservation and controller lock prevent duplicates; booleans do not independently alter behavior |
| Persistence | PASS WITH ACCOUNTING GAP | Strategy/feed/execution settings and records persist; close fields remain unpopulated |
| Restart behavior | PASS BY DESIGN, NOT LIVE-RECHECKED | `enabled=False` is initialized in `ExecutionController`; current launcher recovery is broken |
| Live-account blocking | PASS BY SOURCE | `ACCOUNT_TRADE_MODE_DEMO` equality is required both at enable and send |

## Strategy, Time Wheel, and research validity

No production strategy formula or default was changed during this audit. `wheel.py` implements modulo-normalized angles, 36 sectors, price mappings, digital roots, local-time conversion, and explicit cycle models. `signals.py` requires numerical direction, technical confirmation, and threshold agreement; neutral signals produce no targets. The retained tests cover angle wrap, negative modulo, roots, mappings, timezone behavior, causal pivots, and prefix invariance.

The backtester uses causal feature prefixes, delayed swing confirmation, next-bar open entries, stop-first ambiguity, adverse gap handling, fixed costs, and purged chronological windows. Retained baseline and Time Wheel attribution reports correctly state that the observed final-test results are negative or inconclusive and do not establish profitability. No expensive experiment was rerun.

## DEMO execution and order-safety audit

The only MT5 order path found is `MT5Adapter.send_order`, called by `ExecutionController.consider` after a durable `signal_id` reservation and a process lock. The frontend calls enable/stop/settings endpoints and contains no direct `MetaTrader5` import or raw order method. Account mode is checked using MT5’s DEMO constant; a missing account or terminal fails closed. The current design never closes a position automatically.

The audit did not send a preview or test order. Programmatic duplicate tests use a fake adapter and verify one durable reservation/one send call without contacting MT5. Existing records show 8 accepted execution attempts, all still marked `POSITION OPEN`; this is the evidence behind H-02 and means the current execution ledger must not be treated as a reliable live position ledger.

## Runtime and test evidence

- SQLite `PRAGMA quick_check`: `ok`.
- Counts at audit: 1 strategy, 2 strategy versions, 1 settings row, 1 feed profile, 1 execution-settings row, 454 signals, 1,230 signal results, 454 wheel states, 7 datasets, 39,885 candles, 8,422 market ticks, 1 backtest, 0 experiment rows, and 8 execution orders.
- No orphan execution-to-signal relationships were found.
- Frontend transport test: pass.
- Frontend TypeScript and production build: pass; existing bundle-size warning remains.
- Python suite: 56 total, 54 pass, 2 WebSocket cleanup failures.
- Retained connection stability evidence: 181.30 seconds, unchanged backend PID, 91 WebSocket messages, 93 REST checks, 0 collector errors, 0 MT5 initialize/shutdown events during the window, valid Bid/Ask samples, and no stale/error samples. It is historical evidence, not a current runtime verification.

## Recommended next action

Keep DEMO AUTO TRADING disabled. First repair and verify the local launcher/runtime, then address H-02 through H-05 with focused execution tests and a fresh read-only stability run. Only after close reconciliation, ownership-aware position accounting, market-open checks, and broker-side stop validation pass should DEMO enablement be reconsidered.

## Direct answers

1. **Overall health:** 58/100.
2. **Safe to enable DEMO auto trading:** No, not until the five High findings are resolved and reverified.
3. **Can an issue create unintended duplicate orders?** The current unique reservation and lock make duplicate submission unlikely for an identical persisted signal; the two WebSocket cleanup failures and stale execution lifecycle still require resolution before relying on that conclusion operationally.
4. **Any live-account execution path?** No path was found; the only order path requires MT5 DEMO mode at enable and send.
5. **Multi-timeframe execution correctly implemented?** Backend selection/evaluation is present, but the frontend control is brittle and position accounting is incomplete; overall status is Partial.
6. **Do saved settings match backend behavior?** Core limits and selected timeframes are consumed, but duplicate-protection toggles are not independent and close/accounting state is stale.
7. **Finding counts:** 0 Critical, 5 High, 6 Medium, 2 Low.
8. **Exact next action:** keep execution disabled; repair the runtime launcher, then implement and test close reconciliation plus ownership-aware position accounting before any demo enablement.
