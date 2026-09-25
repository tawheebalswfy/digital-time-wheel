"""Offline XAUUSD-only V6 timeframe discovery; no MT5/order/production calls."""
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
from scripts.v5_concept_discovery import load,split,score,months,plan,sim,metrics,groups,outlier,iso,f,tbl,H,WARM,COST
FILES={x:ROOT/'data'/'history'/f'XAUUSD_{x}.csv' for x in ('M5','H4','D1')};CONCEPTS=('TREND_CONTINUATION','PULLBACK_CONTINUATION','BREAKOUT','MEAN_REVERSION','VOLATILITY_EXPANSION')
def enrich(b):
 q=features(b,Strategy());q['slope']=q.ema_slow-q.ema_slow.shift(3);q['atr_ratio']=q.atr/q.atr.shift(1).rolling(100,min_periods=30).median();q['atr_prev_ratio']=q.atr_ratio.shift(1)
 for n in (10,20,40):q[f'h{n}']=q.high.shift(1).rolling(n).max();q[f'l{n}']=q.low.shift(1).rolling(n).min()
 return q.to_dict('records')
def sg(r,tf,c):
 g=lambda k:finite(r[k]);p=float(r['close']);a=g('atr');adx=g('adx');rsi=finite(r['rsi'],50);ar=finite(r['atr_ratio'],1);d=1 if g('ema_fast')>g('ema_slow') and g('slope')>0 and g('plus_di')>g('minus_di') else -1 if g('ema_fast')<g('ema_slow') and g('slope')<0 and g('minus_di')>g('plus_di') else 0
 adx_t={'M5':15,'H4':25,'D1':20}[tf];n={'M5':10,'H4':20,'D1':40}[tf];pb={'M5':(45,55),'H4':(40,55),'D1':(35,50)}[tf]
 if c=='TREND_CONTINUATION':return d if d and adx>=adx_t and d*(p-g('ema_fast'))>0 and .7<=ar<=1.6 else 0
 if c=='PULLBACK_CONTINUATION':return d if d and adx>=adx_t and ((d==1 and pb[0]<=rsi<=pb[1] and p<=g('ema_fast')+.3*a) or(d==-1 and 100-pb[1]<=rsi<=100-pb[0] and p>=g('ema_fast')-.3*a)) else 0
 if c=='BREAKOUT':return 1 if adx>=adx_t and ar>=.9 and p>g(f'h{n}') else -1 if adx>=adx_t and ar>=.9 and p<g(f'l{n}') else 0
 if c=='MEAN_REVERSION':return -1 if adx<=15 and rsi>=65 and p-g('ema_slow')>=a else 1 if adx<=15 and rsi<=35 and g('ema_slow')-p>=a else 0
 if c=='VOLATILITY_EXPANSION':return 1 if ar>=1.1 and finite(r['atr_prev_ratio'],1)<=.85 and p>g(f'h{n}') else -1 if ar>=1.1 and finite(r['atr_prev_ratio'],1)<=.85 and p<g(f'l{n}') else 0
 return 0
def rec(b,q,tf,c,a,z,wheel='none'):
 s=TIMEFRAMES[tf];out=[];cfg=Strategy()
 for i in range(max(WARM,a),z-max(H)-1):
  # Daily bars legitimately skip weekends/market holidays; use the next actual
  # tradable bar while rejecting larger missing-history discontinuities.
  max_gap=4*86400 if tf=='D1' else s
  if any((b[j]['time']-b[j-1]['time'])>max_gap or (tf!='D1' and b[j]['time']!=b[j-1]['time']+s) for j in range(i+1,i+max(H)+1)):continue
  d=sg(q[i],tf,c)
  if not d:continue
  wd=int(wheel_state(float(q[i]['close']),b[i]['time']+s,cfg)['numerical_direction']) if wheel!='none' else 0
  if wheel=='confirmation' and wd!=d:continue
  if wheel=='veto' and wd==-d:continue
  e=b[i+1]['open'];x={'i':i,'time':b[i+1]['time'],'date':iso(b[i+1]['time'])[:10],'d':d,'entry':e,'atr':finite(q[i]['atr']),'row':q[i]}
  for h in H:
   path=b[i+1:i+h+1];x[f'r{h}']=d*(b[i+h]['close']-e);x[f'mfe{h}']=max((v['high']-e) if d==1 else(e-v['low']) for v in path);x[f'mae{h}']=max((e-v['low']) if d==1 else(v['high']-e) for v in path)
  out.append(x)
 return out
def quality(b,s):
 t=[x['time'] for x in b];bad=sum(not(all(math.isfinite(float(x[k])) and float(x[k])>0 for k in ('open','high','low','close')) and float(x['low'])<=min(float(x['open']),float(x['close'])) and float(x['high'])>=max(float(x['open']),float(x['close']))) for x in b);g=[v-u for u,v in zip(t,t[1:]) if v-u>s]
 return {'first_utc':iso(t[0]),'last_utc':iso(t[-1]),'candles':len(b),'duplicates':len(t)-len(set(t)),'invalid_ohlc':bad,'gaps':len(g),'source':'DIRECT_MT5'}
def classify(x):
 r=x['row'];adx=finite(r['adx']);ar=finite(r['atr_ratio'],1);return ('strong_trend' if adx>=25 else 'weak_trend', 'low_vol' if ar<.8 else 'high_vol' if ar>1.2 else 'normal_vol')
def subset(x,key):
 d=defaultdict(list)
 for v in x:
  if key=='direction':k='BUY' if v['d']==1 else 'SELL'
  elif key=='session':
   h=datetime.fromtimestamp(v['time'],timezone.utc).hour;k='Asia' if h<7 else 'London' if h<13 else 'Overlap' if h<17 else 'New_York'
  else:k=classify(v)[0 if key=='trend' else 1]
  d[k].append(v)
 return {k:score(v)['5']|{'signals':len(v)} for k,v in sorted(d.items())}
def write(o):
 d=ROOT/'docs';p=['# V6 XAU Timeframe Discovery Protocol\n\nXAUUSD only. Offline direct-MT5 CSV research; no production or order APIs. Final holdouts are excluded from discovery. Five fixed coarse archetypes are independently tested per timeframe.\n\n',tbl(['TF','Source','First UTC','Last UTC','Candles','Duplicates','Invalid OHLC','Gaps'],[[tf,x['quality']['source'],x['quality']['first_utc'],x['quality']['last_utc'],x['quality']['candles'],x['quality']['duplicates'],x['quality']['invalid_ohlc'],x['quality']['gaps']] for tf,x in o['timeframes'].items()])]
 (d/'V6_XAU_TIMEFRAME_DISCOVERY_PROTOCOL.md').write_text(''.join(p),encoding='utf-8')
 for tf in ('M5','H4','D1'):
  x=o['timeframes'][tf];p=[f'# V6 {tf} Results\n\n',tbl(['Concept','Dev n','Dev 5b exp','Val n','Val 5b exp','Accuracy','MFE/MAE'],[[c,x['concepts'][c]['development']['signals'],f(x['concepts'][c]['development']['5']['expectancy']),x['concepts'][c]['validation']['signals'],f(x['concepts'][c]['validation']['5']['expectancy']),f(x['concepts'][c]['validation']['5']['accuracy']),f(x['concepts'][c]['validation']['5']['mfe_mae_ratio'])] for c in CONCEPTS]),f'\n\nLeading raw validation concept: `{x["leading"]}`; frozen: `{x["frozen"]}`.\n\n']
  for title,key in [('BUY / SELL','direction'),('Trend regime','trend'),('Volatility regime','vol')]:p+=[f'## {title}\n\n',tbl(['Group','Signals','5b exp','Accuracy','MFE/MAE'],[[k,v['signals'],f(v['expectancy']),f(v['accuracy']),f(v['mfe_mae_ratio'])] for k,v in x['analysis'].get(key,{}).items()]),'\n\n']
  if tf=='M5':p+=['## UTC session analysis\n\n',tbl(['Session','Signals','5b exp','Accuracy','MFE/MAE'],[[k,v['signals'],f(v['expectancy']),f(v['accuracy']),f(v['mfe_mae_ratio'])] for k,v in x['analysis'].get('session',{}).items()]),'\n']
  (d/f'V6_{tf}_RESULTS.md').write_text(''.join(p),encoding='utf-8')
 (d/'V6_XAU_FINAL_DECISION.md').write_text('# V6 XAU Final Decision\n\n'+o['decision']+'\n',encoding='utf-8')
def main():
 o={'research_id':'DIGITAL_TIME_WHEEL_V6_XAU_TIMEFRAME_DISCOVERY','read_only':True,'timeframes':{}};winners=[]
 for tf,path in FILES.items():
  b=load(path);q=enrich(b);w=split(b);x={'quality':quality(b,TIMEFRAMES[tf]),'concepts':{},'analysis':{},'frozen':None,'tw':{},'exits':{}}
  raw={}
  for c in CONCEPTS:
   dev=rec(b,q,tf,c,*w['development']);val=rec(b,q,tf,c,*w['validation']);raw[c]=(dev,val);x['concepts'][c]={'development':score(dev),'validation':score(val),'months':months(val)}
  good=[c for c in CONCEPTS if x['concepts'][c]['development']['signals']>=50 and (x['concepts'][c]['development']['5']['expectancy'] or 0)>0 and x['concepts'][c]['validation']['signals']>=50 and (x['concepts'][c]['validation']['5']['expectancy'] or 0)>0]
  x['leading']=max(good,key=lambda c:x['concepts'][c]['validation']['5']['expectancy']) if good else max(CONCEPTS,key=lambda c:(x['concepts'][c]['validation']['5']['expectancy'] or -1e9))
  def stable(c):
   m=[v for v in x['concepts'][c]['months'].values() if v['signals']>=30];return len(m)>=3 and sum((v['5']['expectancy'] or 0)>0 for v in m)/len(m)>=.6
  ok=[c for c in good if stable(c)];x['frozen']=max(ok,key=lambda c:x['concepts'][c]['validation']['5']['expectancy']) if ok else None
  lead=x['leading'];x['analysis']={'direction':subset(raw[lead][1],'direction'),'trend':subset(raw[lead][1],'trend'),'vol':subset(raw[lead][1],'vol')}
  if tf=='M5':x['analysis']['session']=subset(raw[lead][1],'session')
  if x['frozen']:
   c=x['frozen'];ps={z:plan(raw[c][1],z) for z in ('structural','atr_capped_structural')}
   for z,v in ps.items():
    for R in (.5,.75,1,1.25,1.5):x['exits'][f'{z}_{R}R']=metrics(sim(b,v,w['validation'][1],R))
   best=max(x['exits'],key=lambda z:x['exits'][z]['expectancy'] or -1e9);rule,R=best.rsplit('_',1);R=float(R[:-1]);x['best_exit']=best
   for m in ('alone','confirmation','veto'):
    z=raw[c][1] if m=='alone' else rec(b,q,tf,c,*w['validation'],m);x['tw'][m]={'entry':score(z),'trade':metrics(sim(b,plan(z,rule),w['validation'][1],R))}
   chosen=max(x['tw'],key=lambda z:x['tw'][z]['trade']['expectancy'] or -1e9);v=x['tw'][chosen]['trade']
   if v['trades']>=30 and (v['profit_factor'] or 0)>1.1 and (v['expectancy'] or 0)>0:winners.append((tf,c,rule,R,chosen,v))
  o['timeframes'][tf]=x
 if not winners:o['final']={'name':'NONE','metrics':metrics([]),'outliers':{}};o['decision']='**NO ROBUST XAUUSD TIMEFRAME CONCEPT FOUND.** M5, H4, and D1 produced no concept meeting positive development/validation expectancy, adequate sample size, stable validation subwindows, and executable PF/expectancy gates. Holdouts were intentionally not opened. Time Wheel remains informational. Do not parameter-sweep further; collect tick/session-quality M5 data or reconsider the strategy premise/instrument.'
 else:
  tf,c,rule,R,wm,_=max(winners,key=lambda z:z[-1]['expectancy']);b=load(FILES[tf]);q=enrich(b);a,z=split(b)['holdout'];rr=rec(b,q,tf,c,a,z,'none' if wm=='alone' else wm);t=sim(b,plan(rr,rule),z,R);o['final']={'name':f'{tf} {c} {rule} {R}R {wm}','metrics':metrics(t),'outliers':outlier(t),'quarters':groups(t,'quarter')};o['decision']='A frozen candidate was evaluated once on its untouched holdout; see audit metrics.'
 (ROOT/'docs'/'V6_XAU_TIMEFRAME_DISCOVERY_RESULTS.json').write_text(json.dumps(o,indent=2,allow_nan=False),encoding='utf-8');write(o);print(json.dumps(o['final'],indent=2))
if __name__=='__main__':main()
