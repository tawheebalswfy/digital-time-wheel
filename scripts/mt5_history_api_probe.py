"""Read-only MT5 history API probe; intentionally contains no trading calls."""
import json
from datetime import datetime, timezone

import MetaTrader5 as mt5


SYMBOL = "XAUUSD"
TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1")
COUNTS = (1, 100, 1000)


def stamp(value):
    return datetime.fromtimestamp(int(value), timezone.utc).isoformat()


def main():
    output = {"symbol": SYMBOL, "initialized": False, "calls": []}
    initialized = mt5.initialize(timeout=10_000)
    output["initialized"] = bool(initialized)
    try:
        terminal = mt5.terminal_info() if initialized else None
        output["terminal_connected"] = bool(getattr(terminal, "connected", False))
        output["server"] = str(getattr(terminal, "server", None))
        output["symbol_select_returned"] = bool(initialized and mt5.symbol_select(SYMBOL, True))
        symbol = mt5.symbol_info(SYMBOL) if initialized else None
        output["symbol_selected_status"] = bool(getattr(symbol, "visible", False))
        for timeframe in TIMEFRAMES:
            constant = getattr(mt5, "TIMEFRAME_" + timeframe)
            for requested_bars in COUNTS:
                rates = mt5.copy_rates_from_pos(SYMBOL, constant, 0, requested_bars) if initialized else None
                returned_bars = 0 if rates is None else len(rates)
                now_terminal = mt5.terminal_info() if initialized else None
                now_symbol = mt5.symbol_info(SYMBOL) if initialized else None
                output["calls"].append({
                    "timeframe": timeframe,
                    "requested_bars": requested_bars,
                    "returned_bars": returned_bars,
                    "first_returned_timestamp": stamp(rates[0]["time"]) if returned_bars else None,
                    "last_returned_timestamp": stamp(rates[-1]["time"]) if returned_bars else None,
                    "mt5_last_error": list(mt5.last_error()),
                    "terminal_connected": bool(getattr(now_terminal, "connected", False)),
                    "symbol_selected_status": bool(getattr(now_symbol, "visible", False)),
                })
        print(json.dumps(output, indent=2))
    finally:
        if initialized:
            mt5.shutdown()


if __name__ == "__main__":
    main()
