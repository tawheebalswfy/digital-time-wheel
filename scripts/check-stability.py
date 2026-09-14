"""Read-only live integration check. Does not initialize or reconnect MT5."""
import argparse,asyncio,json,time
from pathlib import Path
import httpx,websockets

async def check(seconds):
    base='http://127.0.0.1:8000';started=time.time();samples=[];errors=[]
    async with httpx.AsyncClient(timeout=15) as client:
        before=(await client.get(base+'/api/health')).json()
        async with websockets.connect(base.replace('http','ws')+'/ws?timeframe=M1&client_id=stability-probe',origin='http://127.0.0.1:5173') as ws:
            while time.time()-started<seconds:
                s=json.loads(await asyncio.wait_for(ws.recv(),timeout=15));tick=s.get('tick') or {}
                h=(await client.get(base+'/api/health'));h.raise_for_status();h=h.json()
                sample={'received_at_utc_epoch':time.time(),'pid':h['pid'],'connections':h['connections'],
                        'initialize_calls':h['mt5']['initialize_calls'],'shutdown_calls':h['mt5']['shutdown_calls'],
                        'poll_count':s['connection_diagnostics']['poll_count'],'tick_calls':h['mt5']['tick_calls'],
                        'bid':tick.get('bid'),'ask':tick.get('ask'),'broker_epoch':tick.get('raw_time'),
                        'normalized_utc_epoch':tick.get('time'),'age_seconds':s.get('tick_age_seconds'),
                        'stale':s.get('stale'),'error':s.get('error'),'candle_count':len(s.get('candles',[])),
                        'price_angle':(s.get('wheel') or {}).get('price_angle')}
                samples.append(sample)
                if s.get('error') or s.get('stale'):errors.append(sample)
        await asyncio.sleep(.25)
        after=(await client.get(base+'/api/health')).json()
    summary={'duration_seconds':round(time.time()-started,2),'messages':len(samples),'REST_checks':len(samples)+2,
             'same_backend_pid':before['pid']==after['pid'],'initializations_during_test':after['mt5']['initialize_calls']-before['mt5']['initialize_calls'],
             'shutdowns_during_test':after['mt5']['shutdown_calls']-before['mt5']['shutdown_calls'],
             'distinct_prices':len({(s['bid'],s['ask']) for s in samples}),
             'distinct_tick_timestamps':len({s['normalized_utc_epoch'] for s in samples}),
             'all_bid_ask_valid':all(s['bid'] and s['ask']>=s['bid']>0 for s in samples),
             'max_tick_age_seconds':max(s['age_seconds'] for s in samples if s['age_seconds'] is not None),
             'stale_or_error_samples':len(errors),'history_available':any(s['candle_count'] for s in samples),
             'before':before,'after':after}
    out=Path(__file__).resolve().parents[1]/'docs'/'CONNECTION_STABILITY.json'
    out.write_text(json.dumps({'summary':summary,'samples':samples},indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
    assert summary['same_backend_pid'] and summary['all_bid_ask_valid'] and not errors
    assert summary['initializations_during_test']==summary['shutdowns_during_test']==0
    assert summary['distinct_tick_timestamps']>1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=180)
    asyncio.run(check(parser.parse_args().seconds))
