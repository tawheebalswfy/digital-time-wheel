import os,tempfile,unittest,json,math,sqlite3
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import Mock
from backend.app.config import Strategy,TIMEFRAMES
from backend.app.wheel import digital_root,time_angle,time_root,price_angle,angular_distance,safe_formula,inverse_raw,raw_price_angle,state
from backend.app.data import parse_csv,resample,MT5Adapter,FeedError
from backend.app.technical import features
from backend.app.signals import analyze,targets
from backend.app.database import Database,digest
from backend.app.backtest import run_backtest,execute_trade,forward_results,walk_forward

def fixture(n=700):
    """Deterministic constructed OHLC, not genuine market data and never shipped as live prices."""
    start=1704067200;result=[];prev=2000.
    for i in range(n):
        close=2000+math.sin(i/11)*8+math.sin(i/37)*15+i*.004
        result.append({'time':start+i*60,'open':prev,'high':max(prev,close)+.8,'low':min(prev,close)-.8,'close':close,'tick_volume':100.})
        prev=close
    return result

class Mathematics(unittest.TestCase):
    def test_roots(self):
        for n,r in [(270,9),(258,6),(4454,8),(0,0),(-4454,8)]:self.assertEqual(digital_root(n),r)
        self.assertEqual(digital_root(4454.99,2),8)
        self.assertEqual(digital_root(218.0625),2)
        self.assertEqual(digital_root(218.0625,2),8)
        with self.assertRaises(ValueError):digital_root(float('nan'))
    def test_angles(self):
        c=Strategy();dt=datetime(2026,1,1,14,32,15,tzinfo=timezone.utc)
        self.assertAlmostEqual(time_angle(dt,c),218.0625)
        self.assertEqual(angular_distance(359,1),2)
        for cycle in [86400,43200,21600,10800,3600,1800,900,300,60]:self.assertTrue(0<=time_angle(dt,c,cycle)<360)
    def test_video_modes(self):
        for minute,angle,root24,root12 in [(42,252,1,7),(43,258,2,8),(45,270,4,1),(47,282,6,3)]:
            dt=datetime(2026,8,30,22,minute,8,tzinfo=timezone.utc)
            self.assertEqual(time_angle(dt,Strategy(time_mapping='minute_step')),angle)
            self.assertEqual(time_root(dt,Strategy(time_model='HM24')),root24)
            self.assertEqual(time_root(dt,Strategy(time_model='HM12')),root12)
    def test_equivalent_models_and_timezone(self):
        dt=datetime(2026,1,1,12,30,45,tzinfo=timezone.utc)
        self.assertEqual(time_root(dt,Strategy(time_model='A')),time_root(dt,Strategy(time_model='B')))
        self.assertAlmostEqual(time_angle(dt,Strategy(timezone='Asia/Riyadh'))-time_angle(dt,Strategy()),45)
        anchor=Strategy(anchor_time=dt);self.assertEqual(time_angle(dt,anchor),0)
    def test_mappings_roundtrip(self):
        for method in ['linear','sqrt','increment','anchor']:
            c=Strategy(price_mapping=method,anchor_price=2000,increment=.5)
            self.assertAlmostEqual(inverse_raw(raw_price_angle(2012.3,c),c),2012.3)
        c=Strategy(anchor_price=2000,increment=2)
        self.assertEqual(price_angle(1998,c),350)
        self.assertEqual(price_angle(1998,c.model_copy(update={'clockwise':False})),10)
    def test_custom_formula_safety(self):
        self.assertEqual(safe_formula('(h+m)*2',{'h':12,'m':3}),30)
        for expression in ['__import__("os")','h**9999999','h.__class__','[1]*1000000','1/0']:
            with self.assertRaises(ValueError):safe_formula(expression,{'h':1})
    def test_settings_rejection(self):
        for settings in [{'increment':0},{'cycle_seconds':0},{'weights':{'wheel':100}},{'gates':['secret']},{'ema_fast':30,'ema_slow':20}]:
            with self.assertRaises(ValueError):Strategy(**settings)

class Causality(unittest.TestCase):
    def test_features_prefix_invariance(self):
        bars=fixture();c=Strategy();full=features(bars,c);prefix=features(bars[:300],c)
        for name in ['atr','adx','rsi','ema_fast','macd','swing_high','swing_low','high_pattern','low_pattern','structure']:
            self.assertEqual(full.iloc[299][name],prefix.iloc[-1][name])
        a=analyze(full.iloc[299].to_dict(),c,bars[299]['time']+60);b=analyze(prefix.iloc[-1].to_dict(),c,bars[299]['time']+60)
        self.assertEqual(digest(a),digest(b))
    def test_pivot_delay(self):
        bars=fixture(20)
        for i,b in enumerate(bars):b.update(high=20 if i==10 else 10,low=1,open=5,close=5)
        f=features(bars,Strategy(swing_strength=3))
        self.assertNotEqual(f.iloc[12]['swing_high'],20)
        self.assertEqual(f.iloc[13]['swing_high'],20)
    def test_resampling_closed_only(self):
        bars=fixture(10);asof=bars[6]['time']+60
        out=resample(bars,'M1','M5',asof);self.assertEqual(len(out),1)
        self.assertEqual(out[0]['close'],bars[4]['close'])
        self.assertEqual(resample(bars[1:],'M1','M5',asof),[])
        self.assertEqual(resample(bars,'M5','M1',asof),[])
    def test_forward_horizon_wall_clock(self):
        bars=fixture(30);sig={'timestamp':bars[0]['time']+60,'price':bars[0]['close'],'direction_value':1}
        result=forward_results(sig,bars,60);self.assertEqual(result[0]['price'],bars[5]['close'])
        missing=forward_results(sig,[b for i,b in enumerate(bars) if i!=5],60)
        self.assertFalse(missing[0]['available'])
    def test_manual_fib_known_at(self):
        from backend.app.technical import fibonacci
        c=Strategy(fib_low=100,fib_high=200,fib_anchor_time=datetime(2030,1,1,tzinfo=timezone.utc))
        self.assertEqual(fibonacci({},c,1704067200),[])

class Simulation(unittest.TestCase):
    def test_ambiguous_bar_stop_first(self):
        bars=[{'time':0,'open':100,'high':100,'low':100,'close':100},{'time':60,'open':100,'high':110,'low':90,'close':105}]
        signal={'timestamp':60,'direction_value':1,'direction':'BUY','targets':[{'price':108}],'invalidation':{'price':95}}
        t=execute_trade(bars,signal,0,2,Strategy(spread=.3,slippage=.05))
        self.assertEqual(t['reason'],'stop_first');self.assertAlmostEqual(t['pnl'],-5.4)
    def test_stop_gap(self):
        bars=[{'time':0,'open':100,'high':100,'low':100,'close':100},{'time':60,'open':100,'high':101,'low':99,'close':100},{'time':120,'open':90,'high':94,'low':88,'close':91}]
        sig={'timestamp':60,'direction_value':1,'direction':'BUY','targets':[{'price':108}],'invalidation':{'price':95}}
        self.assertEqual(execute_trade(bars,sig,0,3,Strategy())['exit'],90)
    def test_reproducible_backtest_and_forecasts(self):
        bars=fixture(400);c=Strategy(anchor_price=2000,threshold=45,tolerance=15,max_hold_bars=10)
        a=run_backtest(bars,c);b=run_backtest(bars,c)
        self.assertEqual(digest(a),digest(b));self.assertGreater(a['metrics']['total_signals'],0)
        self.assertAlmostEqual(a['equity'][-1]['value'],c.initial_equity+a['metrics']['net_pnl'])
        for f in a['forecasts']:self.assertEqual(f['original_hash'],digest(f['original']))
        for trade in a['trades']:self.assertGreaterEqual(trade['entry_time'],trade['signal_timestamp'])
    def test_targets_direction_and_reasons(self):
        bars=fixture(200);c=Strategy(anchor_price=2000);row=features(bars,c).iloc[-1].to_dict();p=row['close'];ts=bars[-1]['time']+60;w=state(p,ts,c)
        for d in [-1,1]:
            result=targets(p,d,row,w,c,ts);self.assertEqual(len(result['targets']),3)
            for t in result['targets']:self.assertGreater(d*(t['price']-p),0);self.assertTrue(t['reasons'][0]['formula'])
            self.assertGreater(d*(p-result['invalidation']['price']),0)
    def test_scoring_needs_wheel(self):
        bars=fixture(200);c=Strategy(harmonics=[],threshold=0);row=features(bars,c).iloc[-1].to_dict()
        a=analyze(row,c,bars[-1]['time']+60);self.assertEqual(a['direction'],'NEUTRAL');self.assertAlmostEqual(sum(a['scores'].values()),100,places=3)
    def test_walk_forward_boundaries(self):
        c=Strategy(anchor_price=2000,max_hold_bars=5);r=walk_forward(fixture(700),[c], 'M1',300,200)
        self.assertEqual(len(r['folds']),2)
        for fold in r['folds']:
            self.assertLess(fold['train_end_exclusive'],fold['test_start'])
            self.assertEqual(fold['purge_bars'],6)

class StorageAndFeed(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.db=Database(Path(self.tmp.name)/'test.sqlite')
    def tearDown(self):self.db.conn.close();self.tmp.cleanup()
    def test_immutable_chain(self):
        p={'wheel':{},'direction':'BUY'};sid=self.db.log_signal(p,'one');self.assertEqual(self.db.log_signal({'wheel':{},'direction':'SELL'},'one'),sid)
        self.assertEqual(self.db.signals()[0]['payload']['direction'],'BUY')
        self.assertTrue(self.db.verify()['valid'])
        for sql in ['UPDATE signals SET payload=\'{}\'','DELETE FROM signals']:
            with self.assertRaises(sqlite3.IntegrityError):self.db.conn.execute(sql)
        self.db.save_result(sid,300,{'price':100});self.assertEqual(len(self.db.signals()[0]['results']),1)
    def test_version_history(self):
        a=self.db.version(Strategy());b=self.db.version(Strategy(increment=2));self.assertNotEqual(a,b)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM strategy_versions').fetchone()[0],2)
    def test_csv(self):
        b=b'time,open,high,low,close,tick_volume\n2024-01-01T00:00:00Z,100,102,99,101,20\n'
        bars=parse_csv(b);self.assertEqual(bars[0]['time'],1704067200)
        with self.assertRaises(ValueError):parse_csv(b+b.splitlines()[1]+b'\n')
        with self.assertRaises(ValueError):parse_csv(b.replace(b'102',b'98'))
    def test_mt5_tick_mapping(self):
        adapter=MT5Adapter();adapter.connected=True;adapter.symbol='XAUUSD.a';adapter.mt5=Mock()
        tick=Mock(time=1704067200,time_msc=1704067200000,bid=2000.,ask=2000.4,volume=20)
        adapter.mt5.symbol_info_tick.return_value=tick
        self.assertAlmostEqual(adapter.get_current_tick()['spread'],.4)
        adapter.connected=False
        with self.assertRaises(FeedError):adapter.get_current_tick()

class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();os.environ['TIME_WHEEL_DB']=str(Path(cls.tmp.name)/'api.sqlite')
        from backend.app import main
        from fastapi.testclient import TestClient
        cls.main=main;cls.client=TestClient(main.app)
    @classmethod
    def tearDownClass(cls):cls.main.db.conn.close();cls.tmp.cleanup()
    def test_api_health_and_websocket(self):
        self.assertEqual(self.client.get('/api/health').status_code,200)
        with self.client.websocket_connect('/ws') as ws:self.assertEqual(ws.receive_json()['provider'],'disconnected')
    def test_config_and_origin(self):
        c=Strategy().model_dump(mode='json');self.assertEqual(self.client.put('/api/config',json=c).status_code,200)
        self.assertEqual(self.client.put('/api/config',json=c,headers={'origin':'https://untrusted.example'}).status_code,403)
        c['increment']=0;self.assertEqual(self.client.put('/api/config',json=c).status_code,422)
    def test_websocket_reconnect_cleans_up_and_does_not_poll(self):
        before=self.main.service.poll_count
        for _ in range(3):
            with self.client.websocket_connect('/ws?client_id=reconnect-test') as ws:
                self.assertIn('provider',ws.receive_json())
                self.assertEqual(self.main.connections['active'],1)
            self.assertEqual(self.main.connections['active'],0)
        self.assertEqual(self.main.service.poll_count,before)
        self.assertNotIn('reconnect-test',self.main.socket_clients)
    def test_websocket_same_client_replaced_once(self):
        from starlette.websockets import WebSocketDisconnect
        with self.client.websocket_connect('/ws?client_id=same-tab') as first:
            first.receive_json()
            with self.client.websocket_connect('/ws?client_id=same-tab') as second:
                second.receive_json()
                with self.assertRaises(WebSocketDisconnect) as result:first.receive_json()
                self.assertEqual(result.exception.code,4001)
                self.assertIn('wall_time',second.receive_json())
        self.assertEqual(self.main.connections['active'],0)
    def test_websocket_remains_open_for_multiple_updates(self):
        with self.client.websocket_connect('/ws?client_id=steady-test') as ws:
            samples=[ws.receive_json() for _ in range(3)]
            self.assertGreater(samples[-1]['wall_time'],samples[0]['wall_time'])
            self.assertEqual(self.client.get('/api/health').status_code,200)
    def test_csv_roundtrip(self):
        bars=fixture(100);text='time,open,high,low,close,tick_volume\n'+'\n'.join(','.join(str(b[k]) for k in ['time','open','high','low','close','tick_volume']) for b in bars)
        response=self.client.post('/api/datasets/csv',content=text,headers={'content-type':'text/csv'});self.assertEqual(response.status_code,200)
        did=response.json()['id'];self.assertEqual(self.client.post('/api/datasets/'+did+'/select').status_code,200)
        snap=self.client.get('/api/snapshot').json();self.assertEqual(snap['provider'],'CSV historical');self.assertIsNone(snap['tick']);self.assertTrue(snap['analysis'])
        # Snapshot caching must preserve historical analysis after a settings edit.
        c=self.client.get('/api/config').json()['config'];c['increment']=2
        self.assertEqual(self.client.put('/api/config',json=c).status_code,200)
        changed=self.client.get('/api/snapshot').json();self.assertTrue(changed['analysis'])
        self.assertNotEqual(changed['strategy_version'],snap['strategy_version'])
        self.assertFalse(self.client.get('/api/feed/settings').json()['auto_connect'])
        audit=self.client.get('/api/audit').json();self.assertTrue(audit['valid']);self.assertGreater(audit['count'],0)
        self.client.post('/api/feed/disconnect')

if __name__=='__main__':unittest.main(verbosity=2)
