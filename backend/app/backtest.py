"""Next-open simulation, immutable forecasts, wall-clock evaluations and purged walk-forward."""
import math
import numpy as np
from datetime import datetime,timezone
from .config import Strategy,TIMEFRAMES
from .technical import features
from .signals import analyze
from .database import digest

HORIZONS=[300,900,1800,3600,14400,86400]

def forward_results(signal,bars,seconds):
    lookup={b['time']+seconds:b for b in bars};out=[]
    for horizon in HORIZONS:
        endpoint=signal['timestamp']+horizon;b=lookup.get(endpoint)
        out.append({'horizon_seconds':horizon,'endpoint':endpoint,'available':b is not None,'price':b['close'] if b else None,
                    'change':b['close']-signal['price'] if b else None,'directional_change':signal['direction_value']*(b['close']-signal['price']) if b and signal['direction_value'] else None})
    return out

def execute_trade(bars,signal,index,end,c):
    """One quote-price unit. Round-trip spread, two slippages and fee charged once."""
    if index+1>=end or not signal['targets'] or not signal['invalidation']:return None
    d=signal['direction_value'];entry=bars[index+1]['open'];stop=signal['invalidation']['price'];target=signal['targets'][0]['price']
    if d*(target-entry)<=0 or d*(entry-stop)<=0:return None # Gap already beyond proposed range: no entry.
    costs=c.spread+2*c.slippage+c.fee;mae=mfe=0.;path=[]
    last=min(end-1,index+c.max_hold_bars);reason='time_exit';exit_price=bars[last]['close'];exit_index=last
    for j in range(index+1,last+1):
        b=bars[j];adverse=b['low'] if d==1 else b['high'];favorable=b['high'] if d==1 else b['low']
        mae=max(mae,max(0,-d*(adverse-entry)));mfe=max(mfe,max(0,d*(favorable-entry)))
        hit_stop=adverse<=stop if d==1 else adverse>=stop
        hit_target=favorable>=target if d==1 else favorable<=target
        if hit_stop:
            exit_price=min(stop,b['open']) if d==1 else max(stop,b['open']);exit_index=j;reason='stop_first';path.append((j,d*(exit_price-entry)-costs));break
        if hit_target:
            exit_price=target;exit_index=j;reason='target';path.append((j,d*(exit_price-entry)-costs));break
        path.append((j,d*(b['close']-entry)-costs))
    pnl=d*(exit_price-entry)-costs
    return {'signal_timestamp':signal['timestamp'],'entry_time':bars[index+1]['time'],'exit_time':bars[exit_index]['time'],'entry':entry,'exit':exit_price,'target':target,'stop':stop,
            'direction':signal['direction'],'pnl':pnl,'costs':costs,'mae':mae,'mfe':mfe,'excursion_note':'Full-bar range; exit-bar intrabar excursion order is unknowable.',
            'reason':reason,'exit_index':exit_index,'path':path}

def metrics(trades,equity,times,initial):
    pnl=np.array([t['pnl'] for t in trades],dtype=float);wins=pnl[pnl>0];losses=pnl[pnl<0]
    eq=np.array([initial]+list(equity),dtype=float);peaks=np.maximum.accumulate(eq);dd=peaks-eq
    days={}
    for t,e in zip(times,equity):days[datetime.fromtimestamp(t,timezone.utc).date().isoformat()]=e
    daily=np.array([initial]+list(days.values()));returns=np.diff(daily)/daily[:-1] if len(daily)>1 and np.all(daily>0) else np.array([])
    sharpe=float(returns.mean()/returns.std(ddof=1)*math.sqrt(252)) if len(returns)>1 and returns.std(ddof=1)>0 else None
    downside=math.sqrt(float(np.mean(np.minimum(returns,0)**2))) if len(returns) else 0
    sortino=float(returns.mean()/downside*math.sqrt(252)) if len(returns)>1 and downside>0 else None
    return {'trades':len(trades),'wins':len(wins),'losses':len(losses),'breakeven':int(sum(pnl==0)), 'win_rate':float(len(wins)/len(pnl)) if len(pnl) else None,
            'profit_factor':float(wins.sum()/-losses.sum()) if len(losses) else None,'profit_factor_note':'Undefined if no gross losses; never silently reported as a finite profit factor.',
            'expectancy':float(pnl.mean()) if len(pnl) else None,'average_win':float(wins.mean()) if len(wins) else None,'average_loss':float(losses.mean()) if len(losses) else None,
            'net_pnl':float(pnl.sum()),'max_drawdown':float(dd.max()),'max_drawdown_percent':float(np.max(dd/np.maximum(peaks,1e-9))*100),
            'sharpe':sharpe,'sortino':sortino,'return_basis':'Daily UTC marked equity, one quote-price unit, 252-day annualization, zero risk-free rate; undefined for insufficient/degenerate samples.',
            'maximum_adverse_excursion':max([t['mae'] for t in trades],default=0),'maximum_favorable_excursion':max([t['mfe'] for t in trades],default=0),'daily_observations':len(returns),'bankrupt':bool(np.any(eq<=0))}

def run_backtest(bars,c:Strategy,timeframe='M1',start_index=None,end_index=None,keep_signals=True):
    warmup=max(60,c.ema_slow*3,c.sma_period,c.bb_period,2*c.swing_strength+2)
    start=max(warmup,start_index or warmup);end=min(len(bars),end_index or len(bars));seconds=TIMEFRAMES[timeframe]
    if end<=start+c.max_hold_bars+1:raise ValueError(f'Need more candles: warmup {warmup}, holding period {c.max_hold_bars}, requested range {end-start}')
    f=features(bars[:end],c);records=f.to_dict('records');trades=[];forecasts=[];next_free=start;equity=np.full(end-start,c.initial_equity,dtype=float);realized=0.;pending={};counts={'BUY':0,'SELL':0,'NEUTRAL':0};study=[]
    lookup={b['time']+seconds:b['close'] for b in bars[:end]}
    for i in range(start,end-1):
        if i in pending:realized+=pending[i]
        equity[i-start]=c.initial_equity+realized
        signal=analyze(records[i],c,bars[i]['time']+seconds);counts[signal['direction']]+=1
        if c.enable_369:
            root_condition=any(signal['wheel'][k] in [3,6,9] for k in ['price_root','time_root','angle_root']) or signal['wheel']['sector'] in [3,6,9]
            future=lookup.get(signal['timestamp']+3600)
            if future is not None:study.append((root_condition,(future-signal['price'])/signal['price']))
        if keep_signals:
            # Original forecast remains separate from future evaluations.
            original={k:v for k,v in signal.items() if k not in ['candidates']}
            horizons=[{'horizon_seconds':h,'endpoint':signal['timestamp']+h,'available':signal['timestamp']+h in lookup,
                       'price':lookup.get(signal['timestamp']+h),'directional_change':signal['direction_value']*(lookup[signal['timestamp']+h]-signal['price']) if signal['timestamp']+h in lookup and signal['direction_value'] else None} for h in HORIZONS]
            forecasts.append({'original':original,'original_hash':digest(original),'results':horizons})
        if i<next_free or not signal['direction_value']:continue
        # No overnight/weekend gap entry is substituted for the immediate next bar.
        if bars[i+1]['time']!=signal['timestamp']:continue
        trade=execute_trade(bars,signal,i,end,c)
        if trade:
            base=realized
            for j,value in trade['path']:equity[j-start]=c.initial_equity+base+value
            pending[trade['exit_index']+1]=trade['pnl'];next_free=trade['exit_index']+1
            trades.append(trade)
    # Rebuild the curve once from nonoverlapping trades; avoid flat-loop overwrites of open positions.
    equity[:]=c.initial_equity;realized=0.;cursor=start
    for trade in trades:
        entry_index=next(j for j in range(cursor,end) if bars[j]['time']==trade['entry_time'])
        equity[cursor-start:entry_index-start]=c.initial_equity+realized
        for j,value in trade.pop('path'):equity[j-start]=c.initial_equity+realized+value
        realized+=trade['pnl'];cursor=trade['exit_index']+1
    equity[cursor-start:]=c.initial_equity+realized
    times=[b['time']+seconds for b in bars[start:end]]
    stats=metrics(trades,equity,times,c.initial_equity);stats['total_signals']=sum(counts.values());stats['signal_counts']=counts
    def group(vals):
        a=np.array(vals,dtype=float)
        return {'n':len(a),'mean_return':float(a.mean()) if len(a) else None,'standard_error':float(a.std(ddof=1)/math.sqrt(len(a))) if len(a)>1 else None}
    study_result={'enabled':c.enable_369,'horizon_seconds':3600,'conditional':group([v for ok,v in study if ok]),'unconditional':group([v for _,v in study]),'complement':group([v for ok,v in study if not ok]),'caveat':'Overlapping horizons are dependent. Descriptive statistics, not an independent-sample significance test or proof of edge.'}
    yearly={}
    for t in trades:yearly.setdefault(str(datetime.fromtimestamp(t['exit_time'],timezone.utc).year),[]).append(t['pnl'])
    return {'strategy':c.model_dump(mode='json'),'strategy_hash':digest(c.model_dump(mode='json')),'timeframe':timeframe,'start':times[0],'end':times[-1],
            'metrics':stats,'yearly':{y:{'trades':len(v),'pnl':sum(v),'expectancy':sum(v)/len(v)} for y,v in yearly.items()},
            'trades':trades,'forecasts':forecasts,'equity':[{'time':t,'value':float(v)} for t,v in zip(times,equity)],'research_369':study_result,
            'assumptions':['Next-bar open; no overlapping positions','Fixed full spread + two slippages + per-trade fee in quote-price units','Stop first on ambiguous bars; adverse stop gap fill','Only target1 used for trade exit; all target rationales retained','No broker lot size, leverage, financing or currency conversion simulation']}

def objective(m):
    if m['trades']<5 or m['expectancy'] is None:return -1e12
    pf=m['profit_factor'] if m['profit_factor'] is not None else (1 if m['net_pnl']>0 else 0)
    return m['expectancy']*min(pf,3)/(1+m['max_drawdown'])

def walk_forward(bars,configs,timeframe,train_size,test_size):
    if not 1<=len(configs)<=12:raise ValueError('Compare 1–12 strategy configurations')
    purge=max(c.max_hold_bars for c in configs)+1
    if train_size<200 or test_size<purge+100:raise ValueError('Training >=200; test window >= holding period +101')
    folds=[];start=train_size
    while start+test_size<=len(bars):
        training=[]
        for c in configs:
            # Build feature warmup from earlier history, but evaluate only within train window.
            result=run_backtest(bars,c,timeframe,max(0,start-train_size),start-purge,False)
            yearly=list(result['yearly'].values());stability=sum(y['expectancy']>0 for y in yearly)/len(yearly) if yearly else 0
            training.append({'config':c,'metrics':result['metrics'],'objective':objective(result['metrics'])*stability if objective(result['metrics'])>0 else objective(result['metrics'])})
        best=max(training,key=lambda x:x['objective']);test=run_backtest(bars,best['config'],timeframe,start,start+test_size,True)
        ins=best['metrics'];oos=test['metrics'];warning=ins['expectancy'] is not None and ins['expectancy']>0 and (oos['expectancy'] is None or oos['expectancy']<=0 or oos['expectancy']<ins['expectancy']*.25)
        folds.append({'train_start':max(0,start-train_size),'train_end_exclusive':start-purge,'test_start':start,'test_end_exclusive':start+test_size,'purge_bars':purge,
                      'selected':best['config'].model_dump(mode='json'),'train_metrics':ins,'test':test,'warning':'POSSIBLE OVERFITTING' if warning else None,
                      'candidates':[{'strategy':x['config'].name,'objective':x['objective'],'metrics':x['metrics']} for x in training]})
        start+=test_size
    if not folds:raise ValueError('Insufficient bars for a complete train/test fold')
    return {'folds':folds,'selection':'Training-only expectancy/profit-factor/drawdown objective, penalized by positive-year fraction; all variants disclosed.',
            'unused_tail_bars':len(bars)-start,'assistant':research_summary(folds)}

def research_summary(folds):
    total=sum(f['test']['metrics']['trades'] for f in folds)
    if total<30:return f'Only {total} out-of-sample trades. Evidence is insufficient to claim an edge.'
    warnings=sum(bool(f['warning']) for f in folds);positive=sum(f['test']['metrics']['net_pnl']>0 for f in folds)
    if warnings:return f'POSSIBLE OVERFITTING: {warnings} of {len(folds)} folds deteriorated materially out of sample. Compare against baselines and independent data.'
    return f'{positive} of {len(folds)} test folds had positive net P&L across {total} trades. This descriptive result does not establish statistical significance.'
