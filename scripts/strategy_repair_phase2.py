"""Read-only phase-2 diagnostics on retained genuine MT5 XAUUSD M1 history.

Production settings and SQLite data are never written.  The final historical
segment is reported as retrospective OOS because it predates this script.
"""
import json, sqlite3, sys
from pathlib import Path
from copy import deepcopy

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.config import Strategy, TIMEFRAMES
from backend.app import backtest
from backend.app.data import validate_bars

DB=ROOT/'runtime'/'timewheel.sqlite3'
BOUNDS={'validation':(18102,24105),'holdout':(24136,30170)}

def bars():
 c=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)
 did=c.execute("select id from datasets where payload like '%\"symbol\":\"XAUUSD\"%' and payload like '%\"timeframe\":\"M1\"%' limit 1").fetchone()[0]
 x=[json.loads(r[0]) for r in c.execute('select payload from candles where dataset_id=? order by time',(did,))];c.close();return validate_bars(x,60)

def brief(r):
 m=r['metrics'];p=[x['pnl'] for x in r['trades']];w=[x for x in p if x>0];l=[x for x in p if x<0]
 return {k:m[k] for k in ('trades','win_rate','profit_factor','expectancy','net_pnl','max_drawdown','average_win','average_loss')}|{'payoff_ratio':(sum(w)/len(w))/-(sum(l)/len(l)) if w and l else None}

def run(b,c,kind='current',r=None,be=None):
 original=backtest.execute_trade
 def execute(bars,signal,index,end,cfg):
  s=deepcopy(signal)
  entry=bars[index+1]['open'];risk=abs(entry-s['invalidation']['price'])
  if kind=='r':s['targets']=[{'price':entry+s['direction_value']*r*risk}]
  if be is None:return original(bars,s,index,end,cfg)
  # Conservative BE: activation is observed at close of a qualifying bar and
  # only applies from the following bar; no intrabar ordering is assumed.
  t=original(bars,s,index,end,cfg)
  if not t:return None
  d=s['direction_value'];cost=cfg.spread+2*cfg.slippage+cfg.fee;stop=s['invalidation']['price'];last=min(end-1,index+cfg.max_hold_bars);active=False
  for j in range(index+1,last+1):
   bar=bars[j];adverse=bar['low'] if d==1 else bar['high'];fav=bar['high'] if d==1 else bar['low']
   hit_stop=adverse<=stop if d==1 else adverse>=stop;target=s['targets'][0]['price'];hit_tp=fav>=target if d==1 else fav<=target
   if hit_stop or hit_tp:
    px=(min(stop,bar['open']) if d==1 else max(stop,bar['open'])) if hit_stop else target
    t.update(exit=px,exit_time=bars[j]['time'],exit_index=j,pnl=d*(px-entry)-cost,reason='breakeven_stop' if active and hit_stop else ('stop_first' if hit_stop else 'target'));return t
   if active:stop=entry
   if fav>=entry+d*be*risk if d==1 else fav<=entry-d*be*risk:active=True
  return t
 backtest.execute_trade=execute
 try:return backtest.run_backtest(b,c,'M1',*BOUNDS['validation'] if False else (None,None),keep_signals=False)
 finally:backtest.execute_trade=original

def window(b,c,start,end,kind='current',r=None,be=None):
 original=backtest.execute_trade
 def ex(bs,s,i,e,cfg):
  x=deepcopy(s);entry=bs[i+1]['open'];risk=abs(entry-x['invalidation']['price'])
  if kind=='r':x['targets']=[{'price':entry+x['direction_value']*r*risk}]
  return original(bs,x,i,e,cfg)
 backtest.execute_trade=ex
 try:return backtest.run_backtest(b,c,'M1',start,end,False)
 finally:backtest.execute_trade=original

def main():
 b=bars();c=Strategy(symbol='XAUUSD',anchor_price=4400,spread=.3,slippage=.05,fee=0)
 out={'exit_r':{},'holding':{},'mfe_mae':{},'baseline_m1':{}}
 for seg,(a,z) in BOUNDS.items():
  base=backtest.run_backtest(b,c,'M1',a,z,False);out['baseline_m1'][seg]=brief(base)
  for r in [.5,.75,1,1.25,1.5]:out['exit_r'].setdefault(str(r),{})[seg]=brief(window(b,c,a,z,'r',r))
  for mins in [1,3,5,10,15,30]:out['holding'].setdefault(str(mins),{})[seg]=brief(backtest.run_backtest(b,c.model_copy(update={'max_hold_bars':mins}), 'M1',a,z,False))
  out['holding'].setdefault('no_time_limit',{})[seg]=brief(base)
  losses=[t for t in base['trades'] if t['pnl']<0]
  out['mfe_mae'][seg]={'losers':len(losses),'mean_mfe':sum(t['mfe'] for t in losses)/len(losses) if losses else None,'mean_mae':sum(t['mae'] for t in losses)/len(losses) if losses else None,
   'reached_025R':sum(t['mfe']>=.25*abs(t['entry']-t['stop']) for t in losses)/len(losses) if losses else None,
   'reached_05R':sum(t['mfe']>=.5*abs(t['entry']-t['stop']) for t in losses)/len(losses) if losses else None,
   'reached_10R':sum(t['mfe']>=abs(t['entry']-t['stop']) for t in losses)/len(losses) if losses else None}
 print(json.dumps(out,indent=2,allow_nan=False))
if __name__=='__main__':main()
