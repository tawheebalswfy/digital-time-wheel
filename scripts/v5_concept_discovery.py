"""Offline V5 concept discovery. No MT5, execution, or production imports."""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from backend.app.config import Strategy, TIMEFRAMES
from backend.app.technical import features, finite
from backend.app.wheel import state as wheel_state

FILES={x:ROOT/'data'/'history'/f'XAUUSD_{x}.csv' for x in ('M15','M30','H1')}
H=(1,2,3,5,10); WARM=150; COST=.40
CONCEPTS=('TREND_CONTINUATION','PULLBACK_CONTINUATION','BREAKOUT','MEAN_REVERSION','VOLATILITY_EXPANSION')
def iso(t):return datetime.fromtimestamp(int(t),timezone.utc).isoformat()
def f(x):return '—' if x is None else f'{x:.3f}'
def tbl(h,r):return '| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+'\n'.join('| '+' | '.join(map(str,x))+' |' for x in r)
def load(p):
 with p.open(encoding='utf-8') as z:r=list(csv.DictReader(z))
 for x in r:
  x['time']=int(x['time'])
  for k in ('open','high','low','close','tick_volume','spread','real_volume'):x[k]=float(x[k])
 return r
def split(b):
 n=len(b);return {'development':(0,int(n*.6)),'validation':(int(n*.6),int(n*.8)),'holdout':(int(n*.8),n)}
def enrich(b,c):
 q=features(b,c);q['slope']=q.ema_slow-q.ema_slow.shift(3);q['atr_ratio']=q.atr/q.atr.shift(1).rolling(100,min_periods=30).median();q['atr_prev_ratio']=q.atr_ratio.shift(1);q['high10']=q.high.shift(1).rolling(10).max();q['low10']=q.low.shift(1).rolling(10).min();return q.to_dict('records')
def sig(r,name):
 g=lambda k:finite(r[k]);d=1 if g('ema_fast')>g('ema_slow') and g('slope')>0 and g('plus_di')>g('minus_di') else -1 if g('ema_fast')<g('ema_slow') and g('slope')<0 and g('minus_di')>g('plus_di') else 0
 c=float(r['close']);a=g('atr');adx=g('adx');rsi=finite(r['rsi'],50);ar=finite(r['atr_ratio'],1)
 if name=='TREND_CONTINUATION':return d if d and adx>=20 and d*(c-g('ema_fast'))>0 and .75<=ar<=1.5 else 0
 if name=='PULLBACK_CONTINUATION':return d if d and adx>=20 and ((d==1 and 40<=rsi<=55 and c<=g('ema_fast')+.25*a) or (d==-1 and 45<=rsi<=60 and c>=g('ema_fast')-.25*a)) else 0
 if name=='BREAKOUT':return 1 if adx>=20 and ar>=.9 and c>g('high10') else -1 if adx>=20 and ar>=.9 and c<g('low10') else 0
 if name=='MEAN_REVERSION':return -1 if adx<=15 and rsi>=70 and c-g('ema_slow')>=a else 1 if adx<=15 and rsi<=30 and g('ema_slow')-c>=a else 0
 if name=='VOLATILITY_EXPANSION':return 1 if ar>=1.1 and finite(r['atr_prev_ratio'],1)<=.85 and c>g('high10') else -1 if ar>=1.1 and finite(r['atr_prev_ratio'],1)<=.85 and c<g('low10') else 0
 return 0
def contiguous(b,i,h,s):return all(b[j]['time']==b[j-1]['time']+s for j in range(i+1,i+h+1))
def records(b,q,tf,name,a,z,wheel='none'):
 s=TIMEFRAMES[tf];out=[];cfg=Strategy()
 for i in range(max(WARM,a),z-max(H)-1):
  if not contiguous(b,i,max(H),s):continue
  d=sig(q[i],name)
  if not d:continue
  wd=int(wheel_state(float(q[i]['close']),b[i]['time']+s,cfg)['numerical_direction']) if wheel!='none' else 0
  if wheel=='confirmation' and wd!=d:continue
  if wheel=='veto' and wd==-d:continue
  e=b[i+1]['open'];x={'i':i,'time':b[i+1]['time'],'date':iso(b[i+1]['time'])[:10],'d':d,'entry':e,'atr':finite(q[i]['atr']),'row':q[i]}
  for h in H:
   path=b[i+1:i+h+1];x[f'r{h}']=d*(b[i+h]['close']-e);x[f'mfe{h}']=max((v['high']-e) if d==1 else (e-v['low']) for v in path);x[f'mae{h}']=max((e-v['low']) if d==1 else (v['high']-e) for v in path)
  out.append(x)
 return out
def score(x):
 o={'signals':len(x)}
 for h in H:
  v=np.array([a[f'r{h}'] for a in x],float);mfe=np.mean([a[f'mfe{h}'] for a in x]) if len(x) else None;mae=np.mean([a[f'mae{h}'] for a in x]) if len(x) else None
  o[str(h)]={'expectancy':float(v.mean()) if len(v) else None,'median':float(np.median(v)) if len(v) else None,'accuracy':float((v>0).mean()) if len(v) else None,'mfe':float(mfe) if mfe is not None else None,'mae':float(mae) if mae is not None else None,'mfe_mae_ratio':float(mfe/mae) if mae else None}
 return o
def months(x):
 d=defaultdict(list)
 for v in x:d[iso(v['time'])[:7]].append(v)
 return {k:score(v) for k,v in sorted(d.items())}
def plan(x,stop_rule):
 out=[]
 for p in x:
  d,e,a=p['d'],p['entry'],p['atr'];r=p['row'];struct=finite(r['support']) if d==1 else finite(r['resistance'])
  fallback=e-d*1.5*a
  if not struct or d*(e-struct)<=0:struct=fallback
  stop=struct if stop_rule=='structural' else (max(struct,e-1.5*a) if d==1 else min(struct,e+1.5*a))
  if d*(e-stop)>0:out.append({**p,'stop':stop,'risk':abs(e-stop)})
 return out
def sim(b,p,z,R,hold=None):
 trades=[];free=-1
 for x in p:
  if x['i']<free or x['i']+1>=z:continue
  k=x['i']+1;d=x['d'];e=x['entry'];st=x['stop'];tp=e+d*R*x['risk']
  if hold is None:last=min(z-1,k+30);scan=last;px=b[last]['close']
  else:
   deadline=x['time']+hold*60;last=next((j for j in range(k+1,z) if b[j]['time']>=deadline),z-1);scan=k-1
   for j in range(k,last):
    if b[j+1]['time']<=deadline:scan=j
    else:break
   px=b[last]['open']
  ei=last;reason='time'
  for j in range(k,scan+1):
   hi,lo=b[j]['high'],b[j]['low'];hitst=lo<=st if d==1 else hi>=st;hittp=hi>=tp if d==1 else lo<=tp
   if hitst:ei=j;px=min(st,b[j]['open']) if d==1 else max(st,b[j]['open']);reason='stop';break
   if hittp:ei=j;px=tp;reason='target';break
  trades.append({**x,'pnl':d*(px-e)-COST,'exit_i':ei,'exit_time':b[ei]['time'],'hold':(b[ei]['time']-x['time'])/60,'reason':reason});free=ei+1
 return trades
def metrics(t):
 p=np.array([x['pnl'] for x in t],float);w=p[p>0];l=p[p<0];curve=np.cumsum(p) if len(p) else np.array([]);peaks=np.maximum.accumulate(np.r_[0.,curve])[:-1] if len(p) else np.array([])
 return {'trades':len(p),'win_rate':float((p>0).mean()) if len(p) else None,'profit_factor':float(w.sum()/-l.sum()) if len(l) else None,'expectancy':float(p.mean()) if len(p) else None,'net_pnl':float(p.sum()),'average_win':float(w.mean()) if len(w) else None,'average_loss':float(l.mean()) if len(l) else None,'payoff_ratio':float(w.mean()/-l.mean()) if len(w) and len(l) else None,'max_drawdown':float(np.max(peaks-curve)) if len(p) else 0,'largest_loss':float(p.min()) if len(p) else None,'average_duration':float(np.mean([x['hold'] for x in t])) if len(t) else None}
def groups(t,key):
 d=defaultdict(list)
 for x in t:
  dt=datetime.fromtimestamp(x['time'],timezone.utc);k=iso(x['time'])[:7] if key=='month' else f'{dt.year}-Q{(dt.month-1)//3+1}' if key=='quarter' else str(dt.year) if key=='year' else ('BUY' if x['d']==1 else 'SELL')
  d[k].append(x)
 return {k:metrics(v) for k,v in sorted(d.items())}
def outlier(t):
 if not t:return {}
 ds=defaultdict(float)
 for x in t:ds[x['date']]+=x['pnl']
 bt=max(t,key=lambda x:x['pnl']);wt=min(t,key=lambda x:x['pnl']);bd=max(ds,key=ds.get);wd=min(ds,key=ds.get)
 return {k:metrics(v) for k,v in {'all':t,'without_best_trade':[x for x in t if x is not bt],'without_worst_trade':[x for x in t if x is not wt],'without_best_day':[x for x in t if x['date']!=bd],'without_worst_day':[x for x in t if x['date']!=wd]}.items()}
def write(o):
 d=ROOT/'docs';rows=[]
 for tf,x in o['timeframes'].items():
  for n,(a,z) in x['windows'].items():rows.append([tf,n,iso(a),iso(z),x['counts'][n]])
 (d/'V5_CONCEPT_DISCOVERY_PROTOCOL.md').write_text('# DIGITAL_TIME_WHEEL_V5_CONCEPT_DISCOVERY\n\nOffline, read-only study using only direct-MT5 CSVs. Five fixed, distinct technical archetypes were tested; no parameter sweep, no MT5 import, no order API. Signal is at completed-bar close, entry next contiguous-bar open, and the holdout is absent from all discovery/selection loops. Time Wheel is tested only after a concept passes the development/validation entry gates.\n\n'+tbl(['TF','Split','First UTC','Last UTC','Bars'],rows)+'\n\nConcepts: TREND_CONTINUATION, PULLBACK_CONTINUATION, BREAKOUT, MEAN_REVERSION, VOLATILITY_EXPANSION.\n',encoding='utf-8')
 p=['# V5 Concept Results\n']
 for tf,x in o['timeframes'].items():
  p+=[f'## {tf}\n\n',tbl(['Concept','Dev n','Dev 5b exp','Val n','Val 5b exp','Val accuracy','Val MFE/MAE'],[[c,x['concepts'][c]['development']['signals'],f(x['concepts'][c]['development']['5']['expectancy']),x['concepts'][c]['validation']['signals'],f(x['concepts'][c]['validation']['5']['expectancy']),f(x['concepts'][c]['validation']['5']['accuracy']),f(x['concepts'][c]['validation']['5']['mfe_mae_ratio'])] for c in CONCEPTS]),'\n\n']
 (d/'V5_CONCEPT_RESULTS.md').write_text(''.join(p),encoding='utf-8')
 p=['# V5 Validation Results\n']
 for tf,x in o['timeframes'].items():
  p+=[f'## {tf}\n\nLeading validation-positive concept: `{x["leading"]}`; frozen: `{x["frozen"]}`.\n\n']
  if x['frozen']:
   p+=[tbl(['Exit','Trades','PF','Expectancy','Net P/L','Max DD'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['net_pnl']),f(v['max_drawdown'])] for k,v in x['exits'].items()]),'\n\n',tbl(['Quarter','Trades','PF','Expectancy','Max DD'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['max_drawdown'])] for k,v in x['quarters'].items()]),'\n\n']
 (d/'V5_VALIDATION_RESULTS.md').write_text(''.join(p),encoding='utf-8')
 p=['# V5 Time Wheel Incremental Test\n']
 for tf,x in o['timeframes'].items():
  p+=[f'## {tf}\n\n']
  if x['tw']:p+=[tbl(['Arm','Signals','5b expectancy','PF','Max DD'],[[k,v['entry']['signals'],f(v['entry']['5']['expectancy']),f(v['trade']['profit_factor']),f(v['trade']['max_drawdown'])] for k,v in x['tw'].items()]),'\n\n']
  else:p+=['No concept passed the validation entry gate; Time Wheel remained informational only.\n\n']
 (d/'V5_TIME_WHEEL_INCREMENTAL_TEST.md').write_text(''.join(p),encoding='utf-8')
 (d/'V5_FINAL_DECISION.md').write_text('# V5 Final Decision\n\n'+o['decision']+'\n',encoding='utf-8')
def main():
 o={'research_id':'DIGITAL_TIME_WHEEL_V5_CONCEPT_DISCOVERY','read_only':True,'timeframes':{}};frozen=[];cfg=Strategy()
 for tf,path in FILES.items():
  b=load(path);q=enrich(b,cfg);w=split(b);x={'windows':{k:(b[a]['time'],b[z-1]['time']) for k,(a,z) in w.items()},'counts':{k:z-a for k,(a,z) in w.items()},'concepts':{}}
  raw={}
  for c in CONCEPTS:
   dev=records(b,q,tf,c,*w['development']);val=records(b,q,tf,c,*w['validation']);raw[c]=(dev,val);x['concepts'][c]={'development':score(dev),'validation':score(val),'validation_months':months(val)}
  def stable(c):
   m=[v for v in x['concepts'][c]['validation_months'].values() if v['signals']>=30];return len(m)>=3 and sum((v['5']['expectancy'] or 0)>0 for v in m)/len(m)>=.60
  good=[c for c in CONCEPTS if x['concepts'][c]['development']['signals']>=50 and (x['concepts'][c]['development']['5']['expectancy'] or 0)>0 and x['concepts'][c]['validation']['signals']>=50 and (x['concepts'][c]['validation']['5']['expectancy'] or 0)>0]
  x['leading']=max(good,key=lambda c:x['concepts'][c]['development']['5']['expectancy']) if good else None
  eligible=[c for c in good if stable(c)];x['frozen']=max(eligible,key=lambda c:x['concepts'][c]['validation']['5']['expectancy']) if eligible else None;x['exits']={};x['quarters']={};x['tw']={}
  if x['frozen']:
   c=x['frozen'];plans={rule:plan(raw[c][1],rule) for rule in ('structural','atr_capped_structural')}
   for rule,ps in plans.items():
    for R in (.5,.75,1.,1.25,1.5):x['exits'][f'{rule}_{R}R']=metrics(sim(b,ps,w['validation'][1],R))
   best=max(x['exits'],key=lambda k:(x['exits'][k]['expectancy'] or -1e9));rule,R=best.rsplit('_',1);R=float(R[:-1]);ps=plans[rule];x['best_exit']=best;x['quarters']=groups(sim(b,ps,w['validation'][1],R),'quarter')
   base=raw[c][1]
   for mode in ('alone','confirmation','veto'):
    rec=base if mode=='alone' else records(b,q,tf,c,*w['validation'],mode);tr=sim(b,plan(rec,rule),w['validation'][1],R);x['tw'][mode]={'entry':score(rec),'trade':metrics(tr)}
   chosen=max(x['tw'],key=lambda k:(x['tw'][k]['trade']['expectancy'] or -1e9));x['best_tw']=chosen
   finalv=x['tw'][chosen]['trade'];
   if finalv['trades']>=30 and (finalv['profit_factor'] or 0)>1.10 and (finalv['expectancy'] or 0)>0:frozen.append((tf,c,rule,R,chosen,finalv))
  o['timeframes'][tf]=x
 if not frozen:
  o['final']={'name':'NONE','metrics':metrics([]),'outliers':{},'periods':{}};o['decision']='**NO ROBUST CONCEPT FOUND.** No concept met the development, validation stability, and executable validation PF/expectancy gates; the final holdout was not opened. Do not launch another parameter sweep. Prefer a different instrument or a new timeframe/data family, and reconsider the Time Wheel as informational unless it later demonstrates independent incremental value.'
 else:
  winner=max(frozen,key=lambda v:(v[5]['expectancy'],v[5]['profit_factor']));tf,c,rule,R,wm,_=winner;b=load(FILES[tf]);q=enrich(b,cfg);a,z=split(b)['holdout'];rec=records(b,q,tf,c,a,z,'none' if wm=='alone' else wm);tr=sim(b,plan(rec,rule),z,R);o['final']={'name':f'{tf} {c} {rule} {R}R wheel={wm}','metrics':metrics(tr),'outliers':outlier(tr),'periods':groups(tr,'quarter')};o['decision']='Frozen candidate evaluated once on untouched holdout. See metrics and outlier checks in the JSON audit.'
 (ROOT/'docs'/'V5_CONCEPT_DISCOVERY_RESULTS.json').write_text(json.dumps(o,indent=2,allow_nan=False),encoding='utf-8');write(o);print(json.dumps(o['final'],indent=2))
if __name__=='__main__':main()
