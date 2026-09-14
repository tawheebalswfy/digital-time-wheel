"""TW-FULL-EXIT-1. Research-only fully separated entry/exit attribution."""
from collections import defaultdict
from datetime import datetime, timezone
import gzip, hashlib, json, sqlite3, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.config import Strategy
from backend.app.data import validate_bars
from backend.app.database import canonical,digest
from backend.app.technical import features,fibonacci,finite
from backend.app.wheel import state,wheel_levels,raw_price_angle,inverse_raw
from backend.app import backtest
from research_ablation import checkpoint

RUN_ID='41ba0ea5-4b9d-4c09-8c2d-7947da46385b'
PROTOCOL=ROOT/'docs'/'TIME_WHEEL_FULL_ATTRIBUTION_PROTOCOL.md'
ARMS={'A':'Technical entry + technical exit','B':'Wheel entry + wheel exit','C':'Technical entry + wheel exit','D':'Wheel entry + technical exit','E':'Current production baseline'}
BOUNDS={'train':(78,18071),'validation':(18102,24105),'test':(24136,30170)}

def direction(v):return 1 if v>0 else -1 if v<0 else 0

def technical_entry(row,c,ts):
    p=float(row['close']);structure={'BULLISH':1,'BEARISH':-1}.get(row.get('structure'),0)
    votes=[]
    if 'EMA'in c.indicators:votes.append(direction(finite(row.get('ema_fast'))-finite(row.get('ema_slow'))))
    if 'SMA'in c.indicators:votes.append(direction(p-finite(row.get('sma'),p)))
    if 'RSI'in c.indicators:
        r=finite(row.get('rsi'),50);votes.append(1 if r>55 else -1 if r<45 else 0)
    if 'MACD'in c.indicators:votes.append(direction(finite(row.get('macd_hist'))))
    if 'ADX'in c.indicators and finite(row.get('adx'))>20:votes.append(direction(finite(row.get('plus_di'))-finite(row.get('minus_di'))))
    if 'BB'in c.indicators:votes.append(direction(p-finite(row.get('bb_mid'),p)))
    momentum=direction(sum(votes));atr=finite(row.get('atr'));support,resistance=finite(row.get('support')),finite(row.get('resistance'))
    sr=1 if support and p>support and p-support<atr*.5 else -1 if resistance and p<resistance and resistance-p<atr*.5 else 0
    fib_vote=structure if any(abs(p-x['price'])<atr*.3 for x in fibonacci(row,c,ts)) else 0
    components={'structure':structure,'support_resistance':sr,'momentum':momentum,'fibonacci':fib_vote};total=sum(c.weights[k] for k in components)
    scores={name:100*sum(c.weights[k] for k,v in components.items() if v==sign)/total for name,sign in [('buy',1),('sell',-1),('neutral',0)]}
    d=1 if scores['buy']>scores['sell'] else -1 if scores['sell']>scores['buy'] else 0
    return d if max(scores['buy'],scores['sell'])>=c.threshold else 0,components,scores

def wheel_entry(row,c,ts):
    w=state(float(row['close']),ts,c);d=w['numerical_direction'];components={'wheel':d,'geometry':d,'gates':d if w['gates'] else 0};total=sum(c.weights[k] for k in components)
    scores={name:100*sum(c.weights[k] for k,v in components.items() if v==sign)/total for name,sign in [('buy',1),('sell',-1),('neutral',0)]}
    final=1 if scores['buy']>scores['sell'] else -1 if scores['sell']>scores['buy'] else 0
    return final if final==d and max(scores['buy'],scores['sell'])>=c.threshold else 0,components,scores

def clustered(items,p,d):
    valid=[x for x in items if x['price']>0 and d*(x['price']-p)>.01]
    return min(valid,key=lambda x:(abs(x['price']-p),x['price'])) if valid else None

def technical_exit(row,c,ts,d):
    p=float(row['close']);items=[]
    for name in ['support','resistance','swing_high','swing_low']:
        x=finite(row.get(name),None)
        if x is not None:items.append({'price':round(x,6),'source':name,'formula':'previously confirmed '+name})
    items += [{'price':round(x['price'],6),'source':'fibonacci','formula':x['formula'],'ratio':x['ratio']} for x in fibonacci(row,c,ts)]
    return clustered(items,p,d),clustered(items,p,-d)

def wheel_exit(row,c,ts,d):
    p=float(row['close']);items=[]
    for x in wheel_levels(p,c,2):items.append({'price':round(x['price'],6),'source':'wheel','formula':x['formula'],'angle':x['angle']})
    raw=raw_price_angle(p,c)
    for angle in sorted(set(c.harmonics)):
        if angle:
            for sign in [-1,1]:
                x=inverse_raw(raw+sign*angle,c)
                if x is not None:items.append({'price':round(x,6),'source':'angular','formula':f'inverse_{c.price_mapping}({raw}+{sign}*{angle})','angle':sign*angle})
    return clustered(items,p,d),clustered(items,p,-d)

def execute(bars,i,end,d,target,stop,c):
    entry=bars[i+1]['open'];cost=c.spread+2*c.slippage+c.fee
    if d*(target['price']-entry)<=0 or d*(entry-stop['price'])<=0:return None
    last=min(end-1,i+c.max_hold_bars);mae=mfe=0.;path=[];exit_price=bars[last]['close'];exit_index=last;reason='time_exit'
    for j in range(i+1,last+1):
        b=bars[j];adverse=b['low'] if d==1 else b['high'];favorable=b['high'] if d==1 else b['low'];mae=max(mae,max(0,-d*(adverse-entry)));mfe=max(mfe,max(0,d*(favorable-entry)))
        hit_stop=adverse<=stop['price'] if d==1 else adverse>=stop['price'];hit_target=favorable>=target['price'] if d==1 else favorable<=target['price']
        if hit_stop:exit_price=min(stop['price'],b['open']) if d==1 else max(stop['price'],b['open']);exit_index=j;reason='stop_first';path.append((j,d*(exit_price-entry)-cost));break
        if hit_target:exit_price=target['price'];exit_index=j;reason='target';path.append((j,d*(exit_price-entry)-cost));break
        path.append((j,d*(b['close']-entry)-cost))
    return {'signal_timestamp':bars[i]['time']+60,'entry_time':bars[i+1]['time'],'exit_time':bars[exit_index]['time'],'entry':entry,'exit':exit_price,'target':target,'stop':stop,'direction':'BUY' if d==1 else 'SELL','pnl':d*(exit_price-entry)-cost,'costs':cost,'mae':mae,'mfe':mfe,'reason':reason,'exit_index':exit_index,'path':path,'holding_minutes':(exit_index-i)}

def run_variant(bars,c,start,end,entry_kind,exit_kind):
    records=features(bars[:end],c).to_dict('records');trades=[];audit=[];next_free=start;eq=np.full(end-start,c.initial_equity);real=0.;counts={'BUY':0,'SELL':0,'NEUTRAL':0};rejected=0
    for i in range(start,end-1):
        eq[i-start]=c.initial_equity+real
        d,components,scores=technical_entry(records[i],c,bars[i]['time']+60) if entry_kind=='T' else wheel_entry(records[i],c,bars[i]['time']+60)
        counts['BUY'if d==1 else'SELL'if d==-1 else'NEUTRAL']+=1
        target,stop=technical_exit(records[i],c,bars[i]['time']+60,d) if exit_kind=='T' and d else wheel_exit(records[i],c,bars[i]['time']+60,d) if d else (None,None)
        event={'timestamp':bars[i]['time']+60,'direction_value':d,'entry_family':entry_kind,'exit_family':exit_kind,'components':components,'scores':scores,'target':target,'stop':stop}
        if not d or not target or not stop:event['status']='no_signal_or_levels'
        elif i<next_free:event['status']='occupied'
        elif bars[i+1]['time']!=event['timestamp']:event['status']='gap'
        else:
            trade=execute(bars,i,end,d,target,stop,c)
            if trade:
                event['status']='entered';event['trade_index']=len(trades);trades.append(trade);next_free=trade['exit_index']+1
            else:event['status']='invalid_at_next_open';rejected+=1
        audit.append(event)
    eq[:]=c.initial_equity;real=0.;cursor=start
    for t in trades:
        for j,v in t['path']:eq[j-start]=c.initial_equity+real+v
        real+=t['pnl'];cursor=t['exit_index']+1
    if cursor<end:eq[cursor-start:]=c.initial_equity+real
    stats=backtest.metrics(trades,eq,[b['time']+60 for b in bars[start:end]],c.initial_equity);stats.update(total_signals=sum(counts.values()),signal_counts=counts,rejected_at_next_open=rejected)
    for t in trades:t.pop('path')
    return {'strategy':c.model_dump(mode='json'),'start':bars[start]['time']+60,'end':bars[end-1]['time']+60,'metrics':stats,'trades':trades,'equity':[{'time':b['time']+60,'value':float(x)} for b,x in zip(bars[start:end],eq)],'audit':audit,'assumptions':['Frozen TW-FULL-EXIT-1 independent entry/exit families','Next-bar open; no overlapping positions','Fixed 0.40 round-trip cost; stop first; adverse stop gap; 30-bar max hold']}

def summarize(r):
    m=r['metrics'];t=r['trades'];gross=[x['pnl']+x['costs']for x in t]
    return {'trades':m['trades'],'win_rate':m['win_rate'],'average_winner':m['average_win'],'average_loser':m['average_loss'],'profit_factor':m['profit_factor'],'gross_expectancy':float(np.mean(gross))if gross else None,'net_expectancy':m['expectancy'],'net_pnl':m['net_pnl'],'max_drawdown':m['max_drawdown'],'mean_mae':float(np.mean([x['mae']for x in t]))if t else None,'max_mae':m['maximum_adverse_excursion'],'mean_mfe':float(np.mean([x['mfe']for x in t]))if t else None,'max_mfe':m['maximum_favorable_excursion'],'average_holding_minutes':float(np.mean([x['holding_minutes']for x in t]))if t else None,'raw_sharpe':m['sharpe'],'raw_sortino':m['sortino'],'daily_observations':m['daily_observations']}

def save(path,obj):
    with gzip.open(path,'xt',encoding='utf-8')as f:json.dump(obj,f,allow_nan=False)

def full_filter(bars,c,start,end):
    records=features(bars[:end],c).to_dict('records');rows=[]
    for i in range(start,end-1):
        d,_,_=technical_entry(records[i],c,bars[i]['time']+60)
        if not d or bars[i+1]['time']!=bars[i]['time']+60:continue
        target,stop=technical_exit(records[i],c,bars[i]['time']+60,d)
        t=execute(bars,i,end,d,target,stop,c) if target and stop else None
        if not t:continue
        w,_,_=wheel_entry(records[i],c,bars[i]['time']+60)
        # Existing combined requires the baseline analysis; import lazily to preserve fixed research decision.
        from backend.app.signals import analyze
        combined=analyze(records[i],c,bars[i]['time']+60)['direction_value']
        rows.append({'timestamp':bars[i]['time']+60,'technical_direction':d,'combined_accepts_same_direction':combined==d,'counterfactual_pnl':t['pnl'],'counterfactual_gross_pnl':t['pnl']+t['costs'],'wheel_only_direction':w})
    groups={}
    for key in [True,False]:
        x=[r for r in rows if r['combined_accepts_same_direction']==key];p=[r['counterfactual_pnl']for r in x]
        groups['accepted_same_direction'if key else'filtered_by_combined']={'opportunities':len(x),'net_expectancy':float(np.mean(p))if p else None,'net_pnl':float(sum(p)),'profitable':sum(v>0 for v in p),'losing_or_flat':sum(v<=0 for v in p)}
    return {'rows':rows,'summary':groups,'scope':'Technical-entry technical-exit counterfactuals independently evaluated; positions may overlap.'}

def main():
    out=ROOT/'docs'/'experiments'/('TW-FULL-EXIT-1-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True,exist_ok=False)
    base_fingerprints=checkpoint.fingerprints();conn=sqlite3.connect((ROOT/'runtime'/'timewheel.sqlite3').as_uri()+'?mode=ro',uri=True);conn.execute('PRAGMA query_only=ON');db_before=checkpoint.logical_state(conn)
    saved=json.loads(conn.execute('SELECT payload FROM backtests WHERE id=?',(RUN_ID,)).fetchone()[0]);meta=json.loads(conn.execute('SELECT payload FROM datasets WHERE id=?',(saved['dataset_id'],)).fetchone()[0]);bars=[json.loads(x[0])for x in conn.execute('SELECT payload FROM candles WHERE dataset_id=? ORDER BY time',(saved['dataset_id'],))];validate_bars(bars,60);assert digest(bars)==meta['content_hash'] and saved['split_index']==24136
    c=Strategy(**saved['test']['strategy']);registration={'experiment':'TW-FULL-EXIT-1','created_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'dataset':meta,'dataset_id':saved['dataset_id'],'strategy_hash':digest(c.model_dump(mode='json')),'arms':ARMS,'bounds':BOUNDS,'cost':.4,'source_before':base_fingerprints,'database_before':db_before,'parameter_search':False,'timeframe_scope':'M1 only'}
    (out/'registration.json').write_text(json.dumps(registration,indent=2),encoding='utf-8');(out/PROTOCOL.name).write_bytes(PROTOCOL.read_bytes());(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    results={};filters={}
    for segment,(start,end)in BOUNDS.items():
        results[segment]={}
        for arm,e,x in [('A','T','T'),('B','W','W'),('C','T','W'),('D','W','T')]:
            print('Running',segment,arm,flush=True);r=run_variant(bars,c,start,end,e,x);save(out/f'{segment}-{arm}.json.gz',r);results[segment][arm]=summarize(r)
        prod=backtest.run_backtest(bars,c,'M1',start,end,False);results[segment]['E']=summarize(prod);save(out/f'{segment}-E.json.gz',prod)
        filters[segment]=full_filter(bars,c,start,end);save(out/f'{segment}-filter.json.gz',filters[segment])
    assert checkpoint.fingerprints()==base_fingerprints and checkpoint.logical_state(conn)==db_before;conn.close()
    def delta(a,b):return{k:(results['test'][a][k]-results['test'][b][k]if isinstance(results['test'][a][k],(int,float))and isinstance(results['test'][b][k],(int,float))else None)for k in results['test'][a]}
    output={'registration':registration,'summaries':results,'filters':filters,'test_attribution':{'wheel_entry_with_technical_exits_D_minus_A':delta('D','A'),'wheel_entry_with_wheel_exits_B_minus_C':delta('B','C'),'wheel_exit_with_technical_entries_C_minus_A':delta('C','A'),'wheel_exit_with_wheel_entries_B_minus_D':delta('B','D')},'preserved':True,'final_conclusion_scope':'Final test only; M1 only; retrospective OOS not untouched independent.'}
    (out/'comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False),encoding='utf-8');print(json.dumps({'output':str(out),'test':results['test'],'attribution':output['test_attribution'],'filters':filters['test']['summary']},indent=2),flush=True)
if __name__=='__main__':main()
