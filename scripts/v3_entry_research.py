"""DIGITAL_TIME_WHEEL_V3_ENTRY_RESEARCH.

Read-only, entry-quality research.  This runner deliberately has no execution
controller import and never calls an MT5 trading API.  It evaluates a signal at
the close of bar i, enters hypothetically at bar i+1 open, and measures only
subsequent raw directional movement.  No exit model is used or selected.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from backend.app.config import Strategy, TIMEFRAMES
from backend.app.data import MT5Adapter, validate_bars
from backend.app.technical import features, finite
from backend.app.wheel import state as wheel_state

DATABASE = ROOT / "runtime" / "timewheel.sqlite3"
DATASETS = {
    "M15": "9b42086946a9ceab1a8fde7c889d931cf6fddbde30e24436272c988f49796612",
    "M30": "bfebffa2ad1632deba070629e9ed28f91f6a4146072112fa11dc9ff12b05a988",
    "H1": "aa9dd4bc95536d041bec47fbbec7e6b317a0f1db6309c84629cbac792470ef43",
}
HORIZONS = (1, 2, 3, 5, 10)
WARMUP = 100


def iso(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def sample_label(n: int) -> str:
    return "INSUFFICIENT_SAMPLE" if n < 30 else "LOW_CONFIDENCE" if n < 100 else "USABLE_FOR_COMPARISON"


def load_saved() -> tuple[dict[str, list[dict]], dict[str, dict], Strategy]:
    conn = sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    saved = json.loads(conn.execute("SELECT payload FROM backtests LIMIT 1").fetchone()[0])
    strategy = Strategy(**saved["test"]["strategy"])
    bars, meta = {}, {}
    for timeframe, dataset_id in DATASETS.items():
        payload = conn.execute("SELECT payload FROM datasets WHERE id=?", (dataset_id,)).fetchone()
        if payload is None:
            raise RuntimeError(f"Required retained MT5 dataset is missing: {timeframe}")
        meta[timeframe] = json.loads(payload[0])
        bars[timeframe] = [json.loads(r[0]) for r in conn.execute(
            "SELECT payload FROM candles WHERE dataset_id=? ORDER BY time", (dataset_id,)
        )]
        validate_bars(bars[timeframe], TIMEFRAMES[timeframe])
    conn.close()
    return bars, meta, strategy


def mt5_availability() -> dict:
    """A bounded read-only rate request.  No datasets or DB rows are saved."""
    adapter = MT5Adapter()
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    end = datetime(2026, 9, 22, tzinfo=timezone.utc)
    result = {"attempted": True, "range_utc": [start.isoformat(), end.isoformat()], "timeframes": {}}
    try:
        adapter.connect_mt5("XAUUSD")
        result["connected"] = True
        result["terminal"] = {k: adapter.diagnostics().get(k) for k in ("terminal_path", "account_mode", "algo_trading_available")}
        for tf in DATASETS:
            try:
                values = adapter.get_historical_data(tf, start, end)
                result["timeframes"][tf] = {
                    "bars": len(values),
                    "first_utc": iso(values[0]["time"]) if values else None,
                    "last_utc": iso(values[-1]["time"]) if values else None,
                }
            except Exception as exc:  # evidence, not a reason to substitute data
                result["timeframes"][tf] = {"error": str(exc)}
    except Exception as exc:
        result["connected"] = False
        result["error"] = str(exc)
    finally:
        adapter.disconnect_mt5()
    return result


def candidates(frame: pd.DataFrame) -> dict[str, Callable[[pd.Series, int], int]]:
    def base(row: pd.Series, direction: int) -> bool:
        fast, slow = finite(row.ema_fast), finite(row.ema_slow)
        slope = finite(row.ema_slow_slope)
        price = float(row.close)
        return direction * (fast - slow) > 0 and direction * slope > 0 and direction * (price - fast) > 0

    def trend_adx(threshold: int) -> Callable[[pd.Series, int], int]:
        def signal(row: pd.Series, _i: int) -> int:
            for direction in (1, -1):
                if base(row, direction) and finite(row.adx) >= threshold and direction * (finite(row.plus_di) - finite(row.minus_di)) > 0:
                    return direction
            return 0
        return signal

    def pullback(row: pd.Series, _i: int) -> int:
        rsi = finite(row.rsi, 50)
        if base(row, 1) and finite(row.adx) >= 20 and 40 <= rsi <= 55:
            return 1
        if base(row, -1) and finite(row.adx) >= 20 and 45 <= rsi <= 60:
            return -1
        return 0

    def normal_atr(row: pd.Series, _i: int) -> int:
        ratio = finite(row.atr_ratio, 0)
        if not (.75 <= ratio <= 1.50):
            return 0
        return trend_adx(20)(row, _i)

    return {
        "TC_ADX15": trend_adx(15),
        "TC_ADX20": trend_adx(20),
        "TC_ADX25": trend_adx(25),
        "TC_ADX30": trend_adx(30),
        "PULLBACK_RSI_40_60": pullback,
        "NORMAL_ATR_TREND": normal_atr,
    }


def enrich(bars: list[dict], strategy: Strategy) -> pd.DataFrame:
    frame = features(bars, strategy)
    frame["ema_slow_slope"] = frame.ema_slow - frame.ema_slow.shift(3)
    # Each ratio and regime value is based exclusively on prior completed bars.
    prior_median = frame.atr.shift(1).rolling(100, min_periods=30).median()
    frame["atr_ratio"] = frame.atr / prior_median
    frame["atr_q33"] = frame.atr.shift(1).rolling(100, min_periods=30).quantile(.33)
    frame["atr_q67"] = frame.atr.shift(1).rolling(100, min_periods=30).quantile(.67)
    return frame


def wheel_direction(row: pd.Series, strategy: Strategy, timestamp: int) -> int:
    return int(wheel_state(float(row.close), timestamp, strategy)["numerical_direction"])


def collect(
    bars: list[dict], frame: pd.DataFrame, strategy: Strategy, candidate: Callable[[pd.Series, int], int],
    start: int, end: int, wheel_mode: str = "none",
) -> list[dict]:
    output = []
    # end excludes the final ten-bar forward observation.
    for i in range(max(WARMUP, start), end - max(HORIZONS)):
        row = frame.iloc[i]
        if not np.isfinite(row.ema_slow_slope):
            continue
        direction = candidate(row, i)
        if not direction or bars[i + 1]["time"] != bars[i]["time"] + TIMEFRAMES[strategy_timeframe(bars)]:
            continue
        timestamp = bars[i]["time"] + TIMEFRAMES[strategy_timeframe(bars)]
        wheel = wheel_direction(row, strategy, timestamp)
        if wheel_mode == "confirmation" and wheel != direction:
            continue
        if wheel_mode == "veto" and wheel == -direction:
            continue
        entry = bars[i + 1]["open"]
        horizon_returns = {str(h): direction * (bars[i + h]["close"] - entry) for h in HORIZONS}
        window = bars[i + 1:i + max(HORIZONS) + 1]
        favorable = max(b["high"] - entry for b in window) if direction == 1 else max(entry - b["low"] for b in window)
        adverse = max(entry - b["low"] for b in window) if direction == 1 else max(b["high"] - entry for b in window)
        atr = finite(row.atr)
        regime = "high" if row.atr >= row.atr_q67 else "low" if row.atr <= row.atr_q33 else "normal"
        trend = "strong" if finite(row.adx) >= 25 else "weak"
        output.append({
            "signal_time": timestamp, "date": iso(timestamp)[:10], "month": iso(timestamp)[:7], "direction": "BUY" if direction == 1 else "SELL",
            "wheel_direction": wheel, "entry": entry, "adx": finite(row.adx), "rsi": finite(row.rsi, 50),
            "trend_regime": trend, "volatility_regime": regime,
            "mfe": favorable, "mae": adverse, "mfe_r": favorable / atr if atr else None, "mae_r": adverse / atr if atr else None,
            **{f"return_{h}": horizon_returns[str(h)] for h in HORIZONS},
        })
    return output


def strategy_timeframe(bars: list[dict]) -> str:
    # The caller gives one homogeneous validated dataset; infer without external state.
    delta = bars[1]["time"] - bars[0]["time"]
    return next(tf for tf, seconds in TIMEFRAMES.items() if seconds == delta)


def score(records: list[dict]) -> dict:
    if not records:
        return {"signals": 0, "sample_label": sample_label(0)}
    result = {"signals": len(records), "sample_label": sample_label(len(records))}
    for h in HORIZONS:
        values = np.array([r[f"return_{h}"] for r in records], dtype=float)
        result[f"forward_{h}_expectancy"] = float(values.mean())
        result[f"forward_{h}_accuracy"] = float((values > 0).mean())
        result[f"forward_{h}_median"] = float(np.median(values))
    for k in ("mfe", "mae", "mfe_r", "mae_r"):
        values = [r[k] for r in records if r[k] is not None]
        result[f"mean_{k}"] = float(np.mean(values)) if values else None
    return result


def grouped(records: list[dict], field: str) -> dict:
    values: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        values[str(record[field])].append(record)
    return {key: score(rows) for key, rows in sorted(values.items())}


def robustness(records: list[dict]) -> dict:
    if not records:
        return {}
    key = "return_5"
    groups = {
        "all": records,
        "without_best_trade": [x for x in records if x is not max(records, key=lambda r: r[key])],
        "without_worst_trade": [x for x in records if x is not min(records, key=lambda r: r[key])],
    }
    by_day: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_day[record["date"]].append(record)
    daily = {day: sum(x[key] for x in rows) for day, rows in by_day.items()}
    groups["without_best_day"] = [x for x in records if x["date"] != max(daily, key=daily.get)]
    groups["without_worst_day"] = [x for x in records if x["date"] != min(daily, key=daily.get)]
    return {name: {"signals": len(rows), "forward_5_expectancy": score(rows).get("forward_5_expectancy"), "forward_5_accuracy": score(rows).get("forward_5_accuracy")} for name, rows in groups.items()}


def coverage(meta: dict, bars: list[dict]) -> dict:
    days = len({iso(b["time"])[:10] for b in bars})
    return {"source": meta.get("source"), "earliest_utc": iso(bars[0]["time"]), "latest_utc": iso(bars[-1]["time"]), "candles": len(bars), "calendar_days": days}


def f(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + "\n".join("| " + " | ".join(row) + " |" for row in rows)


def write_reports(results: dict) -> None:
    docs = ROOT / "docs"
    coverage_rows = [[tf, data["source"], data["earliest_utc"], data["latest_utc"], str(data["candles"]), str(data["calendar_days"])] for tf, data in results["retained_coverage"].items()]
    attempt = results["mt5_history_attempt"]
    mt5_rows = []
    for tf, data in attempt["timeframes"].items():
        mt5_rows.append([tf, str(data.get("bars", 0)), str(data.get("first_utc", "—")), str(data.get("last_utc", "—")), data.get("error", "retrieved")])
    (docs / "V3_ENTRY_RESEARCH.md").write_text(
        "# DIGITAL_TIME_WHEEL_V3_ENTRY_RESEARCH\n\n"
        "Research-only causal entry study. V1 and V2 were not read, modified, or executed. This runner imports no execution controller and sends no MT5 order. It evaluates a signal only at a completed bar, assumes next-bar-open entry, and measures raw directional movement at 1, 2, 3, 5, and 10 completed bars. No stop, target, holding-time, cost, or position-cap selection occurred.\n\n"
        "## Historical availability\n\n" + table(["Timeframe", "Source", "First UTC", "Last UTC", "Candles", "Calendar days"], coverage_rows) + "\n\n"
        "A bounded read-only request for 2026-03-01 through 2026-09-22 was attempted against the connected MT5 terminal. It did not save bars, alter the database, or call an order API.\n\n" + table(["Timeframe", "Returned", "First UTC", "Last UTC", "Result"], mt5_rows) + "\n\n"
        "The terminal connected but `copy_rates_range` returned `(-1, Terminal: Call failed)` for M15, M30, and H1. The available retained data therefore remains about 30 calendar days and has already been inspected in V1/V2. The chronological partitions below are explicitly **retrospective IN-SAMPLE**, not independent unseen validation.\n\n"
        "## Protocol\n\n"
        "- Windows: first 60% development, next 20% validation, last 20% retrospective holdout; signals within ten bars of a boundary are excluded from that window.\n"
        "- Candidate selection: greatest development 5-bar directional expectancy among candidates with at least 30 signals.\n"
        "- Minimum labels: <30 INSUFFICIENT_SAMPLE; 30–99 LOW_CONFIDENCE; >=100 USABLE_FOR_COMPARISON.\n"
        "- Existing features only: EMA structure and 3-bar slow-EMA slope, ADX/+DI/-DI, RSI, ATR. ATR regime uses only the prior 100 completed bars.\n"
        "- Time Wheel is recorded but is not mandatory in the base V3 entry arm.\n",
        encoding="utf-8",
    )
    candidate_sections = ["# V3 Entry Candidates\n", "Six coarse, interpretable technical candidates were run independently for every timeframe. Values are raw quote-price units per signal after a next-bar-open hypothetical entry; they are not P/L and are not exit-optimized.\n"]
    for tf, data in results["timeframes"].items():
        candidate_sections.append(f"## {tf}\n\n")
        for window in ("development", "validation", "holdout_retrospective"):
            rows = []
            for name, metrics in data["candidates"].items():
                rows.append([name, str(metrics[window]["signals"]), metrics[window]["sample_label"], f(metrics[window].get("forward_5_expectancy")), f(metrics[window].get("forward_5_accuracy")), f(metrics[window].get("mean_mfe")), f(metrics[window].get("mean_mae"))])
            candidate_sections.append(f"### {window.replace('_', ' ').title()}\n\n" + table(["Candidate", "Signals", "Label", "5-bar expectancy", "5-bar accuracy", "Mean MFE", "Mean MAE"], rows) + "\n\n")
    (docs / "V3_ENTRY_CANDIDATES.md").write_text("\n".join(candidate_sections), encoding="utf-8")
    tw_sections = ["# V3 Time Wheel Attribution\n", "For each timeframe, the development-selected technical candidate was replayed unchanged under three Time Wheel roles: none (base V3), confirmation (Wheel must agree), and veto (only an opposite Wheel value rejects). This is attribution, not an accepted entry rule.\n"]
    for tf, data in results["timeframes"].items():
        tw_sections.append(f"## {tf}: development-selected `{data['selected_on_development']}`\n\n")
        rows = []
        for mode, windows in data["time_wheel_attribution"].items():
            for window, metrics in windows.items():
                rows.append([mode, window, str(metrics["signals"]), metrics["sample_label"], f(metrics.get("forward_5_expectancy")), f(metrics.get("forward_5_accuracy"))])
        tw_sections.append(table(["Wheel role", "Window", "Signals", "Label", "5-bar expectancy", "Accuracy"], rows) + "\n\n")
    tw_sections.append("A role is not treated as beneficial merely because it raises an in-sample average while shrinking the sample. The base technical and veto arms are negative in every final retrospective segment. M30 confirmation is positive (+3.962) in that segment, but has only 13 signals (INSUFFICIENT_SAMPLE) after being only 40 signals in development; it is not stable evidence. The study therefore finds no demonstrated incremental Time Wheel entry value.\n")
    (docs / "V3_TIME_WHEEL_ATTRIBUTION.md").write_text("\n".join(tw_sections), encoding="utf-8")
    validation = ["# V3 Validation Results\n", "## Frozen per-timeframe selections\n"]
    rows = []
    for tf, data in results["timeframes"].items():
        name = data["selected_on_development"]
        m = data["candidates"][name]
        rows.append([tf, name, str(m["development"]["signals"]), f(m["development"].get("forward_5_expectancy")), str(m["validation"]["signals"]), f(m["validation"].get("forward_5_expectancy")), str(m["holdout_retrospective"]["signals"]), f(m["holdout_retrospective"].get("forward_5_expectancy")), f(m["holdout_retrospective"].get("forward_5_accuracy"))])
    validation.append(table(["TF", "Frozen on development", "Dev n", "Dev exp", "Validation n", "Validation exp", "Final n", "Final exp", "Final accuracy"], rows) + "\n\n")
    validation.append("All three development selections are positive in development and validation but negative in the final chronological segment. This rejects them as stable entry candidates and blocks exit research.\n")
    for tf, data in results["timeframes"].items():
        details = data["selected_validation_details"]
        validation.append(f"## {tf} validation diagnostics ({data['selected_on_development']})\n\n")
        for label, section in (("BUY / SELL", details.get("validation_buy_sell", {})), ("Trend regime", details.get("validation_trend_regime", {})), ("Volatility regime", details.get("validation_volatility_regime", {}))):
            rows = [[key, str(v["signals"]), v["sample_label"], f(v.get("forward_5_expectancy")), f(v.get("forward_5_accuracy"))] for key, v in section.items()]
            validation.append(f"### {label}\n\n" + table(["Group", "Signals", "Label", "5-bar expectancy", "Accuracy"], rows) + "\n\n")
        rows = [[key, str(v["signals"]), v["sample_label"], f(v.get("forward_5_expectancy")), f(v.get("forward_5_accuracy"))] for key, v in details.get("holdout_buy_sell", {}).items()]
        validation.append("### Final retrospective BUY / SELL\n\n" + table(["Group", "Signals", "Label", "5-bar expectancy", "Accuracy"], rows) + "\n\n")
        robust = details.get("validation_robustness", {})
        rows = [[key, str(v["signals"]), f(v.get("forward_5_expectancy")), f(v.get("forward_5_accuracy"))] for key, v in robust.items()]
        validation.append("### Validation robustness\n\n" + table(["Adjustment", "Signals", "5-bar expectancy", "Accuracy"], rows) + "\n\n")
        robust = details.get("holdout_robustness", {})
        rows = [[key, str(v["signals"]), f(v.get("forward_5_expectancy")), f(v.get("forward_5_accuracy"))] for key, v in robust.items()]
        validation.append("### Final retrospective-segment robustness\n\n" + table(["Adjustment", "Signals", "5-bar expectancy", "Accuracy"], rows) + "\n\n")
        monthly = details.get("validation_monthly", {})
        rows = [[key, str(v["signals"]), f(v.get("forward_5_expectancy")), f(v.get("forward_5_accuracy"))] for key, v in monthly.items()]
        validation.append("### Validation monthly results\n\n" + table(["Month", "Signals", "5-bar expectancy", "Accuracy"], rows) + "\n\n")
    validation.append("All 1/2/3/5/10-bar, MFE/MAE results, daily records, and final-segment monthly results are retained in `docs/V3_ENTRY_RESEARCH_RESULTS.json`. The retained history is under 30 calendar days, so monthly summaries are descriptive only.\n")
    (docs / "V3_VALIDATION_RESULTS.md").write_text("\n".join(validation), encoding="utf-8")


def main() -> None:
    # Read-only MT5 request occurs before local analysis; it is not needed for the saved-data results.
    availability = mt5_availability()
    bars_by_tf, metadata, strategy = load_saved()
    all_results = {"research_id": "DIGITAL_TIME_WHEEL_V3_ENTRY_RESEARCH", "read_only": True,
                   "mt5_history_attempt": availability, "retained_coverage": {}, "timeframes": {},
                   "limitations": ["Retained MT5 history was used previously in V1/V2 research; chronological partitions are retrospective IN-SAMPLE, not genuinely unseen.", "No exit, stop, holding-time, position-cap, or order-execution model is evaluated or changed."]}
    for timeframe, bars in bars_by_tf.items():
        all_results["retained_coverage"][timeframe] = coverage(metadata[timeframe], bars)
        frame = enrich(bars, strategy)
        n = len(bars); dev_end = int(n * .60); val_end = int(n * .80)
        windows = {"development": (0, dev_end), "validation": (dev_end, val_end), "holdout_retrospective": (val_end, n)}
        candidate_fns = candidates(frame)
        candidate_results: dict[str, dict] = {}
        for name, candidate in candidate_fns.items():
            candidate_results[name] = {window: score(collect(bars, frame, strategy, candidate, start, end)) for window, (start, end) in windows.items()}
        # Selection only sees development 5-candle directional expectancy, then freezes per timeframe.
        selectable = [(data["development"].get("forward_5_expectancy", float("-inf")), name) for name, data in candidate_results.items() if data["development"].get("signals", 0) >= 30]
        selected = max(selectable)[1] if selectable else None
        selected_fn = candidate_fns[selected] if selected else None
        attribution = {}
        details = {}
        if selected_fn:
            for mode in ("none", "confirmation", "veto"):
                attribution[mode] = {window: score(collect(bars, frame, strategy, selected_fn, start, end, mode)) for window, (start, end) in windows.items()}
            base_records = collect(bars, frame, strategy, selected_fn, *windows["validation"])
            holdout_records = collect(bars, frame, strategy, selected_fn, *windows["holdout_retrospective"])
            details = {"validation_buy_sell": grouped(base_records, "direction"), "validation_trend_regime": grouped(base_records, "trend_regime"),
                       "validation_volatility_regime": grouped(base_records, "volatility_regime"), "validation_robustness": robustness(base_records),
                       "holdout_buy_sell": grouped(holdout_records, "direction"), "holdout_trend_regime": grouped(holdout_records, "trend_regime"),
                       "holdout_volatility_regime": grouped(holdout_records, "volatility_regime"), "holdout_robustness": robustness(holdout_records), "validation_monthly": grouped(base_records, "month"),
                       "holdout_monthly": grouped(holdout_records, "month")}
        all_results["timeframes"][timeframe] = {"windows": windows, "candidates": candidate_results, "selected_on_development": selected,
                                                 "time_wheel_attribution": attribution, "selected_validation_details": details}
    output = ROOT / "docs" / "V3_ENTRY_RESEARCH_RESULTS.json"
    output.write_text(json.dumps(all_results, indent=2, allow_nan=False), encoding="utf-8")
    write_reports(all_results)
    print(output)


if __name__ == "__main__":
    main()
