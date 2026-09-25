"""V9 XAUUSD prospective shadow collector.  Read-only MT5 market-data API only."""
from __future__ import annotations
import argparse, csv, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
START = datetime(2026, 9, 25, tzinfo=timezone.utc)
SYMBOL = "XAUUSD"
CANDIDATES = {
    "H1_STRONG_TREND_TREND_CONTINUATION": ("H1", "TREND_CONTINUATION", 1.25),
    "D1_STRONG_TREND_PULLBACK_CONTINUATION": ("D1", "PULLBACK_CONTINUATION", 1.50),
}
SIGNAL_FIELDS = ["signal_id", "candidate", "timeframe", "signal_timestamp_utc", "entry_timestamp_utc", "direction", "regime", "entry_price", "stop_price", "target_price", "risk", "atr", "adx", "ema_fast", "ema_slow", "rsi", "plus_di", "minus_di", "time_wheel_direction", "time_wheel_confluence", "created_utc"]
RESULT_FIELDS = ["signal_id", "candidate", "timeframe", "direction", "entry_timestamp_utc", "exit_timestamp_utc", "outcome", "entry_price", "exit_price", "stop_price", "target_price", "holding_bars", "holding_minutes", "realized_r", "realized_quote_pnl", "mfe", "mae", "closed_utc"]

def iso(ts): return datetime.fromtimestamp(int(ts), timezone.utc).isoformat()
def now(): return datetime.now(timezone.utc).isoformat()
def utc_ts(text): return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
def val(x, default=0.0):
    try:
        y = float(x)
        return y if y == y else default
    except (TypeError, ValueError): return default

def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def read_csv(path):
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))

def protocol():
    return """# V9 Forward Shadow Protocol

Prospective start is **2026-09-25T00:00:00+00:00**. This program observes only XAUUSD H1 and D1 bars through MT5 `initialize`, `terminal_info`, `symbol_select`, and `copy_rates_from_pos`; it contains no trade-placement API and creates no positions.

Only the most recently closed candle is eligible to create a signal on a collector run. Earlier bars are used solely as indicator warm-up and are excluded from V9 performance. Signals are append-only and deduplicated by candidate plus entry timestamp. Outcomes are reconciled only after each subsequent candle has closed.

Frozen rules: EMA 12/26, ADX/ATR/RSI 14; ADX >= 25; absolute three-bar slow-EMA slope >= 0.15 ATR; one non-overlapping virtual position per candidate; maximum 30 bars. H1 uses trend continuation with a structural stop and 1.25R target. D1 uses pullback continuation with a structural stop and 1.5R target. These are V9 preregistered shadow exits, not V8-validated exits. Time Wheel attributes state only and never permits or vetoes a signal.
"""

def status(signals, results):
    completed = {x["signal_id"] for x in results}
    lines = ["# V9 Forward Shadow Status\n", f"- Prospective start: `{START.isoformat()}`\n", f"- Logged prospective signals: **{len(signals)}**\n", f"- Completed shadow outcomes: **{len(results)}**\n", f"- Open virtual positions: **{sum(x['signal_id'] not in completed for x in signals)}**\n", "- Status: **IN_PROGRESS** (minimums: H1 100 completed trades; D1 50 completed trades).\n"]
    for candidate in CANDIDATES:
        s = [x for x in signals if x["candidate"] == candidate]; r = [x for x in results if x["candidate"] == candidate]
        lines.append(f"## {candidate}\n\nSignals: {len(s)}; completed: {len(r)}. {summary(r)} No profitability conclusion is permitted before the preregistered sample minimum and meaningful calendar coverage.\n")
    return "\n".join(lines)

def summary(rows):
    if not rows: return "No completed outcome metrics yet."
    p = [val(x["realized_quote_pnl"]) for x in rows]; w = [x for x in p if x > 0]; l = [x for x in p if x < 0]
    pf = sum(w) / -sum(l) if l else None
    win = len(w) / len(p)
    return f"Completed metrics: win rate={win:.3f}; PF={'N/A' if pf is None else f'{pf:.3f}'}; expectancy={sum(p)/len(p):.3f}; net P/L={sum(p):.3f}."

def ensure_files():
    data = ROOT / "data"; docs = ROOT / "docs"; data.mkdir(exist_ok=True); docs.mkdir(exist_ok=True)
    sp, rp = data / "v9_forward_signals.csv", data / "v9_forward_results.csv"
    if not sp.exists(): write_csv(sp, SIGNAL_FIELDS, [])
    if not rp.exists(): write_csv(rp, RESULT_FIELDS, [])
    (docs / "V9_FORWARD_PROTOCOL.md").write_text(protocol(), encoding="utf-8")
    (docs / "V9_FORWARD_STATUS.md").write_text(status(read_csv(sp), read_csv(rp)), encoding="utf-8")
    return sp, rp

def structural_stop(row, direction, entry):
    atr = val(row["atr"]); structural = val(row["support"] if direction == "BUY" else row["resistance"])
    fallback = entry - 1.5 * atr if direction == "BUY" else entry + 1.5 * atr
    if structural <= 0 or (entry - structural if direction == "BUY" else structural - entry) <= 0: structural = fallback
    return structural

def signal_from_bar(bars, enriched, index, candidate, concept, target_r):
    from backend.app.technical import finite
    from backend.app.wheel import state as wheel_state
    from backend.app.config import Strategy
    row, bar = enriched[index], bars[index]
    atr, adx, slope = finite(row["atr"]), finite(row["adx"]), abs(finite(row["slope"]))
    if not (adx >= 25 and slope >= .15 * atr): return None
    fast, slow, plus, minus, close = (finite(row[k]) for k in ("ema_fast", "ema_slow", "plus_di", "minus_di", "close"))
    trend = "BUY" if fast > slow and finite(row["slope"]) > 0 and plus > minus else "SELL" if fast < slow and finite(row["slope"]) < 0 and minus > plus else None
    if not trend: return None
    rsi = finite(row["rsi"], 50)
    if concept == "TREND_CONTINUATION": ok = close > fast if trend == "BUY" else close < fast
    else: ok = (40 <= rsi <= 55 and close <= fast + .3 * atr) if trend == "BUY" else (45 <= rsi <= 60 and close >= fast - .3 * atr)
    if not ok: return None
    entry_bar = bars[index + 1]; entry = val(entry_bar["open"]); stop = structural_stop(row, trend, entry); risk = abs(entry - stop)
    if risk <= 0: return None
    direction = 1 if trend == "BUY" else -1
    wheel = wheel_state(close, int(bar["time"]), Strategy())
    entry_time = int(entry_bar["time"]); sig_time = int(bar["time"])
    return {"signal_id": f"V9-{candidate}-{entry_time}", "candidate": candidate, "timeframe": CANDIDATES[candidate][0], "signal_timestamp_utc": iso(entry_time), "entry_timestamp_utc": iso(entry_time), "direction": trend, "regime": "STRONG_TREND", "entry_price": entry, "stop_price": stop, "target_price": entry + direction * target_r * risk, "risk": risk, "atr": atr, "adx": adx, "ema_fast": fast, "ema_slow": slow, "rsi": rsi, "plus_di": plus, "minus_di": minus, "time_wheel_direction": wheel["numerical_direction"], "time_wheel_confluence": wheel["confluence"], "created_utc": now()}

def reconcile(signal, bars, last_closed_time):
    entry_time = utc_ts(signal["entry_timestamp_utc"])
    completed = [b for b in bars if entry_time <= int(b["time"]) <= last_closed_time]
    if not completed: return None
    direction = 1 if signal["direction"] == "BUY" else -1
    entry, stop, target, risk = (val(signal[k]) for k in ("entry_price", "stop_price", "target_price", "risk"))
    highs, lows = [val(x["high"]) for x in completed], [val(x["low"]) for x in completed]
    mfe = max((h-entry) if direction == 1 else (entry-l) for h,l in zip(highs,lows)); mae = max((entry-l) if direction == 1 else (h-entry) for h,l in zip(highs,lows))
    outcome = exit_price = None; exit_bar = None
    for b in completed:
        hit_stop = val(b["low"]) <= stop if direction == 1 else val(b["high"]) >= stop
        hit_target = val(b["high"]) >= target if direction == 1 else val(b["low"]) <= target
        if hit_stop:
            outcome = "stop"; exit_price = min(stop, val(b["open"])) if direction == 1 else max(stop, val(b["open"])); exit_bar = b; break
        if hit_target: outcome = "target"; exit_price = target; exit_bar = b; break
    if outcome is None and len(completed) < 30: return None
    if outcome is None: outcome = "timeout"; exit_bar = completed[29]; exit_price = val(exit_bar["close"])
    pnl = direction * (exit_price-entry); hold_min = (int(exit_bar["time"])-entry_time)/60
    return {"signal_id": signal["signal_id"], "candidate": signal["candidate"], "timeframe": signal["timeframe"], "direction": signal["direction"], "entry_timestamp_utc": signal["entry_timestamp_utc"], "exit_timestamp_utc": iso(exit_bar["time"]), "outcome": outcome, "entry_price": entry, "exit_price": exit_price, "stop_price": stop, "target_price": target, "holding_bars": completed.index(exit_bar)+1, "holding_minutes": hold_min, "realized_r": pnl/risk, "realized_quote_pnl": pnl, "mfe": mfe, "mae": mae, "closed_utc": now()}

def fetch(tf):
    import MetaTrader5 as mt5
    rate_tf = getattr(mt5, f"TIMEFRAME_{tf}")
    raw = mt5.copy_rates_from_pos(SYMBOL, rate_tf, 0, 1000)
    if raw is None: raise RuntimeError(f"copy_rates_from_pos {tf}: {mt5.last_error()}")
    return [{k: (v.item() if hasattr(v, "item") else v) for k,v in zip(raw.dtype.names, row)} for row in raw]

def collect():
    import MetaTrader5 as mt5
    from backend.app.config import Strategy
    from backend.app.technical import features
    sp, rp = ensure_files(); signals, results = read_csv(sp), read_csv(rp); known = {x["signal_id"] for x in signals}; closed = {x["signal_id"] for x in results}
    if not mt5.initialize(timeout=10000): raise RuntimeError(f"MT5 initialize: {mt5.last_error()}")
    try:
        info = mt5.terminal_info()
        if not info or not info.connected: raise RuntimeError("MT5 terminal is not connected")
        if not mt5.symbol_select(SYMBOL, True): raise RuntimeError(f"XAUUSD selection: {mt5.last_error()}")
        for candidate, (tf, concept, target_r) in CANDIDATES.items():
            bars = fetch(tf)
            if len(bars) < 160: raise RuntimeError(f"Insufficient {tf} bars for indicator warm-up")
            # Last element is potentially forming; only the immediately prior bar can signal.
            closed_index = len(bars)-2; last_closed_time = int(bars[closed_index]["time"])
            enriched = features(bars, Strategy()); enriched["slope"] = enriched.ema_slow-enriched.ema_slow.shift(3)
            enriched = enriched.to_dict("records")
            active = any(x["candidate"] == candidate and x["signal_id"] not in closed for x in signals)
            sig_close = int(bars[closed_index]["time"]) + (3600 if tf == "H1" else 86400)
            if sig_close >= START.timestamp() and not active:
                signal = signal_from_bar(bars, enriched, closed_index, candidate, concept, target_r)
                if signal and signal["signal_id"] not in known:
                    signals.append(signal); known.add(signal["signal_id"])
            for signal in [x for x in signals if x["candidate"] == candidate and x["signal_id"] not in closed]:
                result = reconcile(signal, bars, last_closed_time)
                if result: results.append(result); closed.add(result["signal_id"])
    finally:
        mt5.shutdown()
    write_csv(sp, SIGNAL_FIELDS, signals); write_csv(rp, RESULT_FIELDS, results)
    (ROOT / "docs" / "V9_FORWARD_STATUS.md").write_text(status(signals, results), encoding="utf-8")
    print({"signals": len(signals), "results": len(results), "status": "IN_PROGRESS"})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--initialize-only", action="store_true"); args = parser.parse_args()
    if args.initialize_only: ensure_files(); print({"status": "IN_PROGRESS", "initialized": True})
    else: collect()
