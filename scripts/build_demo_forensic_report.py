"""Build the requested read-only demo-week forensic report from parsed MT5 trades."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from analyze_demo_report import parse_report, stats


def q(value):
    return "—" if value is None else f"{value:.2f}"


def pf(trades):
    s = stats(trades)
    return s["profit_factor"]


def max_drawdown(trades):
    balance = peak = 0.0
    drawdown = 0.0
    for t in sorted(trades, key=lambda x: x["close_time"]):
        balance += t["net_pl"]
        peak = max(peak, balance)
        drawdown = max(drawdown, peak - balance)
    return drawdown


def streaks(trades):
    best_wins = best_losses = 0
    wins = losses = 0
    for t in sorted(trades, key=lambda x: x["close_time"]):
        if t["net_pl"] > 0:
            wins += 1; losses = 0
        elif t["net_pl"] < 0:
            losses += 1; wins = 0
        else:
            wins = losses = 0
        best_wins = max(best_wins, wins); best_losses = max(best_losses, losses)
    return best_wins, best_losses


def fmt_stats(items):
    s = stats(items)
    return f"{s['trades']} | {s['win_rate']*100:.1f}% | {q(s['net_pl'])} | {q(s['profit_factor'])} | {q(s['expectancy'])} | {q(s['average_win'])} | {q(s['average_loss'])} | {q(s['max_loss'])} | {q(s['max_win'])}"


def clusters(trades, seconds):
    result = []
    ordered = sorted(trades, key=lambda t: (t["symbol"], t["direction"], t["open_time"]))
    current = []
    key = None
    last = None
    for t in ordered:
        dt = datetime.strptime(t["open_time"], "%Y.%m.%d %H:%M:%S")
        k = (t["symbol"], t["direction"])
        if key != k or last is None or (dt - last).total_seconds() > seconds:
            if len(current) > 1:
                result.append(current)
            current = [t]
        else:
            current.append(t)
        key, last = k, dt
    if len(current) > 1:
        result.append(current)
    return result


def main():
    report = Path("ReportHistory-52960017.html")
    trades = parse_report(report)
    out = Path("runtime/demo_report_forensic.json")
    machine = {"source": str(report), "summary": stats(trades), "trades": trades, "symbol": {}, "hour": {}, "duration": {}, "clusters": {}}
    for sym in sorted({t["symbol"] for t in trades}):
        machine["symbol"][sym] = stats([t for t in trades if t["symbol"] == sym])
    for hour in range(24):
        machine["hour"][str(hour)] = stats([t for t in trades if datetime.strptime(t["open_time"], "%Y.%m.%d %H:%M:%S").hour == hour])
    buckets = [("<1m", 0, 60), ("1-5m", 60, 300), ("5-15m", 300, 900), ("15-60m", 900, 3600), (">60m", 3600, float("inf"))]
    for name, lo, hi in buckets:
        machine["duration"][name] = stats([t for t in trades if lo <= t["duration_seconds"] < hi])
    for window in (5, 30, 60):
        cs = clusters(trades, window)
        machine["clusters"][str(window)] = [{"count": len(c), "symbol": c[0]["symbol"], "direction": c[0]["direction"], "open_times": [t["open_time"] for t in c], "net_pl": sum(t["net_pl"] for t in c), "positions": [t["position"] for t in c]} for c in cs]
    rr = [t["planned_rr"] for t in trades if t["planned_rr"] is not None]
    machine["planned_rr"] = {"count": len(rr), "min": min(rr), "max": max(rr), "mean": sum(rr)/len(rr), "median": sorted(rr)[len(rr)//2]}
    out.write_text(json.dumps(machine, indent=2), encoding="utf-8")
    lines = [
        "# Demo Week Forensic Report",
        "",
        "Source: `ReportHistory-52960017.html` (196 closed Positions rows). This is retrospective analysis of one demo report, not forward validation.",
        "",
        "## Verified baseline",
        "",
        "| Trades | Winners | Losers | Win rate | Gross profit | Gross loss | Net profit (report profit) | Commission | Swap | Net after costs | PF | Avg win | Avg loss | Expectancy | Max loss | Max win | Max DD |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    sraw = stats(trades)
    best_wins, best_losses = streaks(trades)
    gross_profit = sum(t["gross_pl"] for t in trades if t["gross_pl"] > 0)
    gross_loss = sum(t["gross_pl"] for t in trades if t["gross_pl"] < 0)
    commission = sum(t["commission"] for t in trades)
    swap = sum(t["swap"] for t in trades)
    lines.append(f"| {len(trades)} | {sraw['wins']} | {sraw['losses']} | {sraw['win_rate']*100:.2f}% | {gross_profit:.2f} | {gross_loss:.2f} | {gross_profit+gross_loss:.2f} | {commission:.2f} | {swap:.2f} | {sraw['net_pl']:.2f} | {sraw['profit_factor']:.3f} | {sraw['average_win']:.2f} | {sraw['average_loss']:.2f} | {sraw['expectancy']:.2f} | {sraw['max_loss']:.2f} | {sraw['max_win']:.2f} | {max_drawdown(trades):.2f} |")
    lines.append(f"\nMaximum consecutive wins by realized net result: {best_wins}; maximum consecutive losses: {best_losses}.")
    lines += ["", "The MT5 summary reports 196 trades, 159 winning trades, 37 losing trades, gross profit 348.28, gross loss -371.91, net -23.63 and PF 0.94. Recalculation from all 196 position rows yields 158 positive rows and 38 negative rows when `Profit + Commission + Swap` is classified as realized net. The one-row difference is a report accounting/classification discrepancy and is retained rather than silently corrected.", ""]

    lines += ["## Symbol breakdown", "", "| Symbol | Trades | Win rate | Net P/L | PF | Expectancy | Avg win | Avg loss | Largest loss | Largest win |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for sym in sorted({t["symbol"] for t in trades}):
        ts = [t for t in trades if t["symbol"] == sym]; s = stats(ts)
        lines.append(f"| {sym} | {s['trades']} | {s['win_rate']*100:.1f}% | {s['net_pl']:.2f} | {q(s['profit_factor'])} | {q(s['expectancy'])} | {q(s['average_win'])} | {q(s['average_loss'])} | {q(s['max_loss'])} | {q(s['max_win'])} |")

    lines += ["", "## BUY / SELL attribution", "", "| Symbol | Direction | Trades | Win rate | Net P/L | PF | Expectancy | Avg loss | Max loss |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for sym in sorted({t["symbol"] for t in trades}):
        for side in ("buy", "sell"):
            ts = [t for t in trades if t["symbol"] == sym and t["direction"] == side]; s = stats(ts)
            win_rate = "—" if s["win_rate"] is None else f"{s['win_rate']*100:.1f}%"
            lines.append(f"| {sym} | {side.upper()} | {s['trades']} | {win_rate} | {s['net_pl']:.2f} | {q(s['profit_factor'])} | {q(s['expectancy'])} | {q(s['average_loss'])} | {q(s['max_loss'])} |")

    lines += ["", "## Largest losses", "", "| Position | Open | Symbol | Side | Entry | SL | TP | Exit | Net P/L | Planned R:R | Duration |", "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for t in sorted(trades, key=lambda x: x["net_pl"])[:10]:
        lines.append(f"| {t['position']} | {t['open_time']} | {t['symbol']} | {t['direction'].upper()} | {t['entry']:.2f} | {t['sl']:.2f} | {t['tp']:.2f} | {t['exit']:.2f} | {t['net_pl']:.2f} | {q(t['planned_rr'])} | {t['duration_seconds']/60:.1f}m |")

    lines += ["", "## Largest wins", "", "| Position | Symbol | Side | Net P/L | Planned R:R |", "|---:|---|---|---:|---:|"]
    for t in sorted(trades, key=lambda x: x["net_pl"], reverse=True)[:10]:
        lines.append(f"| {t['position']} | {t['symbol']} | {t['direction'].upper()} | {t['net_pl']:.2f} | {q(t['planned_rr'])} |")

    lines += ["", "## Loss concentration", "", "| Worst losses included | Combined net P/L | Share of total negative net P/L |", "|---:|---:|---:|"]
    total_loss = abs(sum(t["net_pl"] for t in trades if t["net_pl"] < 0))
    for n in (1, 3, 5, 10):
        value = sum(t["net_pl"] for t in sorted(trades, key=lambda x: x["net_pl"])[:n])
        lines.append(f"| {n} | {value:.2f} | {abs(value)/total_loss*100:.1f}% |")

    lines += ["", "## Entry clusters", "", "Timeframe cannot be positively reconstructed from this HTML report; its comments identify DTW demo signals but do not carry timeframe or signal IDs. Clusters below are same-symbol, same-direction open timestamps within the stated window.", "", "| Window | Clusters | Largest entries | Largest combined net loss |", "|---|---:|---:|---:|"]
    for window in (5, 30, 60):
        cs = clusters(trades, window)
        largest = max((len(c) for c in cs), default=0)
        worst = min((sum(t["net_pl"] for t in c) for c in cs), default=0)
        lines.append(f"| {window}s | {len(cs)} | {largest} | {worst:.2f} |")

    lines += ["", "## Risk/reward and costs", "", f"- Planned R:R is available for all {len(trades)} rows with positive SL distance; median and mean are reported in the machine-readable artifact.", f"- Total commission: {commission:.2f}; total swap: {swap:.2f}; costs: {commission+swap:.2f}.", f"- Before costs (raw Profit column): {gross_profit+gross_loss:.2f}; after costs: {sraw['net_pl']:.2f}.", "- The strategy is already negative before costs; costs are not the primary cause of the loss.", "- The dominant structural signature is a high hit rate paired with materially larger average losses than wins.", ""]

    lines += ["## Holding time and time of day", "", "| Duration | Trades | Win rate | Net P/L | PF | Expectancy |", "|---|---:|---:|---:|---:|---:|"]
    buckets = [("<1 minute",0,60),("1–5 minutes",60,300),("5–15 minutes",300,900),("15–60 minutes",900,3600),(">60 minutes",3600,float('inf'))]
    for name, lo, hi in buckets:
        s=stats([t for t in trades if lo <= t['duration_seconds'] < hi]); lines.append(f"| {name} | {s['trades']} | {s['win_rate']*100:.1f}% | {s['net_pl']:.2f} | {q(s['profit_factor'])} | {q(s['expectancy'])} |")
    lines += ["", "The negative tail is concentrated in trades held 5 minutes or longer, especially over 60 minutes. Hour 04 has the most negative net result (-108.21), followed by hour 13 (-38.62); these are descriptive observations from a small sample, not causal session filters.", ""]

    lines += ["## Strategy-side traceback", "", "The SQLite execution history positively links 19 report tickets to persisted symbol, timeframe, signal ID, strategy version, direction, SL and TP fields. The remaining report rows are UNMATCHED in the local database. The HTML report does not contain Time Wheel state, technical-confirmation state, or signal reasoning, so those fields are not inferred.", ""]

    lines += ["## Attribution limits and proposed controls", "", "The report positively supports a risk/exposure problem, especially where same-direction entries cluster. It does not prove timeframe, signal age, Time Wheel state, technical confirmation, or causality. No strategy formula change is justified by this report alone.", "", "| Rank | Candidate | Evidence | Action |", "|---:|---|---|---|", "| 1 | Same-symbol/same-direction cluster cap or cooldown | Directly observable clustered opens and asymmetric loss magnitude | Implement only as an execution risk control after replay |", "| 2 | Planned R:R floor | SL/TP are present and loss asymmetry is measurable | Dry-run/replay first; do not alter signal generation |", "| 3 | Daily loss stop / loss-streak pause | Plausible containment, but this report alone cannot set an unbiased threshold | Forward-test as configurable safety control |", "| 4 | Direction filter | Must be evaluated by symbol and direction sample size | Do not implement from this report alone |", "", "## Conclusion", "", "The week is negative before costs, with losses concentrated in a small number of large adverse outcomes relative to small winners. The evidence supports exposure/risk containment as the first research direction, not a change to Time Wheel or technical signal formulas. Any replay comparison on this same week is retrospective and in-sample; it is not evidence of a future edge."]
    Path("docs/DEMO_WEEK_FORENSIC_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
