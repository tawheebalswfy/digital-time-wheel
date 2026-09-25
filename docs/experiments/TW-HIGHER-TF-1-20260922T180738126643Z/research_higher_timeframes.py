"""TW-HIGHER-TF-1: frozen isolated attribution on retained M15/H1 data."""
import gzip,hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.config import Strategy,TIMEFRAMES
from backend.app.data import validate_bars
from backend.app.database import digest
from backend.app.technical import features
from backend.app import backtest
from research_ablation import checkpoint
from research_full_attribution import technical_entry,wheel_entry,technical_exit,wheel_exit,summarize,ARMS

PROTOCOL=ROOT/'docs'/'TIME_WHEEL_HIGHER_TIMEFRAME_PROTOCOL.md'
SPECS={'M15':('9b42086946a9ceab1a8fde7c889d931cf6fddbde30e24436272c988f49796612',{'train':(78,1176),'validation':(1207,1579),'test':(1610,2013)}),'H1':('aa9dd4bc95536d041bec47fbbec7e6b317a0f1db6309c84629cbac792470ef43',{'train':(78,270),'validation':(301,371),'test':(402,503)})}
H4=('4dda02867ad6c17b1956a685009b3ac86294c9e2c9af2778dab1560be582f03e',131)

def execute(bars,i,end,d,target,stop,c,seconds):
 entry=bars[i+1]['open'];cost=c.spread+2*c.slippage+c.fee
 if d*(target['price']-entry)<=0 or d*(entry-stop['price'])<=0:return None
 last=min(end-1,i+c.max_hold_bars);mae=mfe=0.;path=[];exit_price=bars[last]['close'];exit_index=last;reason='time_exit'
 for j in range(i+1,last+1):
  b=bars[j];adverse=b['low']if d==1 else b['high'];favorable=b['high']if d==1 else b['low'];mae=max(mae,max(0,-d*(adverse-entry)));mfe=max(mfe,max(0,d*(favorable-entry)))
  hs=adverse<=stop['price']if d==1 else adverse>=stop['price'];ht=favorable>=target['price']if d==1 else favorable<=target['price']
  if hs:exit_price=min(stop['price'],b['open'])if d==1 else max(stop['price'],b['open']);exit_index=j;reason='stop_first';path.append((j,d*(exit_price-entry)-cost));break
  if ht:exit_price=target['price'];exit_index=j;reason='target';path.append((j,d*(exit_price-entry)-cost));break
  path.append((j,d*(b['close']-entry)-cost))
 return {'signal_timestamp':bars[i]['time']+seconds,'entry_time':bars[i+1]['time'],'exit_time':bars[exit_index]['time'],'entry':entry,'exit':exit_price,'target':target,'stop':stop,'direction':'BUY'if d==1 else'SELL','pnl':d*(exit_price-entry)-cost,'costs':cost,'mae':mae,'mfe':mfe,'reason':reason,'exit_index':exit_index,'holding_minutes':(exit_index-i)*seconds/60,'path':path}

def run(bars,c,tf,start,end,ek,xk):
 sec=TIMEFRAMES[tf];rows=features(bars[:end],c).to_dict('records');trades=[];audit=[];next_free=start;equity=np.full(end-start,c.initial_equity);real=0.;counts={'BUY':0,'SELL':0,'NEUTRAL':0}
 for i in range(start,end-1):
  equity[i-start]=c.initial_equity+real;ts=bars[i]['time']+sec;d,components,scores=technical_entry(rows[i],c,ts)if ek=='T'else wheel_entry(rows[i],c,ts);counts['BUY'if d==1 else'SELL'if d==-1 else'NEUTRAL']+=1
  target,stop=technical_exit(rows[i],c,ts,d)if xk=='T'and d else wheel_exit(rows[i],c,ts,d)if d else(None,None);event={'timestamp':ts,'direction_value':d,'entry_family':ek,'exit_family':xk,'components':components,'scores':scores,'target':target,'stop':stop}
  if not d or not target or not stop:event['status']='no_signal_or_levels'
  elif i<next_free:event['status']='occupied'
  elif bars[i+1]['time']!=ts:event['status']='gap'
  else:
   t=execute(bars,i,end,d,target,stop,c,sec)
   if t:event['status']='entered';event['trade_index']=len(trades);trades.append(t);next_free=t['exit_index']+1
   else:event['status']='invalid_at_next_open'
  audit.append(event)
 equity[:]=c.initial_equity;real=0.;cursor=start
 for t in trades:
  for j,v in t['path']:equity[j-start]=c.initial_equity+real+v
  real+=t['pnl'];cursor=t['exit_index']+1
 if cursor<end:equity[cursor-start:]=c.initial_equity+real
 m=backtest.metrics(trades,equity,[b['time']+sec for b in bars[start:end]],c.initial_equity);m.update(total_signals=sum(counts.values()),signal_counts=counts)
 for t in trades:t.pop('path')
 return {'timeframe':tf,'strategy':c.model_dump(mode='json'),'metrics':m,'trades':trades,'equity':[{'time':b['time']+sec,'value':float(v)}for b,v in zip(bars[start:end],equity)],'audit':audit}

def gz(p,x):
 with gzip.open(p,'xt',encoding='utf8')as f:json.dump(x,f,allow_nan=False)
def delta(r,a,b):return{k:(r[a][k]-r[b][k]if isinstance(r[a][k],(int,float))and isinstance(r[b][k],(int,float))else None)for k in r[a]}
def main():
 out=ROOT/'docs'/'experiments'/('TW-HIGHER-TF-1-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True,exist_ok=False);src=checkpoint.fingerprints();conn=sqlite3.connect((ROOT/'runtime'/'timewheel.sqlite3').as_uri()+'?mode=ro',uri=True);conn.execute('PRAGMA query_only=ON');db=checkpoint.logical_state(conn);saved=json.loads(conn.execute('SELECT payload FROM backtests LIMIT 1').fetchone()[0]);c=Strategy(**saved['test']['strategy']);all_results={};registration={'experiment':'TW-HIGHER-TF-1','protocol_sha256':hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),'dataset_specs':SPECS,'h4':{'dataset_id':H4[0],'bars':H4[1],'status':'insufficient: warmup 78 equals 60% boundary; purge makes training end 47'},'source_before':src,'database_before':db,'parameter_search':False,'created_utc':datetime.now(timezone.utc).isoformat()};(out/'registration.json').write_text(json.dumps(registration,indent=2),encoding='utf8');(out/PROTOCOL.name).write_bytes(PROTOCOL.read_bytes());(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
 for tf,(did,bounds)in SPECS.items():
  meta=json.loads(conn.execute('SELECT payload FROM datasets WHERE id=?',(did,)).fetchone()[0]);bars=[json.loads(z[0])for z in conn.execute('SELECT payload FROM candles WHERE dataset_id=? ORDER BY time',(did,))];validate_bars(bars,TIMEFRAMES[tf]);assert digest(bars)==meta['content_hash'];all_results[tf]={'metadata':meta,'bounds':bounds,'segments':{}}
  for seg,(start,end)in bounds.items():
   s={}
   for arm,e,x in [('A','T','T'),('B','W','W'),('C','T','W'),('D','W','T')]:print('Running',tf,seg,arm,flush=True);v=run(bars,c,tf,start,end,e,x);gz(out/f'{tf}-{seg}-{arm}.json.gz',v);s[arm]=summarize(v)
   v=backtest.run_backtest(bars,c,tf,start,end,False);gz(out/f'{tf}-{seg}-E.json.gz',v);s['E']=summarize(v);all_results[tf]['segments'][seg]=s
  r=all_results[tf]['segments']['test'];all_results[tf]['test_attribution']={'wheel_entry_technical_exit_D_minus_A':delta(r,'D','A'),'wheel_entry_wheel_exit_B_minus_C':delta(r,'B','C'),'wheel_exit_technical_entry_C_minus_A':delta(r,'C','A'),'wheel_exit_wheel_entry_B_minus_D':delta(r,'B','D')}
 assert checkpoint.fingerprints()==src and checkpoint.logical_state(conn)==db;conn.close();outcome={'registration':registration,'results':all_results,'preserved':True,'conclusion_scope':'test only; H4 insufficient'};(out/'comparison.json').write_text(json.dumps(outcome,indent=2,allow_nan=False),encoding='utf8');print(json.dumps({'output':str(out),'test':{k:v['segments']['test']for k,v in all_results.items()},'attribution':{k:v['test_attribution']for k,v in all_results.items()}},indent=2),flush=True)
if __name__=='__main__':main()
