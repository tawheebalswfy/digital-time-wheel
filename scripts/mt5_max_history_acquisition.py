"""Read-only XAUUSD MT5 history acquisition.  Deliberately has no order APIs."""
from __future__ import annotations

import csv
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5


ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "data" / "history"
SYMBOL = "XAUUSD"
TIMEFRAMES = {"M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600}
REQUESTS = (1_000, 5_000, 10_000, 25_000, 50_000, 100_000)
FIELDS = ("time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume")


def iso(timestamp: int | None) -> str | None:
    return None if timestamp is None else datetime.fromtimestamp(int(timestamp), timezone.utc).isoformat()


def records(raw):
    if raw is None or not len(raw):
        return []
    return [{key: row[key].item() if hasattr(row[key], "item") else row[key] for key in raw.dtype.names} for row in raw]


def query(timeframe: str, count: int) -> tuple[list[dict], dict]:
    raw = mt5.copy_rates_from_pos(SYMBOL, getattr(mt5, "TIMEFRAME_" + timeframe), 0, count)
    rows = records(raw)
    return rows, {
        "requested_bars": count,
        "returned_bars": len(rows),
        "first_utc": iso(rows[0]["time"]) if rows else None,
        "last_utc": iso(rows[-1]["time"]) if rows else None,
        "mt5_last_error": list(mt5.last_error()),
    }


def paginate(timeframe: str, page_size: int = 50_000, max_pages: int = 20) -> tuple[list[dict], list[dict]]:
    """Non-overlapping position pages; dedupe timestamps defensively."""
    all_rows, audit = [], []
    constant = getattr(mt5, "TIMEFRAME_" + timeframe)
    for page in range(max_pages):
        position = page * page_size
        raw = mt5.copy_rates_from_pos(SYMBOL, constant, position, page_size)
        rows = records(raw)
        audit.append({
            "position": position, "requested_bars": page_size, "returned_bars": len(rows),
            "first_utc": iso(rows[0]["time"]) if rows else None,
            "last_utc": iso(rows[-1]["time"]) if rows else None,
            "mt5_last_error": list(mt5.last_error()),
        })
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
    unique = {int(row["time"]): row for row in all_rows}
    return [unique[key] for key in sorted(unique)], audit


def quality(rows: list[dict], seconds: int) -> dict:
    ordered = sorted(rows, key=lambda row: int(row["time"]))
    times = [int(row["time"]) for row in ordered]
    duplicates = len(times) - len(set(times))
    invalid_ohlc = invalid_volume = 0
    for row in ordered:
        try:
            o, h, l, c = (float(row[key]) for key in ("open", "high", "low", "close"))
            if not all(math.isfinite(value) and value > 0 for value in (o, h, l, c)) or l > min(o, c) or h < max(o, c) or l > h:
                invalid_ohlc += 1
            if not math.isfinite(float(row.get("tick_volume", 0))) or float(row.get("tick_volume", 0)) <= 0:
                invalid_volume += 1
        except (KeyError, TypeError, ValueError):
            invalid_ohlc += 1
            invalid_volume += 1
    gaps = [later - earlier for earlier, later in zip(times, times[1:]) if later - earlier > seconds]
    return {
        "first_utc": iso(times[0]) if times else None,
        "last_utc": iso(times[-1]) if times else None,
        "total_candles": len(ordered), "duplicates": duplicates,
        "invalid_ohlc_rows": invalid_ohlc, "zero_or_invalid_volume_rows": invalid_volume,
        "gap_count": len(gaps), "longest_gap_seconds": max(gaps, default=0),
        "monotonic_timestamp_check": all(later > earlier for earlier, later in zip(times, times[1:])),
    }


def resample(lower_rows: list[dict], lower_seconds: int, target_seconds: int) -> list[dict]:
    """Aggregate only complete, aligned lower-TF buckets: no future data is used."""
    factor = target_seconds // lower_seconds
    grouped: dict[int, list[dict]] = {}
    for row in lower_rows:
        timestamp = int(row["time"])
        grouped.setdefault(timestamp - timestamp % target_seconds, []).append(row)
    result = []
    for bucket, items in sorted(grouped.items()):
        items.sort(key=lambda row: int(row["time"]))
        expected = [bucket + lower_seconds * index for index in range(factor)]
        if [int(row["time"]) for row in items] != expected:
            continue
        result.append({"time": bucket, "open": items[0]["open"], "high": max(row["high"] for row in items),
                       "low": min(row["low"] for row in items), "close": items[-1]["close"],
                       "tick_volume": sum(row["tick_volume"] for row in items), "spread": items[-1]["spread"],
                       "real_volume": sum(row["real_volume"] for row in items)})
    return result


def save(timeframe: str, rows: list[dict]) -> str:
    HISTORY.mkdir(parents=True, exist_ok=True)
    destination = HISTORY / f"XAUUSD_{timeframe}.csv"
    if destination.exists():
        backup = destination.with_name(f"{destination.stem}.backup_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}{destination.suffix}")
        shutil.copy2(destination, backup)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: int(row["time"])))
    return str(destination)


def span_seconds(rows: list[dict]) -> int:
    return int(rows[-1]["time"]) - int(rows[0]["time"]) if len(rows) > 1 else 0


def main():
    result = {"symbol": SYMBOL, "read_only": True, "api_policy": "Uses only symbol_select, terminal_info, symbol_info, and copy_rates_from_pos; no order API is imported or called.", "timeframes": {}}
    if not mt5.initialize(timeout=10_000):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        selected = mt5.symbol_select(SYMBOL, True)
        for timeframe, seconds in TIMEFRAMES.items():
            attempts, best_rows, needs_pages = [], [], False
            for requested in REQUESTS:
                rows, audit = query(timeframe, requested)
                attempts.append(audit)
                if rows:
                    best_rows = rows
                if len(rows) < requested or audit["mt5_last_error"][0] != 1:
                    needs_pages = True
                    break
            pages = []
            if needs_pages:
                paged_rows, pages = paginate(timeframe)
                if len(paged_rows) > len(best_rows):
                    best_rows = paged_rows
            result["timeframes"][timeframe] = {"depth_probe": attempts, "pagination": pages, "direct_rows": best_rows, "seconds": seconds}

        # If direct higher timeframes are shallower, use only complete M5 bars to causally extend them.
        m5_rows = result["timeframes"]["M5"]["direct_rows"]
        for timeframe in ("M15", "M30", "H1"):
            direct = result["timeframes"][timeframe]["direct_rows"]
            derived = resample(m5_rows, TIMEFRAMES["M5"], TIMEFRAMES[timeframe]) if m5_rows else []
            if span_seconds(derived) > span_seconds(direct):
                final_rows, source = derived, "CAUSALLY_RESAMPLED_MT5"
            else:
                final_rows, source = direct, "DIRECT_MT5"
            result["timeframes"][timeframe].update({"source": source, "final_rows": final_rows})
        for timeframe in ("M1", "M5"):
            result["timeframes"][timeframe].update({"source": "DIRECT_MT5", "final_rows": result["timeframes"][timeframe]["direct_rows"]})

        for timeframe, data in result["timeframes"].items():
            final_rows = data.pop("final_rows")
            data.pop("direct_rows")
            data["quality"] = quality(final_rows, data.pop("seconds"))
            data["saved_path"] = save(timeframe, final_rows)
        result.update({"terminal_connected": bool(getattr(terminal, "connected", False)), "server": getattr(account, "server", None), "symbol_selected": bool(selected and getattr(mt5.symbol_info(SYMBOL), "visible", False))})
    finally:
        mt5.shutdown()
    audit = HISTORY / f"XAUUSD_acquisition_audit_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    audit.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "timeframes"} | {"timeframes": {tf: {key: value for key, value in data.items() if key not in {"depth_probe", "pagination"}} for tf, data in result["timeframes"].items()}}, indent=2))


if __name__ == "__main__":
    main()
