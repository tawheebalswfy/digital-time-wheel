"""Offline DIGITAL_TIME_WHEEL_V4_LONG_HISTORY_RESEARCH; no MT5 or order APIs."""
from __future__ import annotations

import csv, json, math, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.config import Strategy, TIMEFRAMES
from backend.app.technical import features, finite
from backend.app.wheel import state as wheel_state
from backend.app.signals import targets as v1_targets

FILES = {tf: ROOT / "data" / "history" / f"XAUUSD_{tf}.csv" for tf in ("M15", "M30", "H1")}
HORIZONS = (1, 2, 3, 5, 10)
WARMUP = 150
COST = 0.40  # V1 research convention: spread .30 + two .05 slippages.


def ts(x): return datetime.fromtimestamp(int(x), timezone.utc).isoformat()
def fmt(x): return "—" if x is None else f"{x:.3f}"
def table(headers, rows): return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def load(path):
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["time"] = int(row["time"])
        for k in ("open", "high", "low", "close", "tick_volume", "spread", "real_volume"): row[k] = float(row[k])
    return rows


def windows(bars):
    n = len(bars); a = int(n * .60); b = int(n * .80)
    return {"development": (0, a), "validation": (a, b), "holdout": (b, n)}


def enrich(bars, cfg):
    f = features(bars, cfg)
    f["slow_slope"] = f.ema_slow - f.ema_slow.shift(3)
    prior = f.atr.shift(1).rolling(100, min_periods=30).median()
    f["atr_ratio"] = f.atr / prior
    return f


def direction(row, name):
    get = row.get if isinstance(row, dict) else lambda k: getattr(row, k)
    fast, slow, slope, close = finite(get("ema_fast")), finite(get("ema_slow")), finite(get("slow_slope")), float(get("close"))
    def trend(d): return d * (fast-slow) > 0 and d * slope > 0 and d * (close-fast) > 0 and d * (finite(get("plus_di"))-finite(get("minus_di"))) > 0
    for d in (1, -1):
        if not trend(d): continue
        adx, rsi, ar = finite(get("adx")), finite(get("rsi"), 50), finite(get("atr_ratio"), 1)
        ok = {
            "EMA_ADX20": adx >= 20,
            "EMA_ADX25": adx >= 25,
            "STRONG_ADX30": adx >= 30,
            "SLOPE_ADX25": adx >= 25 and abs(slope) >= .15 * finite(get("atr")),
            "RSI_MOMENTUM": adx >= 20 and d * (rsi - 50) >= 5,
            "PULLBACK": adx >= 20 and ((d == 1 and 40 <= rsi <= 55) or (d == -1 and 45 <= rsi <= 60)),
            "NORMAL_ATR_TREND": adx >= 20 and .75 <= ar <= 1.50,
            "LOW_ATR_TREND": adx >= 20 and ar < .90,
        }[name]
        if ok: return d
    return 0


CANDIDATES = ("EMA_ADX20", "EMA_ADX25", "STRONG_ADX30", "SLOPE_ADX25", "RSI_MOMENTUM", "PULLBACK", "NORMAL_ATR_TREND", "LOW_ATR_TREND")


def contiguous(bars, i, h, seconds):
    return all(bars[j]["time"] == bars[j-1]["time"] + seconds for j in range(i+1, i+h+1))


def entry_records(bars, frame, tf, candidate, start, end, wheel="none"):
    seconds = TIMEFRAMES[tf]; out = []
    for i in range(max(WARMUP, start), end - max(HORIZONS) - 1):
        row = frame[i]
        if not np.isfinite(row["slow_slope"]) or not contiguous(bars, i, max(HORIZONS), seconds): continue
        d = direction(row, candidate)
        if not d: continue
        wd = int(wheel_state(float(row["close"]), bars[i]["time"] + seconds, Strategy())['numerical_direction']) if wheel != "none" else 0
        if wheel == "confirmation" and wd != d: continue
        if wheel == "veto" and wd == -d: continue
        entry = bars[i+1]["open"]
        record = {"i": i, "time": bars[i+1]["time"], "date": ts(bars[i+1]["time"])[:10], "d": d, "entry": entry,
                  "atr": finite(row["atr"]), "wheel": wd}
        for h in HORIZONS:
            path = bars[i+1:i+h+1]
            record[f"ret_{h}"] = d * (bars[i+h]["close"] - entry)
            record[f"mfe_{h}"] = max(d*(x["high"]-entry) if d == 1 else d*(x["low"]-entry) for x in path)
            record[f"mae_{h}"] = max(-d*(x["low"]-entry) if d == 1 else -d*(x["high"]-entry) for x in path)
        out.append(record)
    return out


def entry_score(records):
    r = {"signals": len(records)}
    for h in HORIZONS:
        values = np.array([x[f"ret_{h}"] for x in records], float)
        r[str(h)] = {"expectancy": float(values.mean()) if len(values) else None, "accuracy": float((values > 0).mean()) if len(values) else None,
                     "mfe": float(np.mean([x[f"mfe_{h}"] for x in records])) if len(values) else None,
                     "mae": float(np.mean([x[f"mae_{h}"] for x in records])) if len(values) else None}
    return r


def entry_subwindows(records):
    groups = defaultdict(list)
    for x in records: groups[ts(x["time"])[:7]].append(x)
    return {k: entry_score(v) for k, v in sorted(groups.items())}


def signal_plan(bars, frame, tf, candidate, start, end, wheel):
    """Causal V1 stop/target geometry captured at the signal close."""
    cfg = Strategy(); seconds = TIMEFRAMES[tf]; plans = []
    for i in range(max(WARMUP, start), end-1):
        row = frame[i]
        if not np.isfinite(row["slow_slope"]) or bars[i+1]["time"] != bars[i]["time"] + seconds: continue
        d = direction(row, candidate)
        if not d: continue
        w = wheel_state(float(row["close"]), bars[i]["time"] + seconds, cfg)
        wd = int(w["numerical_direction"])
        if wheel == "confirmation" and wd != d: continue
        if wheel == "veto" and wd == -d: continue
        target = v1_targets(float(row["close"]), d, row, w, cfg, bars[i]["time"] + seconds)
        if not target["targets"] or not target["invalidation"]: continue
        entry, stop, take = bars[i+1]["open"], float(target["invalidation"]["price"]), float(target["targets"][0]["price"])
        if d*(entry-stop) <= 0 or d*(take-entry) <= 0: continue
        plans.append({"i": i, "entry_i": i+1, "time": bars[i+1]["time"], "date": ts(bars[i+1]["time"])[:10], "d": d, "entry": entry,
                      "stop": stop, "v1_target": take, "risk": abs(entry-stop)})
    return plans


def simulate(bars, plans, end, exit_kind="v1", hold_minutes=None, be=None):
    """One non-overlapping position; stop-first ambiguity; BE activates next bar."""
    trades=[]; next_free=-1
    for p in plans:
        if p["i"] < next_free or p["entry_i"] >= end: continue
        d, entry, stop = p["d"], p["entry"], p["stop"]
        target = p["v1_target"] if exit_kind == "v1" else entry + d * float(exit_kind) * p["risk"]
        if d*(target-entry) <= 0: continue
        if hold_minutes is None:
            last = min(end-1, p["entry_i"] + 30)  # current V1 30-bar cap
            scan_last = last; exit_price=bars[last]["close"]
        else:
            deadline = p["time"] + hold_minutes * 60
            last = next((j for j in range(p["entry_i"]+1, end) if bars[j]["time"] >= deadline), end-1)
            # A bar may be used only once it has closed by the deadline.
            scan_last=p["entry_i"]-1
            for j in range(p["entry_i"], last):
                if j+1 < len(bars) and bars[j+1]["time"] <= deadline: scan_last=j
                else: break
            exit_price=bars[last]["open"]
        active=False; exit_i=last; reason="time"
        mfe=mae=0.0
        for j in range(p["entry_i"], scan_last+1):
            b=bars[j]; favorable = b["high"] if d == 1 else b["low"]; adverse = b["low"] if d == 1 else b["high"]
            mfe=max(mfe, d*(favorable-entry)); mae=max(mae, -d*(adverse-entry))
            hit_stop = adverse <= stop if d == 1 else adverse >= stop
            hit_take = favorable >= target if d == 1 else favorable <= target
            if hit_stop:
                exit_i=j; exit_price=min(stop,b["open"]) if d == 1 else max(stop,b["open"]); reason="be" if active else "stop"; break
            if hit_take: exit_i=j; exit_price=target; reason="target"; break
            if be is not None and not active and d*(favorable-entry) >= be*p["risk"]: active=True
            if active: stop=entry
        pnl=d*(exit_price-entry)-COST
        trades.append({**p, "exit_i":exit_i, "exit_time":bars[exit_i]["time"], "pnl":pnl, "mfe":mfe, "mae":mae, "reason":reason,
                       "holding_minutes":(bars[exit_i]["time"]-p["time"])/60})
        next_free=exit_i+1
    return trades


def metrics(trades):
    p=np.array([x["pnl"] for x in trades],float); w=p[p>0]; l=p[p<0]
    curve=np.cumsum(p) if len(p) else np.array([]); peaks=np.maximum.accumulate(np.r_[0.,curve])[:-1] if len(p) else np.array([])
    dd=float(np.max(peaks-curve)) if len(p) else 0.
    return {"trades":len(p), "win_rate":float((p>0).mean()) if len(p) else None, "profit_factor":float(w.sum()/-l.sum()) if len(l) else None,
            "expectancy":float(p.mean()) if len(p) else None, "net_pnl":float(p.sum()), "average_win":float(w.mean()) if len(w) else None,
            "average_loss":float(l.mean()) if len(l) else None, "payoff_ratio":float(w.mean()/-l.mean()) if len(w) and len(l) else None,
            "max_drawdown":dd, "largest_loss":float(p.min()) if len(p) else None,
            "average_holding_minutes":float(np.mean([x["holding_minutes"] for x in trades])) if len(p) else None}


def periods(trades):
    groups=defaultdict(list)
    for x in trades: groups[ts(x["time"])[:7]].append(x)
    return {k: metrics(v) for k,v in sorted(groups.items())}


def quarterly(trades):
    groups=defaultdict(list)
    for x in trades:
        d=datetime.fromtimestamp(x["time"],timezone.utc); groups[f"{d.year}-Q{(d.month-1)//3+1}"].append(x)
    return {k:metrics(v) for k,v in sorted(groups.items())}


def outliers(trades):
    if not trades: return {}
    days=defaultdict(float)
    for x in trades: days[x["date"]]+=x["pnl"]
    best=max(trades,key=lambda x:x["pnl"]); worst=min(trades,key=lambda x:x["pnl"])
    bestday=max(days,key=days.get); worstday=min(days,key=days.get)
    sets={"all":trades,"without_best_trade":[x for x in trades if x is not best],"without_worst_trade":[x for x in trades if x is not worst],
          "without_best_day":[x for x in trades if x["date"]!=bestday],"without_worst_day":[x for x in trades if x["date"]!=worstday]}
    return {k:metrics(v) for k,v in sets.items()}


def write_docs(out):
    docs=ROOT/"docs"; r=out["timeframes"]
    split=[]
    for tf,x in r.items():
        for name,w in x["windows"].items(): split.append([tf,name,ts(w[0]),ts(w[1]),x["split_counts"][name]])
    (docs/"V4_LONG_HISTORY_PROTOCOL.md").write_text("# DIGITAL_TIME_WHEEL_V4_LONG_HISTORY_RESEARCH\n\nOffline research only: files are genuine `DIRECT_MT5` CSVs; this program imports no MT5 module, execution controller, or order API. Entries are known at a completed bar close and use the next contiguous bar open. Splits are chronological 60/20/20; ten bars are purged at each entry-quality boundary. Final holdout was not used for candidate, exit, holding-time, or breakeven selection. Fixed research cost is 0.40 quote-price units. Trade tests use one non-overlapping position and conservative stop-first resolution. Holding exits use the first subsequent bar open at or after the wall-clock deadline.\n\n## Splits\n\n"+table(["TF","Window","First UTC","Last UTC","Bars"],split)+"\n\nEight fixed, interpretable technical entries were evaluated independently: EMA_ADX20, EMA_ADX25, STRONG_ADX30, SLOPE_ADX25, RSI_MOMENTUM, PULLBACK, NORMAL_ATR_TREND, LOW_ATR_TREND. ATR regime uses prior data only. Time Wheel arms only filter a frozen technical candidate; they are not a source of entry direction.\n",encoding="utf-8")
    parts=["# V4 Entry Results\n"]
    for tf,x in r.items():
        parts.append(f"## {tf}\n\n")
        rows=[]
        for c,z in x["entries"].items():
            d=z["development"]; v=z["validation"]
            rows.append([c,d["signals"],fmt(d["5"]["expectancy"]),v["signals"],fmt(v["5"]["expectancy"]),fmt(v["5"]["accuracy"]),fmt(v["5"]["mfe"]),fmt(v["5"]["mae"])])
        parts.append(table(["Candidate","Dev n","Dev 5b exp","Val n","Val 5b exp","Val accuracy","Val MFE","Val MAE"],rows)+"\n\n")
        stable=x.get("validation_stability",{})
        parts.append("Frozen technical candidate: `"+str(x["frozen_technical"])+"`; leading validation-positive candidate used for attribution: `"+str(x.get("leading_technical"))+"`. Validation-month stability: `"+str(stable.get("positive_months"))+"/"+str(stable.get("months"))+"` positive 5-bar-expectancy months. Time Wheel comparison (validation):\n\n"+table(["Arm","Signals","5b expectancy","Accuracy","V1-exit PF","V1-exit DD"],[[k,v["signals"],fmt(v["5"]["expectancy"]),fmt(v["5"]["accuracy"]),fmt(x["wheel_trade_attribution"][k]["profit_factor"]),fmt(x["wheel_trade_attribution"][k]["max_drawdown"])] for k,v in x["wheel"].items()])+"\n\n")
    (docs/"V4_ENTRY_RESULTS.md").write_text("".join(parts),encoding="utf-8")
    parts=["# V4 Exit Results\n"]
    for tf,x in r.items():
        parts.append(f"## {tf}: {x['frozen_technical']}\n\n")
        parts.append(table(["Exit","Trades","PF","Expectancy","Net P/L","Max DD"],[[k,v["trades"],fmt(v["profit_factor"]),fmt(v["expectancy"]),fmt(v["net_pnl"]),fmt(v["max_drawdown"])] for k,v in x["exits"].items()])+"\n\n")
        parts.append("Holding-time results using frozen exit `"+str(x["frozen_exit"])+"`:\n\n"+table(["Limit","Trades","PF","Expectancy","Net P/L","Max DD"],[[k,v["trades"],fmt(v["profit_factor"]),fmt(v["expectancy"]),fmt(v["net_pnl"]),fmt(v["max_drawdown"])] for k,v in x["holding"].items()])+"\n\n")
        parts.append("Breakeven results using frozen exit/holding rule:\n\n"+table(["BE","Trades","PF","Expectancy","Net P/L","Max DD"],[[k,v["trades"],fmt(v["profit_factor"]),fmt(v["expectancy"]),fmt(v["net_pnl"]),fmt(v["max_drawdown"])] for k,v in x["breakeven"].items()])+"\n\n")
        parts.append("Validation quarterly stability for the frozen exit (before holding-time/BE selection):\n\n"+table(["Quarter","Trades","PF","Expectancy","Net P/L","Max DD"],[[k,v["trades"],fmt(v["profit_factor"]),fmt(v["expectancy"]),fmt(v["net_pnl"]),fmt(v["max_drawdown"])] for k,v in x.get("validation_quarters",{}).items()])+"\n\n")
    (docs/"V4_EXIT_RESULTS.md").write_text("".join(parts),encoding="utf-8")
    final=out["final"]
    holdout_text = "# V4 Final Holdout Results\n\n"
    if final["metrics"]["trades"] == 0 and final["name"].startswith("NONE"):
        holdout_text += "No candidate passed the pre-holdout validation gate, so the final holdout was intentionally not opened.\n"
    else:
        holdout_text += "Final frozen candidate: `"+final["name"]+"`. This is the first holdout evaluation.\n\n"+table(["Metric","Value"],[[k,fmt(v) if isinstance(v,float) else v] for k,v in final["metrics"].items()])+"\n\n## Outlier robustness\n\n"+table(["Adjustment","Trades","PF","Expectancy","Net P/L","Max DD"],[[k,v["trades"],fmt(v["profit_factor"]),fmt(v["expectancy"]),fmt(v["net_pnl"]),fmt(v["max_drawdown"])] for k,v in final["outliers"].items()])+"\n\n## Monthly holdout consistency\n\n"+table(["Month","Trades","PF","Expectancy","Net P/L","Max DD"],[[k,v["trades"],fmt(v["profit_factor"]),fmt(v["expectancy"]),fmt(v["net_pnl"]),fmt(v["max_drawdown"])] for k,v in final["periods"].items()])+"\n"
    (docs/"V4_HOLDOUT_RESULTS.md").write_text(holdout_text,encoding="utf-8")
    verdict=out["verdict"]
    (docs/"V4_FINAL_CANDIDATE.md").write_text("# V4 Final Candidate\n\n"+verdict+"\n",encoding="utf-8")


def main():
    cfg=Strategy(); out={"research_id":"DIGITAL_TIME_WHEEL_V4_LONG_HISTORY_RESEARCH","read_only":True,"timeframes":{}}
    frozen=[]
    for tf,path in FILES.items():
        bars=load(path); frame=enrich(bars,cfg).to_dict("records"); ws=windows(bars); data={"windows":{k:(bars[a]["time"],bars[b-1]["time"]) for k,(a,b) in ws.items()},"split_counts":{k:b-a for k,(a,b) in ws.items()},"entries":{}}
        for c in CANDIDATES:
            dev=entry_records(bars,frame,tf,c,*ws["development"],"none"); val=entry_records(bars,frame,tf,c,*ws["validation"],"none")
            data["entries"][c]={"development":entry_score(dev),"validation":entry_score(val),"validation_subwindows":entry_subwindows(val)}
        def stable(c):
            subs=data["entries"][c]["validation_subwindows"].values(); usable=[x for x in subs if x["signals"]>=30]
            return len(usable)>=3 and sum((x["5"]["expectancy"] or 0)>0 for x in usable)/len(usable)>=.60
        positive=[c for c in CANDIDATES if data["entries"][c]["validation"]["signals"]>=30 and (data["entries"][c]["validation"]["5"]["expectancy"] or 0)>0]
        leading=max(positive,key=lambda c:(data["entries"][c]["development"]["5"]["expectancy"] or -1e9)) if positive else None
        eligible=[c for c in positive if stable(c)]
        selected=max(eligible,key=lambda c:(data["entries"][c]["development"]["5"]["expectancy"] or -1e9)) if eligible else None
        data["frozen_technical"]=selected; data["leading_technical"]=leading
        data["wheel"]={}
        research_candidate=selected or leading
        if research_candidate:
            sub=data["entries"][research_candidate]["validation_subwindows"].values(); usable=[x for x in sub if x["signals"]>=30]
            data["validation_stability"]={"months":len(usable),"positive_months":sum((x["5"]["expectancy"] or 0)>0 for x in usable)}
            for mode in ("technical_only","confirmation","veto"):
                data["wheel"][mode]=entry_score(entry_records(bars,frame,tf,research_candidate,*ws["validation"],"none" if mode=="technical_only" else mode))
            data["wheel_trade_attribution"]={}
            for mode in ("technical_only","confirmation","veto"):
                wm="none" if mode=="technical_only" else mode; wp=signal_plan(bars,frame,tf,research_candidate,*ws["validation"],wm)
                data["wheel_trade_attribution"][mode]=metrics(simulate(bars,wp,ws["validation"][1],"v1",None,None))
            # Wheel is retained only if it improves validation expectancy without reducing count below 70%.
            use="none"; base=data["wheel"]["technical_only"]; alternatives=[m for m in ("confirmation","veto") if data["wheel"][m]["signals"]>=.7*base["signals"] and (data["wheel"][m]["5"]["expectancy"] or -1e9)>(base["5"]["expectancy"] or -1e9)]
            if alternatives: use=max(alternatives,key=lambda m:data["wheel"][m]["5"]["expectancy"])
            plans=signal_plan(bars,frame,tf,research_candidate,*ws["validation"],use)
            data["exits"]={k:metrics(simulate(bars,plans,ws["validation"][1],k,None,None)) for k in ("v1",.5,.75,1.,1.25,1.5)}
            data["frozen_exit"]=max(data["exits"],key=lambda k:((data["exits"][k]["expectancy"] or -1e9),data["exits"][k]["trades"]))
            data["validation_quarters"]=quarterly(simulate(bars,plans,ws["validation"][1],data["frozen_exit"],None,None))
            # Holding study is only meaningful when validation losers show at least 0.5R MFE.
            base_trades=simulate(bars,plans,ws["validation"][1],data["frozen_exit"],None,None)
            losers=[x for x in base_trades if x["pnl"]<0]; be_allowed=bool(losers) and np.mean([x["mfe"]>=.5*x["risk"] for x in losers])>=.20
            data["holding"]={("no_limit" if m is None else f"{m}m"):metrics(simulate(bars,plans,ws["validation"][1],data["frozen_exit"],m,None)) for m in (None,5,10,15,30,60)}
            data["frozen_holding"]=max(data["holding"],key=lambda k:((data["holding"][k]["expectancy"] or -1e9),data["holding"][k]["trades"]))
            hold=None if data["frozen_holding"]=="no_limit" else int(data["frozen_holding"][:-1])
            be_values=("none",.5,.75,1.) if be_allowed else ("none",)
            data["breakeven"]={str(x):metrics(simulate(bars,plans,ws["validation"][1],data["frozen_exit"],hold,None if x=="none" else x)) for x in be_values}
            data["frozen_be"]=max(data["breakeven"],key=lambda k:((data["breakeven"][k]["expectancy"] or -1e9),data["breakeven"][k]["trades"]))
            final_val=data["breakeven"][data["frozen_be"]]
            if selected: frozen.append((tf,selected,use,data["frozen_exit"],hold,None if data["frozen_be"]=="none" else float(data["frozen_be"]),final_val))
        else:
            data.update({"wheel_trade_attribution":{},"validation_stability":{},"validation_quarters":{},"exits":{},"holding":{},"breakeven":{},"frozen_exit":None,"frozen_holding":None,"frozen_be":None})
        out["timeframes"][tf]=data
    # Freeze one candidate using development+validation only, then inspect holdout exactly once.
    candidates=[x for x in frozen if x[6]["trades"]>=30 and (x[6]["profit_factor"] or 0)>1.10 and (x[6]["expectancy"] or 0)>0]
    if not candidates:
        out["final"]={"name":"NONE — no validation candidate met PF > 1.10, positive expectancy, and 30-trade minimum","metrics":metrics([]),"outliers":{},"periods":{}}
        out["verdict"]="No V4 candidate was frozen: the validation gate was not met. The final holdout remains uninspected, so there is no out-of-sample claim and V4 is not suitable for DEMO forward testing."
    else:
        winner=max(candidates,key=lambda x:((x[6]["expectancy"] or -1e9),(x[6]["profit_factor"] or 0)))
        tf,entry,wheel,exit_kind,hold,be,_=winner; bars=load(FILES[tf]); frame=enrich(bars,cfg).to_dict("records"); a,b=windows(bars)["holdout"]
        plans=signal_plan(bars,frame,tf,entry,a,b,wheel); trades=simulate(bars,plans,b,exit_kind,hold,be)
        m=metrics(trades); name=f"{tf} {entry}; wheel={wheel}; exit={exit_kind}R/V1; hold={'V1 30 bars' if hold is None else str(hold)+'m'}; BE={be}R"
        out["final"]={"name":name,"metrics":m,"outliers":outliers(trades),"periods":periods(trades)}
        robust=out["final"]["outliers"]
        pass_all=(m["trades"]>=30 and (m["profit_factor"] or 0)>1.10 and (m["expectancy"] or 0)>0 and all((robust[k]["expectancy"] or 0)>0 for k in robust if k!="all"))
        out["verdict"]=("The frozen candidate passes the stated holdout and outlier checks; DEMO forward testing may be considered with auto trading still disabled until separately authorized." if pass_all else "The frozen candidate failed one or more final holdout/outlier requirements. Positive expectancy is not demonstrated as robustly out-of-sample; V4 is not suitable for DEMO forward testing.")
    (ROOT/"docs"/"V4_LONG_HISTORY_RESULTS.json").write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    write_docs(out); print(json.dumps(out["final"],indent=2))


if __name__=="__main__": main()
