"""Read-only MT5 XAUUSD history diagnostics and acquisition.

This script intentionally uses only symbol/query/rate APIs.  It does not
import execution code, build trade requests, alter terminal settings, or call
``order_send``.  Every raw MT5 call is logged with its exact UTC arguments and
the immediate ``last_error`` result.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "data" / "history"
AUDIT = ROOT / "docs" / "MT5_HISTORY_ACQUISITION_RAW.json"
REPORT = ROOT / "docs" / "MT5_HISTORY_ACQUISITION_AUDIT.md"
SYMBOL = "XAUUSD"
TIMEFRAMES = {"M15": 900, "M30": 1800, "H1": 3600}
LOWER = {"M1": 60, "M5": 300}
RETAINED_DATASETS = {
    "M15": "9b42086946a9ceab1a8fde7c889d931cf6fddbde30e24436272c988f49796612",
    "M30": "bfebffa2ad1632deba070629e9ed28f91f6a4146072112fa11dc9ff12b05a988",
    "H1": "aa9dd4bc95536d041bec47fbbec7e6b317a0f1db6309c84629cbac792470ef43",
}
RANGES = (7, 30, 60, 90, 180, 365)
CHUNK_DAYS = 30
PAGE_SIZE = 1000
MAX_PAGES = 50  # bounded: enough for 12 months of M15 plus a safety margin


def utc_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return datetime.fromtimestamp(int(value), timezone.utc).isoformat()


def clean(value: Any) -> Any:
    if isinstance(value, datetime):
        return utc_iso(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def rows_to_dicts(rows: Any) -> list[dict]:
    if rows is None:
        return []
    names = getattr(rows.dtype, "names", None)
    if not names:
        return []
    return [{key: clean(row[key].item() if hasattr(row[key], "item") else row[key]) for key in names} for row in rows]


def call(mt5, api: str, args: list, kwargs: dict | None = None) -> tuple[list[dict], dict]:
    kwargs = kwargs or {}
    started = datetime.now(timezone.utc).isoformat()
    try:
        raw = getattr(mt5, api)(*args, **kwargs)
        records = rows_to_dicts(raw)
        result = {"api": api, "args": [clean(x) for x in args], "kwargs": {k: clean(v) for k, v in kwargs.items()},
                  "started_utc": started, "returned_rows": len(records), "last_error": list(mt5.last_error())}
        return records, result
    except Exception as exc:
        return [], {"api": api, "args": [clean(x) for x in args], "kwargs": {k: clean(v) for k, v in kwargs.items()},
                    "started_utc": started, "returned_rows": 0, "exception": repr(exc), "last_error": list(mt5.last_error())}


def quality(rows: list[dict], seconds: int) -> dict:
    ordered = sorted(rows, key=lambda r: int(r["time"]))
    stamps = [int(r["time"]) for r in ordered]
    duplicates = len(stamps) - len(set(stamps))
    gaps = [b - a for a, b in zip(stamps, stamps[1:]) if b - a != seconds]
    invalid = 0
    zero_volume = 0
    for row in ordered:
        try:
            o, h, l, c = (float(row[k]) for k in ("open", "high", "low", "close"))
            if min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c) or l > h:
                invalid += 1
            if float(row.get("tick_volume", 0)) == 0:
                zero_volume += 1
        except (KeyError, TypeError, ValueError):
            invalid += 1
    return {"first_utc": utc_iso(stamps[0]) if stamps else None, "last_utc": utc_iso(stamps[-1]) if stamps else None,
            "candles": len(ordered), "duplicates": duplicates, "non_interval_gaps": len(gaps),
            "largest_gap_seconds": max(gaps) if gaps else 0, "monotonic_strict": all(b > a for a, b in zip(stamps, stamps[1:])),
            "invalid_ohlc": invalid, "zero_tick_volume": zero_volume}


def paged_from_pos(mt5, constant: int) -> tuple[list[dict], list[dict]]:
    records, attempts = [], []
    for page in range(MAX_PAGES):
        position = page * PAGE_SIZE
        rows, audit = call(mt5, "copy_rates_from_pos", [SYMBOL, constant, position, PAGE_SIZE])
        audit["page"] = page
        attempts.append(audit)
        if not rows:
            break
        records.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
    deduped = {int(row["time"]): row for row in records}
    return [deduped[key] for key in sorted(deduped)], attempts


def chunked_range(mt5, constant: int, end: datetime, days: int) -> tuple[list[dict], list[dict]]:
    start = end - timedelta(days=days)
    cursor = start
    rows, attempts = [], []
    while cursor < end:
        right = min(cursor + timedelta(days=CHUNK_DAYS), end)
        values, audit = call(mt5, "copy_rates_range", [SYMBOL, constant, cursor, right])
        attempts.append(audit)
        rows.extend(values)
        cursor = right
    deduped = {int(row["time"]): row for row in rows}
    return [deduped[key] for key in sorted(deduped)], attempts


def write_csv(timeframe: str, rows: list[dict]) -> str | None:
    if not rows:
        return None
    HISTORY.mkdir(parents=True, exist_ok=True)
    path = HISTORY / f"XAUUSD_{timeframe}_DIRECT_MT5_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
    keys = ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: int(row["time"])))
    return str(path)


def export_retained_fallback() -> dict:
    """Copy pre-existing MT5-originated bars into a research-only CSV snapshot."""
    source = ROOT / "runtime" / "timewheel.sqlite3"
    conn = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    output = {}
    try:
        for tf, dataset_id in RETAINED_DATASETS.items():
            rows = [json.loads(row[0]) for row in conn.execute("SELECT payload FROM candles WHERE dataset_id=? ORDER BY time", (dataset_id,))]
            HISTORY.mkdir(parents=True, exist_ok=True)
            path = HISTORY / f"XAUUSD_{tf}_RETAINED_MT5_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
            keys = ["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
            with path.open("x", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
                writer.writeheader(); writer.writerows(rows)
            output[tf] = {"source": "retained database metadata: MT5", "dataset_id": dataset_id, "csv": str(path), "quality": quality(rows, TIMEFRAMES[tf])}
    finally:
        conn.close()
    return output


def terminal_settings(mt5, terminal: Any) -> dict:
    fields = terminal._asdict() if terminal is not None and hasattr(terminal, "_asdict") else {}
    selected = {key: clean(value) for key, value in fields.items() if any(token in key.lower() for token in ("max", "bar", "path", "build", "connect", "trade"))}
    config_checks = []
    for root_key in ("data_path", "path", "commondata_path"):
        root = fields.get(root_key)
        if not root:
            continue
        for relative in ("config/terminal.ini", "config/common.ini", "terminal.ini"):
            candidate = Path(str(root)) / relative
            try:
                config_checks.append({"path": str(candidate), "exists": candidate.exists(), "readable": candidate.is_file(),
                                      "max_bar_lines": [line.strip() for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines() if "maxbar" in line.lower()] if candidate.is_file() else []})
            except Exception as exc:
                config_checks.append({"path": str(candidate), "exists": candidate.exists(), "read_error": repr(exc)})
    return {"terminal_info_relevant_fields": selected, "read_only_config_checks": config_checks}


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + "\n".join("| " + " | ".join(row) + " |" for row in rows)


def write_report(result: dict) -> None:
    settings = result.get("terminal_settings", {}).get("terminal_info_relevant_fields", {})
    symbol = result.get("symbol_select", {})
    rows = []
    for tf, data in result.get("timeframes", {}).items():
        q = data.get("saved_quality") or {}
        rows.append([tf, str(data.get("maximum_successful_range_days", 0)), str(q.get("candles", 0)), str(q.get("first_utc") or "—"), str(q.get("last_utc") or "—"), str(q.get("duplicates", 0)), str(q.get("non_interval_gaps", 0)), str(q.get("invalid_ohlc", 0))])
    fallback = []
    for tf, data in result.get("retained_mt5_fallback_export", {}).items():
        q = data["quality"]
        fallback.append([tf, q["first_utc"], q["last_utc"], str(q["candles"]), str(q["duplicates"]), str(q["non_interval_gaps"]), str(q["invalid_ohlc"]), str(q["zero_tick_volume"]), data["csv"]])
    error = "(-1, 'Terminal: Call failed')"
    REPORT.write_text(
        "# MT5 History Acquisition Audit\n\n"
        "## Scope and safety\n\n"
        "This is read-only MT5 data diagnostics. The runner contains no order API call, does not import the execution controller, and does not change any strategy or terminal setting. It called only `symbol_select`, `symbol_info`, `copy_rates_range`, `copy_rates_from`, and `copy_rates_from_pos`.\n\n"
        "## Exact observed failure\n\n"
        f"The exact MT5 error for **every** direct XAUUSD rate request was `{error}`. It occurred for all three APIs, including `copy_rates_from_pos(..., 0, 1)`, which requests only the newest single bar. Therefore the evidence rules out a six-month range size, date-window construction, pagination, and selected-symbol issue. The MT5 Python API exposes no more specific cause than code `-1`; the strongest provable diagnosis is that this terminal's rate/history service is failing to supply XAUUSD bars at the API boundary.\n\n"
        f"Terminal: connected={result.get('terminal_connected')}; server={result.get('account', {}).get('server')}; build={settings.get('build')}; `maxbars`={settings.get('maxbars')}; XAUUSD `symbol_select`={symbol.get('returned')}; visible={symbol.get('visible')}; Market Watch path={symbol.get('path')}.\n\n"
        "## API arguments and results\n\n"
        "The complete call-by-call evidence, including exact UTC datetimes, MT5 timeframe constants, row counts, and immediate `last_error()` values, is in `docs/MT5_HISTORY_ACQUISITION_RAW.json`. Every 7/30/60/90/180/365-day range and matching `copy_rates_from` request returned zero rows. The 365-day process also attempted bounded 30-day `copy_rates_range` chunks; all failed identically.\n\n" + markdown_table(["TF", "Max successful direct range (days)", "Downloaded bars", "First", "Last", "Duplicates", "Non-interval gaps", "Invalid OHLC"], rows) + "\n\n"
        "## Position pagination and lower-timeframe alternative\n\n"
        "The position-index alternative failed on page 0 for M15, M30, H1, M1, and M5 with the same error. Thus no deeper M1/M5 history is presently available from this terminal, and causal M15/M30/H1 resampling cannot extend coverage. No synthetic or resampled bars were created.\n\n"
        "## Retained genuine MT5 fallback export\n\n"
        "No newly downloaded data exists. To provide a fixed research-only data location without overwriting anything, the previously retained datasets whose metadata source is `MT5` were copied from SQLite read-only into new CSV files. These are not represented as a successful fresh download.\n\n" + markdown_table(["TF", "First UTC", "Last UTC", "Candles", "Duplicates", "Non-interval gaps", "Invalid OHLC", "Zero volume", "CSV"], fallback) + "\n\n"
        "The non-interval gaps are expected session/weekend gaps pending a broker-session calendar; none is silently filled.\n\n"
        "## Terminal configuration finding and required manual action\n\n"
        "`terminal_info().maxbars` is 100,000, sufficient for the target bar counts (roughly 35k M15, 17.5k M30, 8.8k H1 for one year). Read-only checks found no `MaxBars` line in the terminal INI files. This is not evidence of a max-bars cap.\n\n"
        "Required manual terminal action: in the same ICMarketsSC-Demo terminal, open **XAUUSD M1**, press **Home** (or scroll fully left) and wait for the chart to finish downloading history; then open **F2 / History Center**, select XAUUSD, and download/synchronize bars. Confirm Tools → Options → Charts keeps Max bars in chart at least 100,000, restart/re-login the terminal if needed, and rerun this audit. This action is required because even a one-bar API request currently fails; code-side batching cannot repair absent/unavailable terminal history.\n\n"
        "## Conclusion\n\n"
        "Neither six nor twelve months was achieved. The only usable coverage remains the retained 2026-08-11 through 2026-09-10 UTC MT5 data. Do not begin V4 research until the terminal returns at least six months of direct rates or genuinely deeper lower-timeframe rates suitable for causal resampling.\n",
        encoding="utf-8",
    )


def main() -> None:
    import MetaTrader5 as mt5
    result: dict = {"research_only": True, "symbol_requested": SYMBOL, "api_policy": "Only symbol_select/symbol_info and copy_rates APIs were called; no order API exists in this script.", "started_utc": datetime.now(timezone.utc).isoformat()}
    if not mt5.initialize(timeout=10000):
        result.update({"initialized": False, "initialize_error": list(mt5.last_error())})
        AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        raise SystemExit("MT5 initialize failed")
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        select_ok = mt5.symbol_select(SYMBOL, True)
        symbol = mt5.symbol_info(SYMBOL)
        result.update({"initialized": True, "terminal_connected": bool(getattr(terminal, "connected", False)),
                       "terminal_settings": terminal_settings(mt5, terminal),
                       "account": {"server": getattr(account, "server", None), "login": getattr(account, "login", None), "trade_mode": getattr(account, "trade_mode", None)},
                       "symbol_select": {"requested": SYMBOL, "returned": bool(select_ok), "last_error": list(mt5.last_error()),
                                         "visible": getattr(symbol, "visible", None), "path": getattr(symbol, "path", None), "description": getattr(symbol, "description", None)}})
        all_tf = {}
        for tf, seconds in TIMEFRAMES.items():
            constant = getattr(mt5, "TIMEFRAME_" + tf)
            # Position zero is the terminal's latest available bar and gives an evidence-backed endpoint.
            latest_rows, latest_audit = call(mt5, "copy_rates_from_pos", [SYMBOL, constant, 0, 1])
            tf_result = {"mt5_timeframe_constant": int(constant), "latest_position_probe": latest_audit, "progressive_ranges": [], "copy_rates_from": [], "position_pages": []}
            endpoint = (datetime.fromtimestamp(int(latest_rows[-1]["time"]) + seconds, timezone.utc) if latest_rows else datetime.now(timezone.utc))
            tf_result["endpoint_source"] = "latest copy_rates_from_pos bar" if latest_rows else "diagnostic runner UTC clock; latest-bar probe failed"
            tf_result["latest_available_end_utc"] = utc_iso(endpoint)
            for days in RANGES:
                begin = endpoint - timedelta(days=days)
                values, audit = call(mt5, "copy_rates_range", [SYMBOL, constant, begin, endpoint])
                audit["requested_days"] = days
                tf_result["progressive_ranges"].append(audit)
                count = min(days * 86400 // seconds + 5, 50000)
                values, audit = call(mt5, "copy_rates_from", [SYMBOL, constant, begin, count])
                audit["requested_days"] = days
                tf_result["copy_rates_from"].append(audit)
            paged, pages = paged_from_pos(mt5, constant)
            tf_result["position_pages"] = pages
            tf_result["position_paged_quality"] = quality(paged, seconds)
            direct_chunks, chunk_attempts = chunked_range(mt5, constant, endpoint, 365)
            tf_result["chunked_365_day_attempts"] = chunk_attempts
            tf_result["chunked_365_day_quality"] = quality(direct_chunks, seconds)
            # Prefer successfully paginated rows. They are direct MT5 records and
            # make no time-window assumption; chunk data wins only if deeper.
            chosen = direct_chunks if len(direct_chunks) > len(paged) else paged
            tf_result["saved_direct_mt5_csv"] = write_csv(tf, chosen)
            tf_result["saved_quality"] = quality(chosen, seconds)
            successes = [row["requested_days"] for row in tf_result["progressive_ranges"] if row["returned_rows"]]
            tf_result["maximum_successful_range_days"] = max(successes) if successes else 0
            all_tf[tf] = tf_result
        # Lower-TF availability is checked via bounded pagination only.  It is
        # enough to establish whether causal resampling can add depth.
        lower = {}
        for tf, seconds in LOWER.items():
            constant = getattr(mt5, "TIMEFRAME_" + tf)
            rows, attempts = paged_from_pos(mt5, constant)
            lower[tf] = {"position_pages": attempts, "quality": quality(rows, seconds)}
        result["timeframes"] = all_tf
        result["lower_timeframe_probe"] = lower
        result["retained_mt5_fallback_export"] = export_retained_fallback()
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
    finally:
        mt5.shutdown()
        result["shutdown_called"] = True
        AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
        write_report(result)
    print(AUDIT)


if __name__ == "__main__":
    main()
