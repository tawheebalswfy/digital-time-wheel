"""Forensic timeframe attribution: MT5 report rows matched only by persisted ticket."""
from __future__ import annotations
import json, sqlite3, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_demo_report import parse_report

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'ReportHistory-52960017.html'; DB=ROOT/'runtime/timewheel.sqlite3'
FMT='%Y.%m.%d %H:%M:%S'

def metric(rows):
 vals=[r['net_pl'] for r in rows]; wins=[v for v in vals if v>0]; losses=[v for v in vals if v<0]
 eq=peak=dd=0.; sw=sl=0; cw=cl=0
 for r in sorted(rows,key=lambda x:x['close_time']):
  eq+=r['net_pl']; peak=max(peak,eq); dd=max(dd,peak-eq)
  if r['net_pl']>0: sw+=1;sl=0
  elif r['net_pl']<0: sl+=1;sw=0
  else: sw=sl=0
  cw=max(cw,sw);cl=max(cl,sl)
 rr=[r['planned_rr'] for r in rows if r.get('planned_rr') is not None]
 return {'trades':len(vals),'wins':len(wins),'losses':len(losses),'win_rate':len(wins)/len(vals) if vals else None,'gross_profit':sum(wins),'gross_loss':sum(losses),'net_pl':sum(vals),'profit_factor':sum(wins)/abs(sum(losses)) if losses else None,'expectancy':sum(vals)/len(vals) if vals else None,'average_win':sum(wins)/len(wins) if wins else None,'average_loss':sum(losses)/len(losses) if losses else None,'payoff_ratio':(sum(wins)/len(wins))/abs(sum(losses)/len(losses)) if wins and losses else None,'largest_win':max(vals) if vals else None,'largest_loss':min(vals) if vals else None,'max_drawdown':dd,'max_consecutive_wins':cw,'max_consecutive_losses':cl,'avg_sl':statistics.mean([r['planned_risk_distance'] for r in rows]) if rows else None,'avg_tp':statistics.mean([r['planned_reward_distance'] for r in rows]) if rows else None,'avg_rr':statistics.mean(rr) if rr else None,'avg_duration_min':statistics.mean([r['duration_seconds']/60 for r in rows]) if rows else None,'median_duration_min':statistics.median([r['duration_seconds']/60 for r in rows]) if rows else None}

def side_metrics(rows):
 return {s:metric([r for r in rows if r['direction']==s]) for s in ('buy','sell')}

def load_db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 rows=c.execute('select * from execution_orders').fetchall(); out={}
 for row in rows:
  ticket=row['position_ticket']
  if not ticket: continue
  payload=json.loads(row['request_payload']) if row['request_payload'] else {}
  out[str(ticket)]={'symbol':row['symbol'],'timeframe':row['timeframe'],'signal_id':row['signal_id'],'strategy_version':payload.get('strategy_version'),'magic':20260910,'created_at':row['created_at'],'request':payload}
 return out

def main():
 report=parse_report(REPORT); db=load_db(); matched=[]; unmatched=[]
 for t in report:
  link=db.get(str(t['position']))
  x=dict(t)
  if link and link['symbol']==t['symbol']:
   x.update({'match':'MATCHED','timeframe':link['timeframe'],'signal_id':link['signal_id'],'strategy_version':link['strategy_version'],'magic':link['magic']}); matched.append(x)
  else:
   x.update({'match':'UNMATCHED','timeframe':None,'signal_id':None,'strategy_version':None,'magic':None}); unmatched.append(x)
 by_tf=defaultdict(list); by_st=defaultdict(list)
 for t in matched: by_tf[t['timeframe']].append(t); by_st[(t['symbol'],t['timeframe'])].append(t)
 # clusters use 60-second entry proximity, but classification requires matched evidence.
 grouped=[]; ordered=sorted(report,key=lambda t:datetime.strptime(t['open_time'],FMT)); current=[]; key=None; last=None
 for t in ordered:
  dt=datetime.strptime(t['open_time'],FMT); k=(t['symbol'],t['direction'])
  if key!=k or last is None or (dt-last).total_seconds()>60:
   if len(current)>1: grouped.append(current)
   current=[t]
  else: current.append(t)
  key=k;last=dt
 if len(current)>1: grouped.append(current)
 clusters=[]
 for c in grouped:
  links=[next((m for m in matched if m['position']==t['position']),None) for t in c]
  tfs={m['timeframe'] for m in links if m and m['timeframe']}; sigs={m['signal_id'] for m in links if m and m['signal_id']}
  if len(tfs)>1: cls='LEGITIMATE_MULTI_TIMEFRAME'
  elif len(links)==len(c) and len(tfs)==1 and len(sigs)==1: cls='PROVEN_DUPLICATE_SAME_TIMEFRAME'
  else: cls='UNRESOLVED'
  clusters.append({'open_time':c[0]['open_time'],'symbol':c[0]['symbol'],'direction':c[0]['direction'],'classification':cls,'tickets':[t['position'] for t in c],'timeframes':[m['timeframe'] if m else None for m in links],'signal_ids':[m['signal_id'] if m else None for m in links],'net_pl':sum(t['net_pl'] for t in c),'count':len(c)})
 # Exposure buckets for matched clusters only.
 exposure=defaultdict(list)
 for c in clusters:
  matched_c=[m for m in matched if m['position'] in c['tickets']]
  distinct=len({m['timeframe'] for m in matched_c})
  if distinct: exposure[min(distinct,4)].append(c)
 data={'report_trades':len(report),'matched_trades':len(matched),'unmatched_trades':len(unmatched),'match_pct':len(matched)/len(report)*100,'matched':matched,'unmatched':unmatched,'by_timeframe':{k:metric(v) for k,v in by_tf.items()},'by_symbol_timeframe':{f'{k[0]} {k[1]}':metric(v) for k,v in by_st.items()},'buy_sell':{k:side_metrics(v) for k,v in by_tf.items()},'clusters':clusters,'exposure':{str(k):{'events':len(v),'trades':sum(x['count'] for x in v),'combined_pl':sum(x['net_pl'] for x in v),'average_event_pl':sum(x['net_pl'] for x in v)/len(v),'worst_event_loss':min((x['net_pl'] for x in v),default=0)} for k,v in exposure.items()}}
 Path(ROOT/'runtime/timeframe_attribution.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 print(json.dumps({'report':len(report),'matched':len(matched),'unmatched':len(unmatched),'clusters':{k:sum(x['classification']==k for x in clusters) for k in ('LEGITIMATE_MULTI_TIMEFRAME','PROVEN_DUPLICATE_SAME_TIMEFRAME','UNRESOLVED')},'timeframes':{k:v['net_pl'] for k,v in data['by_timeframe'].items()}},indent=2))

if __name__=='__main__': main()
