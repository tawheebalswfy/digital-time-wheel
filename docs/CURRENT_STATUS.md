# Current status — 10 September 2026

## Latest checkpoint — higher-timeframe attribution completed

**TW-HIGHER-TF-1** applied the fully isolated T/W entry and exit matrix to the retained genuine MT5 M15 and H1 data. M15 used 2,013 candles and H1 503, each under the same causal warmup, chronological train/validation/test split, 31-bar purges, 0.40 cost, and execution assumptions. H4 has only 131 candles and cannot support that methodology: the 78-bar warmup consumes its 60% boundary before the purge, so it is explicitly unavailable.

- **M15:** wheel entries worsen final-test expectancy in both fixed-exit comparisons. Wheel exits improve expectancy per trade (+0.1232 with technical entries, +0.6953 with wheel entries), but all variants remain negative and wheel exits worsen P&L/drawdown.
- **H1:** wheel exits also have positive raw per-trade deltas (+0.6363, +0.6243), but only 15–29 trades per arm make the result unreliable. Every arm is negative.
- **Ranking by evidence:** M15, M1, H1, H4. This ranks measured consistency, not profitability: no timeframe demonstrates standalone Time Wheel value.
- **Preservation:** no production/default/UI change. Fifteen research tests pass; source/database fingerprints are unchanged. The experiment is complete and saved as a checkpoint due to limited usage.

Read [TIME_WHEEL_HIGHER_TIMEFRAME_REPORT.md](TIME_WHEEL_HIGHER_TIMEFRAME_REPORT.md), the [frozen protocol](TIME_WHEEL_HIGHER_TIMEFRAME_PROTOCOL.md), and [full reproducible results](experiments/TW-HIGHER-TF-1-20260910T150431842360Z/comparison.json). Stop here unless a new research question is specified.

## Earlier checkpoint — fully independent Time Wheel attribution completed

## Latest checkpoint — fully independent Time Wheel attribution completed

**TW-FULL-EXIT-1** replaces the prior shared-exit diagnostic for attribution purposes. Production defaults, the saved baseline, MT5 data, and retained SQLite records are unchanged.

- **Fully separated variants:** A technical entry/technical exit; B wheel entry/wheel exit; C technical entry/wheel exit; D wheel entry/technical exit; E immutable current production baseline. Technical exits use only confirmed support/resistance, swings, and Fibonacci. Wheel exits use only wheel levels and angular projections. No ATR, indicators, or technical fields enter wheel exits; no wheel levels, harmonics, gates, or ATR enter technical exits.
- **Same frozen M1 split/costs:** train `[78,18071)`, validation `[18102,24105)`, final test `[24136,30170)`, with the retained 31-bar purges, identical next-open and stop-first behavior, max 30 bars, and 0.40 round-trip cost. The test begins at the corrected 4 September 2026 02:46 UTC bar.
- **Final-test entry value:** mixed. With technical exits, W minus T entry expectancy is +0.000469; with wheel exits it is -0.022331. Wheel entries reduce trades (113 and 84 respectively) and drawdown (52.93 and 13.54), but do not consistently improve expectancy.
- **Final-test exit value:** wheel exits improve expectancy per trade (+0.042798 with technical entries; +0.019997 with wheel entries), while increasing aggregate loss and drawdown because they create more trades.
- **Risk-filter result:** wheel entries reduce drawdown; wheel exits increase it. The combined production filter removed 1,540 losing and 428 profitable technical counterfactuals, but the removed group had less-negative expectancy than the accepted group. It did not selectively remove bad trades in this sample.
- **Conclusion:** no demonstrated standalone Time Wheel value. The final-test results are M1-only, retrospective, and cover six represented UTC dates. They cannot establish a stronger effect on other timeframes or a fresh independent predictive edge.
- **Verification:** 13 research tests pass. Output/source fingerprints and SQLite logical fingerprints are unchanged after the run. The prior general WebSocket cleanup instability is out of scope and was not modified.

Read [TIME_WHEEL_FULL_ATTRIBUTION_REPORT.md](TIME_WHEEL_FULL_ATTRIBUTION_REPORT.md) for every requested metric, attribution answer, and reproducible artifacts. The [frozen protocol](TIME_WHEEL_FULL_ATTRIBUTION_PROTOCOL.md) and [full comparison](experiments/TW-FULL-EXIT-1-20260910T145743432784Z/comparison.json) are retained with compressed per-arm signals, levels, rejected entries, trades, and equity.

## Earlier checkpoint — Time Wheel entry ablation completed

The user-requested **TW-ENTRY-1** diagnostic is complete. It took priority over the previously proposed payoff-eligibility study, which remains unexecuted.

- **Baseline immutable:** production files/defaults, saved profile, dataset, and every retained SQLite table fingerprint are unchanged. The original full-training and final-test baseline results reproduce exactly; all 6,033 final-test baseline forecast hashes match.
- **Experiment:** A = existing baseline; B = technical-only entries; C = wheel-only entries; D = existing combined. A and D are identical controls. All arms share the baseline target/stop generator, including wheel-derived exits, so this isolates entry logic only. Active-family weights are normalized with the unchanged threshold 55; no parameter fitting was performed.
- **Data/split:** the same 30,170 genuine-MT5-provenance M1 candles. Train `[78,18071)`, validation `[18102,24105)`, final test `[24136,30170)`, with 31-bar purges. The corrected final-test start stays 4 September 02:46 UTC for the first bar, 02:47 for the first signal. The original stored split/run is untouched.
- **Final-test net expectancy:** A/D -0.596645; B -0.519797; C -0.526690. Combined minus technical-only = **-0.076849 per trade**. Combined profit factor is 0.3279 versus 0.3675 for technical entries.
- **Exposure distinction:** combined takes 717 trades versus 1,059 technical-only trades. Its total loss is 122.6700 smaller and drawdown 113.4716 smaller, despite worse expectancy per trade. Validation expectancy improved by +0.070876, but that improvement reversed on the final-test segment.
- **Conclusion:** **evidence is inconclusive for independent out-of-sample predictive value**. The final-test entry contribution is adverse on expectancy and the fixed five-minute forecast diagnostic. The test period was already inspected and covers only six represented UTC dates; no strategy was promoted.
- **Verification:** eight new research tests pass; 18 real-data prefix checks pass; 90,081 forecast hashes and 13,844 trades audited. Full suite now has 45 tests: 43 pass, with the two previously documented WebSocket cleanup cases recurring (one failure, one CancelledError). No transport code was changed.

Read [TIME_WHEEL_ABLATION_REPORT.md](TIME_WHEEL_ABLATION_REPORT.md) for all requested train/validation/test metrics and incremental effects. [Frozen protocol](TIME_WHEEL_ABLATION_PROTOCOL.md), [comparison JSON](experiments/TW-ENTRY-1-20260910T143913330642Z/comparison.json), [metrics CSV](experiments/TW-ENTRY-1-20260910T143913330642Z/metrics.csv), and [artifact verification](experiments/TW-ENTRY-1-20260910T143913330642Z/verification.json) retain the complete experiment. Compressed forecasts, trades, equity, raw metrics, archived code, and hashes are alongside the comparison.

Reproduction: `.\.venv\Scripts\python.exe scripts\research_ablation.py`, then `.\.venv\Scripts\python.exe scripts\report_ablation.py <new-result-directory>`. Each simulation invocation creates a new result directory. No live service or MT5 terminal was started for this offline diagnostic. Further independent-edge evaluation requires genuinely uninspected data and a separately frozen protocol; no profitable-parameter search has begun.

## Earlier checkpoint — post-restart strategy validation

Read this section first. The connection-repair sections below describe the earlier session, not services currently running after the PC restart.

- **Platform preserved:** no rebuild, reset, refactor, strategy change, or database-record mutation. The current folder has no Git repository metadata; `git status --short` reports "not a git repository". No repository was initialized.
- **Current runtime:** ports 8000/5173 were not listening and MT5 was not running at inspection. This research session did not start them. Live quotes, wheel animation, and fresh history retrieval therefore remain unverified after the restart; earlier MVP acceptance evidence remains retained below.
- **Persistence verified:** SQLite quick check passed; all seven genuine-MT5-provenance datasets passed content-hash/OHLC checks; the saved Asia/Aden strategy and +03:00 auto-connect profile remain. All logical table fingerprints matched before/after validation.
- **Exact reproduction:** the original train and test backtest payloads reproduce exactly, including forecasts, trades, and equity. All 14 live-signal chain links and 30,059 backtest forecast hashes verified. Existing backend/frontend/test source fingerprints were unchanged.
- **Current checks:** all 37 Python tests pass, including the two previously failing WebSocket cleanup tests. Frontend transport test, TypeScript check, and production build pass; the pre-existing bundle-size warning remains.
- **Research finding:** test expectancy is -0.5966 net and -0.1966 before costs. Median target/stop distance ratio is 0.2525; 71 target exits are nonpositive after costs. The frozen baseline has not passed profitability validation.
- **Date correction:** the original test starts with the candle opening **4 September 2026 02:46 UTC** and first forecast at **02:47 UTC**. The earlier 28 August 08:20 statement was a documentation error; the persisted split remains unchanged.

See [VALIDATION_REPORT.md](VALIDATION_REPORT.md), [retained evidence](validation/20260910T142537938267Z/evidence.json), and the [next research protocol](STRATEGY_VALIDATION_PROTOCOL.md). Reproduce this checkpoint with `.\.venv\Scripts\python.exe scripts\validate-checkpoint.py`; it uses read-only SQLite and creates a new evidence directory.

**Next work as of that checkpoint:** the B0/R1 payoff-eligibility study was proposed. The user's subsequent request prioritized the TW-ENTRY-1 entry ablation completed above. The payoff study remains unexecuted.

## Earlier session — retained connection-repair checkpoint

## Connection repair outcome

The existing project was retained. FastAPI and Vite are running locally. REST and WebSocket delivery are restored. Genuine XAUUSD bid/ask quotes reach Overview and animate the Time Wheel. Analysis timezone is **Asia/Aden**; the separately saved broker UTC offset is **+03:00**; canonical storage and validation use **UTC**.

The final functional verification below confirms that the current terminal returned genuine MT5 candles. No synthetic candles or signals were used. The earlier `(-1, "Terminal: Call failed")` condition was not reproduced in this run.

## Final functional verification — 10 September 2026

All checks used the existing running services and the saved +03:00 MT5 profile; the project was not restarted or refactored.

| Acceptance criterion | Result | Evidence |
|---|---|---|
| MT5 live XAUUSD connection | PASS | `/api/health`: connected, XAUUSD, collector errors 0, initialize 1, shutdown 0 |
| Bid / ask / spread display path | PASS | Live snapshots and WebSocket frames contained valid bid, ask and spread; tick age stayed about 2–3 seconds |
| Time Wheel uses genuine live price | PASS | Wheel price equaled the live bid/ask midpoint in every timeframe snapshot |
| Historical candle retrieval | PASS | Direct `/api/datasets/mt5` retrieval succeeded for all seven timeframes |
| Candlestick chart data path | PASS | Each selected timeframe snapshot contained 600 real OHLC candles; frontend TypeScript/build passed |
| M1, M5, M15, M30, H1, H4, D1 | PASS | All seven returned 600 candles and seven available timeframe rows |
| Multi-timeframe analysis | PASS | Analysis objects were present for all seven snapshots; H4 produced a live SELL state |
| Signal generation | PASS | Signal rows were generated and persisted from MT5 candles; neutral states correctly generated no directional target |
| Target / invalidation display | PASS | H4 SELL contained three targets and an invalidation level |
| Real-candle backtest | PASS | Frozen default strategy run on 30,170 genuine XAUUSD M1 candles completed and persisted |

### Backtest evidence

- Dataset: MT5 XAUUSD M1, 30,170 candles, 11 August 2026 14:04 UTC through 10 September 2026 14:03 UTC.
- Split: 80% train / 20% test; corrected from the retained run: first test bar opened 4 September 2026 02:46 UTC, first forecast at 02:47 UTC. The original 28 August 08:20 entry was a documentation error. No parameter optimization was performed.
- Test signals/trades: 6,033 signals / 717 trades.
- Test win rate: 64.71%.
- Test profit factor: 0.3279.
- Test expectancy: -0.5966 quote-price units per trade.
- Test maximum drawdown: 437.36 quote-price units (4.37%).

The negative test expectancy and profit factor are reported as observed results; they are not optimization targets or a performance claim. The prior history error remains a terminal reliability risk to monitor, but history and the complete analysis pipeline passed this verification run.

## Root cause and evidence

### Backend availability

- At the start of this repair, the old backend process was absent and port 8000 refused connections. The previous foreground tool sessions were no longer running. The frontend server also required recovery.
- Available old output contained normal operation, without a Python exception explaining the exit. Session/process lifetime is the likely cause; an application crash is **not established** by the retained evidence.
- `scripts/start-local.ps1` starts hidden background processes with dedicated output/error logs and PID files, and reuses an already healthy application instead of starting another listener. It uses the project virtual environment when available. It is a local launcher, not a Windows service or boot-time supervisor.
- The collector now belongs to application lifespan. REST requests and WebSocket clients read snapshots; they do not initialize MT5 or independently poll it. Collector exceptions are logged without terminating the API.

### Broker timestamps

- Five fresh pre-normalization observations showed raw broker epoch minus system UTC differences of **10798.73–10799.73 seconds**, corroborating the earlier approximately 10798-second observation. Exact observations are in [BROKER_TIME_EVIDENCE.json](BROKER_TIME_EVIDENCE.json).
- The old UTC assumption made legitimate broker wall-clock epochs appear to be future data. The separately persisted +03:00 correction resolves that error on this connection.
- A stale initial cached tick was explicitly excluded from offset confirmation. The offset is never recalculated from each tick; doing that would conceal genuine staleness.

### Candle retrieval — prior failure and current verification

- Both MT5 `copy_rates_from_pos` and `copy_rates_range` fail for XAUUSD and EURUSD, including requests for a single M1 candle. Trying both UTC and broker-adjusted query ranges did not resolve it.
- The local connector was updated from 5.0.5388 to **5.0.6180** in `.venv`; this did not fix rates. The terminal reported connected, build 6182, maximum bars 100000 during a bounded diagnostic probe.
- The terminal's on-disk logs/history had not changed since its earlier exit, despite subsequent quote activity. Its data directory is outside the task's writable roots. Lack of cache/log write access is a **suspected contributing cause, not a proven diagnosis**.
- Write permission was requested only for the existing terminal data directory and was not granted. No permissions, Windows clock, broker account, orders, or history files were changed to bypass this restriction.
- Further verification requires a normally running MT5 terminal with working history/cache access. Then use Market data → Fetch MT5 history to verify and retain actual candles. A successful tick feed alone does not establish history availability.
- On 10 September 2026, the same running terminal returned 30,170 M1, 6,041 M5, 2,013 M15, 1,006 M30, 503 H1, 131 H4 and 21 D1 bars through the history API. The earlier failure is therefore intermittent or environment-dependent; no code was changed to fabricate or bypass history.

## Timestamp normalization contract

1. `FeedSettings.broker_utc_offset` is a fixed, explicit `±HH:MM` setting. Generic/unconfirmed feeds default to `+00:00`, consistent with the documented MT5 UTC convention. Only this evidence-backed saved connection uses `+03:00`.
2. At MT5 ingress: `normalized_epoch = original_broker_epoch - configured_offset_seconds`. Millisecond ticks subtract the offset multiplied by 1000. CSV UTC timestamps do not receive this correction.
3. Preserve original broker epoch and millisecond epoch, original broker wall-clock time with its offset, normalized UTC epoch/ISO time, configured offset, and normalization rule in the tick payload and database. Candles preserve raw epoch and both time representations.
4. Future-data validation runs **after** normalization. The existing 120-second tolerance remains. Truly future normalized ticks are rejected; genuinely old ticks remain old and are flagged stale after 120 seconds.
5. Historical API requests accept timezone-aware UTC bounds, translate query bounds to the configured broker epoch convention, normalize returned bars once, and retain only bars closed within the requested interval. Broker-aligned H4/D1 sessions are not forcibly re-bucketed to UTC midnight.
6. The saved strategy's **analysis timezone** is Asia/Aden. It controls time-cycle calculations and related display; it does not determine how feed timestamps are decoded. Changing it does not change the broker correction. The UI label explicitly says “Analysis timezone (IANA) · not broker time.”
7. Candle normalization is covered by controlled adapter tests. Actual broker candle timestamp semantics remain unverified until the terminal returns history. A fixed offset is not an automatic DST rule; broker clock changes require a separately verified profile adjustment.

## URLs and connection ownership

- Frontend: `http://127.0.0.1:5173/`
- REST base: `http://127.0.0.1:8000`, overridable with `VITE_API_URL`.
- WebSocket: `ws://127.0.0.1:8000/ws`, derived from the same API base, with timeframe and per-tab client ID.
- The frontend owns one current socket and one pending reconnect timer. Delays increase through 1, 2, 4, 8, 16, and 30 seconds; valid received data resets the delay. Unmount, timeframe changes and hot reload dispose of old ownership and timers. Late callbacks cannot replace newer state.
- The server replaces a socket with the same client ID using close code 4001; the replaced client does not retry against its successor. Receive tasks clean up disconnected clients. Model settings changes no longer recreate a socket.
- Settings are reloaded after WebSocket recovery if initial REST loading happened while the backend was offline.
- The observed dashboard had **one identified client**. Two pre-existing anonymous/legacy consumers also remained connected. Their origins could not be established from the available browser inventory. They stayed stable and did not create additional MT5 collectors. Global “only one socket on the machine” is therefore **not claimed**; older previews should be refreshed to adopt client identification.

## Verification results

The read-only live check ran for **181.30 seconds**; full samples are in [CONNECTION_STABILITY.json](CONNECTION_STABILITY.json).

| Check | Result |
|---|---|
| Backend PID stayed unchanged | Yes, 40904 during the final test |
| WebSocket messages | 91 on one test connection |
| Successful REST checks | 93 |
| Distinct bid/ask pairs | 59 |
| Distinct normalized tick timestamps | 67 |
| All bid/ask pairs valid | Yes |
| Maximum observed tick age | 6.18 seconds |
| Stale/future/feed error samples | 0 |
| MT5 initialize/shutdown calls during test | 0 / 0 |
| Collector errors | 0 |
| Connection lifecycle | Test socket opened/closed; one browser hot-reload replacement during the final UI edit; no rapid retry loop |
| Tick calls during test | 89, consistent with one approximately two-second collector |
| Actual history available | Yes in final verification — all seven MT5 timeframe requests passed |

An earlier independent 181.49-second run also passed (91 messages, 56 quote pairs, zero stale/error samples); it is retained in `CONNECTION_STABILITY_INITIAL.json`. The final controlled restart automatically restored Asia/Aden, +03:00 and MT5. The final API PID was 40904. The PID in the launcher file may identify the Windows virtual-environment bootstrap process; `/api/health` identifies the serving process.

The backend process had initialized MT5 once and had not shut it down. A separate bounded diagnostic process used one initialize/shutdown pair before the stability window. No repeated initialize/shutdown loop was present. Speaker audio was not recorded, so the absence of an audible terminal sound is not independently asserted.

The frontend transport and build checks confirmed `BACKEND ONLINE` data flow, changing genuine gold quotes and changing wheel angles. Snapshot data supplies bid, ask, spread, data age, normalized last tick, original broker time/epoch, normalized UTC epoch, broker offset and analysis timezone. All seven candle series and analysis states were returned; no synthetic market data was introduced.

- The targeted storage/feed and mathematics Python tests pass. The full 37-test run had 35 passes and two existing TestClient WebSocket cleanup failures (`active` connection count remained 1 after context exit); these are unrelated to the final data-pipeline verification and did not affect the running service.
- The frontend transport test passes: single-owner behavior, stale callback suppression, retry cancellation, increasing/capped delays, reset on valid message, endpoint construction and duplicate replacement.
- TypeScript and production build pass. Vite retains a nonfatal bundle-size warning; no large refactor was made for it.

## Files changed or added for this repair

- `backend/app/time_normalization.py`: explicit broker-time contract and guards.
- `backend/app/config.py`: separately validated feed profile.
- `backend/app/data.py`: idempotent MT5 lifecycle, normalization, raw-time audit, diagnostics and history conversion.
- `backend/app/database.py`: persistent feed settings alongside existing immutable research records.
- `backend/app/service.py`: single collector and snapshot cache, live-feed audit fields, saved profile restoration.
- `backend/app/main.py`: lifecycle collection, health diagnostics, feed settings REST API, WebSocket ownership/cleanup.
- `requirements.txt`: updated optional MT5 connector pin.
- `frontend/lib/api.ts`, `frontend/lib/live.ts`: common endpoint configuration and bounded socket reconnect behavior.
- `frontend/app/main.tsx`, `frontend/app/page.tsx`: socket lifecycle integration, recovery state and live data props.
- `frontend/components/dashboard/Settings.tsx`, `DataPanel.tsx`, `frontend/app/dashboard.css`: clear analysis/broker labels and time/quote audit display.
- `frontend/vite-env.d.ts`, `frontend/tsconfig.json`, `frontend/package.json`: environment typing and transport test command.
- `tests/test_system.py`, `tests/test_time_connection.py`, `frontend/tests/live.test.mjs`: connection/time regression coverage.
- `scripts/start-local.ps1`, `scripts/check-stability.py`: repeatable launch and read-only live verification.
- `docs/BROKER_TIME_EVIDENCE.json`, `docs/CONNECTION_STABILITY.json`, `docs/CONNECTION_STABILITY_INITIAL.json`, this document: evidence and status.
- Local `.venv` and saved runtime settings were updated. Existing research formulas, chart code, anchors/increments, backtester and immutable records were retained.

## Local commands (PowerShell, from project root)

```powershell
.\scripts\start-local.ps1
Invoke-RestMethod http://127.0.0.1:8000/api/health
Get-Content .\runtime\backend.stderr.log -Tail 40
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
npm --prefix frontend test
npm --prefix frontend run build
.\.venv\Scripts\python.exe scripts\check-stability.py --seconds 180
```

The live checker records actual observations and does not connect, disconnect or initialize MT5. It does not claim history success when only quotes are available. Preserve `.venv`, `runtime/timewheel.sqlite3`, and the saved broker profile when restarting.

## References

- [MetaQuotes: copy_rates_from](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py): documented UTC convention and dependence on terminal history/max-bars settings. The observed deviation is handled explicitly for this broker profile.
- [Official MetaTrader5 package](https://pypi.org/project/MetaTrader5/): connector distribution. A connector update was tested, not assumed to solve the terminal error.

## Controlled DEMO MT5 execution checkpoint — 10 September 2026

Production strategy formulas, thresholds, research artifacts, and defaults are unchanged. A backend-owned M15 execution layer consumes only the persisted displayed production signal. It defaults to **TRADING DISABLED** on every backend start; the frontend has no raw order endpoint.

- MT5 positively reports account `52960017`, server `ICMarketsSC-Demo`, `trade_mode=0` (MT5 DEMO), and Algo Trading available. A non-DEMO or unconfirmed account is rejected before enable and immediately before every send.
- Fixed M15 settings: 0.01 lot, one XAUUSD position maximum, and three submitted orders per UTC day. Durable unique signal reservations plus an execution lock block duplicates across refresh/reconnect/restart.
- Existing production BUY/STRONG BUY maps to BUY and SELL/STRONG SELL maps to SELL; NEUTRAL does nothing. Existing invalidation and Target 1 are sent as SL/TP only after volume, quote, direction, and broker stop-level validation.
- Dry-run M15 construction succeeded with SL `4344.93` and TP `4365.00`; no `order_send` call was made. Execution is currently disabled. Two pre-existing XAUUSD positions are present and untouched, so the maximum-position guard blocks any new entry.
- UI/API controls: DEMO AUTO TRADING (`POST /api/execution/enable`), STOP AUTO TRADING (`POST /api/execution/stop`), status and durable execution logs. Stop blocks new orders only and never closes a position.

## Editable DEMO execution settings checkpoint — 10 September 2026

The strategy remains unchanged. DEMO AUTO TRADING controls now persist independently in SQLite and restore on backend restart, while the enabled/disabled trading state always resets to **TRADING DISABLED**.

- Editable settings: execution timeframe, fixed lot, daily trade cap or disabled, 1/2/3/5/10 open-position cap, cooldown or disabled, maximum spread or disabled, duplicate-signal protection, one-trade-per-unique-signal, and fixed strategy-derived SL/TP modes.
- Defaults restored: M15, 0.01 lot, three trades/day, one open position, no cooldown, no spread cap, both duplicate controls enabled, existing strategy invalidation for SL, and existing Target 1 for TP.
- A live status panel reports enabled/disabled state, active settings, positions/cap, daily count/cap, current displayed signal, last persisted execution, and the current blocking reason.
- Verification after backend restart: DEMO account remains positively confirmed; auto trading is disabled; no order was sent while these settings were implemented. Targeted execution tests (including persistence and restart-disabled behavior) and the frontend production build pass.
- Multi-timeframe execution is now represented by persisted `selected_timeframes` (default `['M15']`) and the collector evaluates each selected timeframe independently. Per-timeframe position caps are supported; total open positions may be set to 1/2/3/5/10 or unlimited.
- Opposite-direction entries default to blocked. Enabling them requires MT5 retail hedging margin mode; netting accounts are rejected for incompatible simultaneous BUY/SELL behavior.

## Execution repair checkpoint — 13 September 2026

High-severity runtime and execution safety repairs are recorded in [EXECUTION_REPAIR_REPORT.md](EXECUTION_REPAIR_REPORT.md). The launcher now performs stale-PID/listener checks and starts one detached backend/frontend process. Execution records reconcile against MT5 history where position linkage is available; ownership uses the DTW magic/comment and external positions remain separate. Market tradeability and broker bid/ask stop/freeze validation run before every send and are repeated immediately before order submission. WebSocket registration cleanup is idempotent and the full Python suite passes.

No order was sent. Auto trading remains disabled after restart and during the read-only runtime check. Current terminal diagnostics show DEMO account identification, but Algo Trading permission and quote freshness are not currently sufficient for enablement.

## Multi-symbol hardening checkpoint — 13 September 2026

The backend now discovers compatible broker symbols dynamically through MT5, persists independent symbol profiles, and switches EURUSD/XAUUSD without restarting the backend. Execution records have a native indexed `symbol` column with safe migration/backfill from existing request payloads; all eight retained execution records are now identified as XAUUSD. Symbol-scoped daily and per-timeframe execution queries use this column, while strategy identifiers retain symbol and timeframe in their scope.

Read-only switching XAUUSD → EURUSD → XAUUSD passed with DEMO execution still disabled. Python tests (56/56), frontend tests, TypeScript check, and production build passed. Existing XAUUSD behavior and strategy formulas were preserved; no order was sent.
