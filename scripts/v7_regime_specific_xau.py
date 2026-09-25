"""Offline XAUUSD-only V7 regime study; no MT5/order/production APIs."""
from __future__ import annotations
import json,sys,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.config import Strategy,TIMEFRAMES
from backend.app.technical import features,finite
from backend.app.wheel import state as wheel_state
from scripts.v5_concept_discovery import load,split,score,months,plan,sim,metrics,groups,outlier,iso,f,tbl,H,WARM
TFS=('M5','M15','M30','H1','H4','D1');FILES={x:ROOT/'data'/'history'/f'XAUUSD_{x}.csv' for x in TFS}
PAIRS=(('STRONG_TREND','TREND_CONTINUATION'),('STRONG_TREND','PULLBACK_CONTINUATION'),('RANGE_LOW_VOL','MEAN_REVERSION'),('RANGE_NORMAL_VOL','RANGE_FADE'),('HIGH_VOL_EXPANSION','BREAKOUT'),('HIGH_VOL_EXPANSION','VOLATILITY_EXPANSION'))
def enrich(b):
 q=features(b,Strategy());q['slope']=q.ema_slow-q.ema_slow.shift(3);q['atr_ratio']=q.atr/q.atr.shift(1).rolling(100,min_periods=30).median();q['q33']=q.atr_ratio.shift(1).rolling(100,min_periods=30).quantile(.333);q['q67']=q.atr_ratio.shift(1).rolling(100,min_periods=30).quantile(.667);q['h20']=q.high.shift(1).rolling(20).max();q['l20']=q.low.shift(1).rolling(20).min();return q.to_dict('records')
def regime(r):
 a=finite(r['atr']);adx=finite(r['adx']);sl=abs(finite(r['slope']));ar=finite(r['atr_ratio'],1);lo=finite(r['q33'],.85);hi=finite(r['q67'],1.15);p=float(r['close'])
 if adx>=25 and sl>=.15*a:return 'STRONG_TREND'
 if adx>=15:return 'WEAK_TREND'
 if ar<=lo:return 'RANGE_LOW_VOL'
 if ar<hi:return 'RANGE_NORMAL_VOL'
 if ar>=hi and (p>finite(r['h20']) or p<finite(r['l20'])):return 'HIGH_VOL_EXPANSION'
 return 'TRANSITION'
def direction(r,c):
 g=lambda k:finite(r[k]);p=float(r['close']);a=g('atr');rsi=finite(r['rsi'],50);trend=1 if g('ema_fast')>g('ema_slow') and g('slope')>0 and g('plus_di')>g('minus_di') else -1 if g('ema_fast')<g('ema_slow') and g('slope')<0 and g('minus_di')>g('plus_di') else 0
 if c=='TREND_CONTINUATION':return trend if trend and p*trend>g('ema_fast')*trend else 0
 if c=='PULLBACK_CONTINUATION':return trend if trend and ((trend==1 and 40<=rsi<=55 and p<=g('ema_fast')+.3*a) or(trend==-1 and 45<=rsi<=60 and p>=g('ema_fast')-.3*a)) else 0
 if c=='MEAN_REVERSION':return -1 if rsi>=65 and p-g('ema_slow')>=a else 1 if rsi<=35 and g('ema_slow')-p>=a else 0
 if c=='RANGE_FADE':return -1 if p>=g('resistance')-.2*a else 1 if p<=g('support')+.2*a else 0
 if c in ('BREAKOUT','VOLATILITY_EXPANSION'):return 1 if p>g('h20') else -1 if p<g('l20') else 0
 return 0
def valid_gap(b,i,h,s,tf):
 maxgap=4*86400 if tf=='D1' else s
 return not any((b[j]['time']-b[j-1]['time'])>maxgap or(tf!='D1' and b[j]['time']!=b[j-1]['time']+s) for j in range(i+1,i+h+1))
def rec(b,q,tf,pair,a,z,wheel='none'):
 s=TIMEFRAMES[tf];rg,c=pair;out=[];cfg=Strategy()
 for i in range(max(WARM,a),z-max(H)-1):
  if not valid_gap(b,i,max(H),s,tf) or regime(q[i])!=rg:continue
  d=direction(q[i],c)
  if not d:continue
  wd=int(wheel_state(float(q[i]['close']),b[i]['time']+s,cfg)['numerical_direction']) if wheel!='none' else 0
  if wheel=='confirmation' and wd!=d:continue
  if wheel=='veto' and wd==-d:continue
  e=b[i+1]['open'];x={'i':i,'time':b[i+1]['time'],'date':iso(b[i+1]['time'])[:10],'d':d,'entry':e,'atr':finite(q[i]['atr']),'row':q[i],'regime':rg}
  for h in H:
   path=b[i+1:i+h+1];x[f'r{h}']=d*(b[i+h]['close']-e);x[f'mfe{h}']=max((v['high']-e) if d==1 else(e-v['low']) for v in path);x[f'mae{h}']=max((e-v['low']) if d==1 else(v['high']-e) for v in path)
  out.append(x)
 return out
def freq(q):
 d=defaultdict(list)
 for i,r in enumerate(q):d[regime(r)].append(i)
 n=len(q);trans=sum(regime(q[i])!=regime(q[i-1]) for i in range(1,n));out={}
 for k,v in d.items():
  runs=[];cur=0
  for r in q:
   if regime(r)==k:cur+=1
   elif cur:runs.append(cur);cur=0
  if cur:runs.append(cur)
  out[k]={'percent':len(v)/n*100,'average_duration_bars':float(np.mean(runs)) if runs else 0}
 return out,trans
def sub(x,key):
 d=defaultdict(list)
 for v in x:
  if key=='direction':k='BUY' if v['d']==1 else 'SELL'
  else:
   h=datetime.fromtimestamp(v['time'],timezone.utc).hour;k='Asia' if h<7 else 'London' if h<13 else 'Overlap' if h<17 else 'New_York'
  d[k].append(v)
 return {k:score(v)['5']|{'signals':len(v)} for k,v in sorted(d.items())}
def write(o):
 d=ROOT/'docs';defs='''# V7 Regime Definitions\n\n- **STRONG_TREND**: ADX ≥25 and absolute 3-bar slow-EMA slope ≥0.15 ATR.\n- **WEAK_TREND**: ADX 15–24 not qualifying as strong.\n- **RANGE_LOW_VOL**: ADX <15 and causal normalized-ATR lower rolling third.\n- **RANGE_NORMAL_VOL**: ADX <15 and causal normalized ATR between rolling thirds.\n- **HIGH_VOL_EXPANSION**: normalized ATR at/above upper rolling third and a causal 20-bar range break.\n- **TRANSITION**: all remaining bars; no trade tested.\n\nRolling quantiles use only completed prior bars.\n''';(d/'V7_REGIME_DEFINITIONS.md').write_text(defs,encoding='utf-8')
 p=['# V7 Regime Protocol\n\nXAUUSD-only, offline direct-MT5 study. Fixed 60/20/20 chronological partitions; final segments were not read in selection. Matched pairs only: strong-trend continuation/pullback, low/normal range mean-reversion/fade, high-volatility breakout/expansion.\n\n']
 for tf,x in o['timeframes'].items():p+=[f'## {tf}\n\n',tbl(['Regime','% bars','Average duration (bars)'],[[k,f(v['percent']),f(v['average_duration_bars'])] for k,v in x['frequency'].items()]),f'\n\nTransitions: {x["transitions"]}.\n\n']
 (d/'V7_REGIME_PROTOCOL.md').write_text(''.join(p),encoding='utf-8')
 p=['# V7 Regime Entry Results\n']
 for tf,x in o['timeframes'].items():p+=[f'## {tf}\n\n',tbl(['Regime / concept','Dev n','Dev 5b exp','Val n','Val 5b exp','Accuracy','MFE/MAE'],[[f'{a} / {c}',x['pairs'][(a,c)]['development']['signals'],f(x['pairs'][(a,c)]['development']['5']['expectancy']),x['pairs'][(a,c)]['validation']['signals'],f(x['pairs'][(a,c)]['validation']['5']['expectancy']),f(x['pairs'][(a,c)]['validation']['5']['accuracy']),f(x['pairs'][(a,c)]['validation']['5']['mfe_mae_ratio'])] for a,c in PAIRS]),f'\n\nLeading: `{x["leading"]}`; frozen: `{x["frozen"]}`.\n\n']
 (d/'V7_REGIME_ENTRY_RESULTS.md').write_text(''.join(p),encoding='utf-8')
 p=['# V7 Regime Exit Results\n']
 for tf,x in o['timeframes'].items():
  p+=[f'## {tf}\n\n']
  if x['exits']:p+=[tbl(['Exit','Trades','PF','Expectancy','Net P/L','Max DD'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['net_pnl']),f(v['max_drawdown'])] for k,v in x['exits'].items()]),'\n\n']
  else:p+=['No regime pair passed the entry gate; no exit fitting was performed.\n\n']
 (d/'V7_REGIME_EXIT_RESULTS.md').write_text(''.join(p),encoding='utf-8')
 (d/'V7_HOLDOUT_RESULTS.md').write_text('# V7 Holdout Results\n\n'+('No candidate passed pre-holdout gates; holdouts remain untouched.' if o['final']['name']=='NONE' else json.dumps(o['final'],indent=2))+'\n',encoding='utf-8')
 (d/'V7_FINAL_DECISION.md').write_text('# V7 Final Decision\n\n'+o['decision']+'\n',encoding='utf-8')
def main():
 o={'research_id':'DIGITAL_TIME_WHEEL_V7_REGIME_SPECIFIC_XAU','read_only':True,'timeframes':{}};winners=[]
 for tf,path in FILES.items():
  b=load(path);q=enrich(b);w=split(b);fr,tr=freq(q);x={'frequency':fr,'transitions':tr,'pairs':{},'exits':{},'tw':{}}
  raw={}
  for pair in PAIRS:
   dev=rec(b,q,tf,pair,*w['development']);val=rec(b,q,tf,pair,*w['validation']);raw[pair]=(dev,val);x['pairs'][pair]={'development':score(dev),'validation':score(val),'months':months(val)}
  good=[p for p in PAIRS if x['pairs'][p]['development']['signals']>=50 and (x['pairs'][p]['development']['5']['expectancy'] or 0)>0 and x['pairs'][p]['validation']['signals']>=50 and (x['pairs'][p]['validation']['5']['expectancy'] or 0)>0]
  x['leading']=max(good,key=lambda p:x['pairs'][p]['validation']['5']['expectancy']) if good else max(PAIRS,key=lambda p:x['pairs'][p]['validation']['5']['expectancy'] or -1e9)
  def stable(p):
   m=[v for v in x['pairs'][p]['months'].values() if v['signals']>=30];return len(m)>=3 and sum((v['5']['expectancy'] or 0)>0 for v in m)/len(m)>=.6
  ok=[p for p in good if stable(p)];x['frozen']=max(ok,key=lambda p:x['pairs'][p]['validation']['5']['expectancy']) if ok else None
  lead=x['leading'];x['buy_sell']=sub(raw[lead][1],'direction');x['sessions']=sub(raw[lead][1],'session') if tf in ('M5','M15','M30') else {}
  if x['frozen']:
   p=x['frozen'];plans={z:plan(raw[p][1],z) for z in ('structural','atr_capped_structural')}
   for z,v in plans.items():
    for R in (.5,.75,1,1.25,1.5):x['exits'][f'{z}_{R}R']=metrics(sim(b,v,w['validation'][1],R))
   best=max(x['exits'],key=lambda z:x['exits'][z]['expectancy'] or -1e9);rule,R=best.rsplit('_',1);R=float(R[:-1]);x['best_exit']=best
   for m in ('alone','confirmation','veto'):
    rr=raw[p][1] if m=='alone' else rec(b,q,tf,p,*w['validation'],m);x['tw'][m]={'entry':score(rr),'trade':metrics(sim(b,plan(rr,rule),w['validation'][1],R))}
   use=max(x['tw'],key=lambda z:x['tw'][z]['trade']['expectancy'] or -1e9);v=x['tw'][use]['trade']
   if v['trades']>=30 and (v['profit_factor'] or 0)>1.1 and (v['expectancy'] or 0)>0:winners.append((tf,p,rule,R,use,v))
  o['timeframes'][tf]=x
 if not winners:o['final']={'name':'NONE','metrics':metrics([]),'outliers':{}};o['decision']='**NO ROBUST XAUUSD REGIME STRATEGY FOUND.** No matched regime/concept pair jointly met positive development and validation entry expectancy, adequate count, stable validation subwindows, and executable PF >1.10. Holdouts remain untouched; Time Wheel has no measurable incremental evidence and is **INFORMATIONAL_ONLY**. Do not stack or portfolio failed pairs. Recommended XAU-only next step: obtain session/tick-quality data and independently pre-register one narrowly defined session-regime hypothesis before testing it.'
 else:
  tf,p,rule,R,wm,_=max(winners,key=lambda z:z[-1]['expectancy']);b=load(FILES[tf]);q=enrich(b);a,z=split(b)['holdout'];rr=rec(b,q,tf,p,a,z,'none' if wm=='alone' else wm);t=sim(b,plan(rr,rule),z,R);o['final']={'name':f'{tf} {p} {rule} {R}R {wm}','metrics':metrics(t),'outliers':outlier(t),'quarters':groups(t,'quarter')};o['decision']='Frozen regime candidate was evaluated once on untouched holdout.'
 write(o);print(json.dumps(o['final'],indent=2))
if __name__=='__main__':main()
