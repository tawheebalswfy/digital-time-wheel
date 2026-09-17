"""Reproducible, read-only forensic parser for an MT5 HTML history report."""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


DATE_FMT = "%Y.%m.%d %H:%M:%S"


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._in_td = False
        self._cell = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag == "td":
            self._in_td = True
            self._cell = ""

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._cell += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "td":
            if self._row is not None:
                self._row.append(" ".join(self._cell.split()))
            self._in_td = False
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def parse_report(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-16")
    raw_positions = raw.split("<b>Positions</b>", 1)[1].split("<b>Orders</b>", 1)[0]
    parser = _Parser()
    parser.feed(raw_positions)
    start = next(i for i, row in enumerate(parser.rows) if row and row[0] == "Time")
    end = len(parser.rows)
    trades: list[dict] = []
    for row in parser.rows[start + 1 : end]:
        if len(row) != 14 or not re.fullmatch(r"\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}", row[0]):
            continue
        if row[3].lower() not in {"buy", "sell"}:
            continue
        to_float = lambda value: float(value.replace(",", ""))
        opened = datetime.strptime(row[0], DATE_FMT)
        closed = datetime.strptime(row[9], DATE_FMT)
        trade = {
            "open_time": row[0],
            "close_time": row[9],
            "symbol": row[2],
            "direction": row[3].lower(),
            "position": row[1],
            "volume": to_float(row[5]),
            "entry": to_float(row[6]),
            "sl": to_float(row[7]),
            "tp": to_float(row[8]),
            "exit": to_float(row[10]),
            "commission": to_float(row[11]),
            "swap": to_float(row[12]),
            "gross_pl": to_float(row[13]),
        }
        trade["net_pl"] = trade["gross_pl"] + trade["commission"] + trade["swap"]
        trade["duration_seconds"] = (closed - opened).total_seconds()
        if trade["direction"] == "buy":
            risk = trade["entry"] - trade["sl"]
            reward = trade["tp"] - trade["entry"]
        else:
            risk = trade["sl"] - trade["entry"]
            reward = trade["entry"] - trade["tp"]
        trade["planned_risk_distance"] = risk
        trade["planned_reward_distance"] = reward
        trade["planned_rr"] = reward / risk if risk > 0 else None
        trade["realized_r_multiple"] = ((trade["exit"] - trade["entry"]) / risk if trade["direction"] == "buy" else (trade["entry"] - trade["exit"]) / risk) if risk > 0 else None
        trades.append(trade)
    return trades


def stats(trades: list[dict]) -> dict:
    values = [t["net_pl"] for t in trades]
    wins = [v for v in values if v > 0]
    losses = [v for v in values if v < 0]
    gross_profit = sum(wins)
    gross_loss = sum(losses)
    return {
        "trades": len(values),
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(values) - len(wins) - len(losses),
        "win_rate": len(wins) / len(values) if values else None,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_pl": sum(values),
        "profit_factor": gross_profit / abs(gross_loss) if gross_loss else None,
        "average_win": sum(wins) / len(wins) if wins else None,
        "average_loss": sum(losses) / len(losses) if losses else None,
        "expectancy": sum(values) / len(values) if values else None,
        "max_loss": min(values) if values else None,
        "max_win": max(values) if values else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("report", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    trades = parse_report(args.report)
    result = {"source": str(args.report), "trades": trades, "summary": stats(trades)}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
