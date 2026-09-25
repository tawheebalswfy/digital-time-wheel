import time,threading,copy
from .config import Strategy,FeedSettings,ExecutionSettings,TIMEFRAMES
from .time_normalization import offset_seconds,offset_label
from .data import MT5Adapter,CSVAdapter,FeedError
from .technical import features
from .signals import analyze
from .wheel import state,time_angle
from .backtest import forward_results
from .database import digest
from .execution import ExecutionController

class Service:
    def __init__(self,db):
        self.db=db;self.config=Strategy(**(db.config() or {}));self.version=db.version(self.config)
        self.mt5=MT5Adapter();self.provider='disconnected';self.dataset_id=None;self.feed=None;self.lock=threading.RLock()
        self._cache=None;self.poll_count=0;self._rates_cache={};self._rates_updated=0;self._reconnect_backoff=[1,2,5,10,30];self._reconnect_index=0;self._next_reconnect=0.0
        self.feed_settings=FeedSettings(**(db.feed_config() or {}))
        # Never restored from storage: every process start begins with execution disabled.
        self.execution=ExecutionController(db,self.mt5)
    def set_feed_settings(self,settings):
        with self.lock:
            self.feed_settings=settings;self.db.save_feed_config(settings.model_dump())
            self.mt5.timestamp_offset_seconds=offset_seconds(settings.broker_utc_offset)
            self._cache=None;self._rates_cache={};self._rates_updated=0
        return settings.model_dump()
    def restore_feed(self):
        if self.feed_settings.auto_connect:
            self.connect(self.feed_settings.symbol,self.feed_settings.terminal_path)
    def configure(self,c):
        with self.lock:
            if self.mt5.connected and c.symbol!=self.config.symbol:
                self.mt5.disconnect_mt5();self.provider='disconnected';self.feed=None
            self.config=c;self.version=self.db.version(c);self._cache=None
            if self.provider=='CSV historical' and self.feed:self.poll()
            return {'version':self.version,'config':c.model_dump(mode='json')}
    def connect(self,symbol,path=None,timestamp_offset_seconds=None):
        with self.lock:
            switching=self.config.symbol!=symbol
            if switching and self.execution.enabled:
                # Symbol changes always require an explicit readiness/enable step.
                self.execution.stop()
            if self.provider=='MT5' and self.config.symbol!=symbol:
                self.db.save_symbol_profile(self.config.symbol,self.config.model_dump(mode='json'),self.execution.settings.model_dump(),self.feed_settings.model_dump())
            timestamp_offset_seconds=offset_seconds(self.feed_settings.broker_utc_offset) if timestamp_offset_seconds is None else timestamp_offset_seconds
            result=self.mt5.connect_mt5(symbol,path,timestamp_offset_seconds);self.provider='MT5';self.dataset_id=None;self.feed=self.mt5
            profile=self.db.symbol_profile(result['symbol'])
            if profile:
                self.config=Strategy(**profile['strategy']); self.execution.settings=ExecutionSettings(**profile['execution'])
            elif result['symbol']!='XAUUSD':
                tick=self.mt5.get_current_tick(); info=self.mt5.get_symbol_info(); midpoint=(tick['bid']+tick['ask'])/2
                self.config=Strategy(**{**self.config.model_dump(),'symbol':result['symbol'],'anchor_price':midpoint,'increment':max(info['point']*10,info['point'])})
            self.set_feed_settings(FeedSettings(**{**self.feed_settings.model_dump(),'symbol':result['symbol'],'terminal_path':path,'broker_utc_offset':offset_label(timestamp_offset_seconds),'auto_connect':True}))
            self.configure(Strategy(**{**self.config.model_dump(),'symbol':result['symbol']}));self.db.save_symbol_profile(result['symbol'],self.config.model_dump(mode='json'),self.execution.settings.model_dump(),self.feed_settings.model_dump());self._rates_cache={};self._rates_updated=0;self.poll();return result
    def disconnect(self):
        with self.lock:self.mt5.disconnect_mt5();self.provider='disconnected';self.feed=None;self._cache=None
    def select_dataset(self,did):
        with self.lock:
            metadata=next((x for x in self.db.datasets() if x['id']==did),None)
            if not metadata:raise ValueError('Dataset not found')
            self.set_feed_settings(self.feed_settings.model_copy(update={'auto_connect':False}))
            bars=self.db.bars(did);self.mt5.disconnect_mt5();self.feed=CSVAdapter(bars,metadata['timeframe']);self.provider='CSV historical';self.dataset_id=did
            self.configure(Strategy(**{**self.config.model_dump(),'symbol':metadata['symbol']}))
            return metadata
    def snapshot(self,tf='M1'):
        if tf not in TIMEFRAMES:raise ValueError('Unsupported timeframe')
        with self.lock:
            result=copy.deepcopy(self._cache) if self._cache else self._empty()
            result['wall_time']=time.time();result['clock_angle']=time_angle(time.time(),self.config)
            result['candles']=result.pop('charts',{}).get(tf,[])
            result['analysis']=result.pop('analyses',{}).get(tf)
            result['signal_id']=result.pop('signal_ids',{}).get(tf)
            if self.provider!='MT5' and result['analysis']:result['wheel']=result['analysis']['wheel']
            result['connection_diagnostics']={'poll_count':self.poll_count,**self.mt5.diagnostics()}
            result['feed_settings']=self.feed_settings.model_dump()
            result['execution']=self.execution.status()
            result['analysis_timezone']=self.config.timezone
            if result.get('tick'):
                tick=result['tick'];result['tick_age_seconds']=time.time()-tick['time_msc']/1000
                result['stale']=result['tick_age_seconds']>120
                result['last_candle_timestamp']=result['candles'][-1]['time'] if result['candles'] else None
                result['last_candle_broker_time']=result['candles'][-1].get('broker_time') if result['candles'] else None
            return result
    def _empty(self):
        return {'provider':self.provider,'dataset_id':self.dataset_id,'symbol':self.config.symbol,'strategy_version':self.version,'wall_time':time.time(),
                'disclaimer':'Signals are probabilistic and are not guaranteed.','clock_angle':time_angle(time.time(),self.config),'tick':None,'candles':[],'timeframes':[],'analysis':None,'wheel':None,'error':None}
    def poll(self):
        with self.lock:
            self.poll_count+=1
            # Lifecycle recovery is independent of auto-trading.  It only
            # reads positions/history and is throttled by the controller.
            if self.provider=='MT5':self.execution.reconcile_periodic()
            try:self._cache=self._collect()
            except (FeedError,ValueError) as e:
                if self.provider=='MT5' and time.monotonic()>=self._next_reconnect:
                    try:
                        self.mt5.refresh_session(str(e)); self.mt5.get_current_tick(); account=self.mt5.execution_account()
                        if not account.get('demo_confirmed'): raise FeedError(account.get('reason','Account session invalid'))
                        self._reconnect_index=0; self._next_reconnect=time.monotonic()+1
                    except Exception as reconnect_error:
                        delay=self._reconnect_backoff[min(self._reconnect_index,len(self._reconnect_backoff)-1)];self._reconnect_index=min(self._reconnect_index+1,len(self._reconnect_backoff)-1);self._next_reconnect=time.monotonic()+delay
                        self.mt5.last_reconnect_reason=f'{e}; refresh failed: {reconnect_error}'
                # A transient quote read failure must not erase the last valid
                # live snapshot.  Consumers use the cache as the transport
                # source, so replacing it with an empty error object would
                # broadcast a stale/empty tick over the next WebSocket update.
                previous=self._cache
                if previous and previous.get('tick') and previous['tick'].get('bid') is not None and previous['tick'].get('ask') is not None:
                    self._cache={**previous,'error':None}
                else:
                    self._cache={**self._empty(),'error':str(e),'stale':True}
            return self._cache
    def _collect(self):
        with self.lock:
            wall=time.time();result={**self._empty(),'charts':{},'analyses':{},'signal_ids':{}}
            if not self.feed:return result
            if self.provider=='MT5':
                tick=self.mt5.get_current_tick();result['tick']=tick;self.db.save_tick('MT5',self.config.symbol,tick)
                result['stale']=wall-tick['time']>120;result['tick_age_seconds']=max(0,wall-tick['time'])
                if result['stale']: raise FeedError('Quote is stale; MT5 session refresh required')
                asof=min(wall,tick['time']);result['wheel']=state((tick['bid']+tick['ask'])/2,asof,self.config)
            else:asof=self.feed.bars[-1]['time']+TIMEFRAMES[self.feed.timeframe];result['stale']=True
            result['analysis_asof']=asof
            refresh_rates=wall-self._rates_updated>=10
            for name,seconds in TIMEFRAMES.items():
                try:
                    if self.provider=='MT5' and not refresh_rates and name in self._rates_cache:
                        cached=self._rates_cache[name]
                        if isinstance(cached,str):raise FeedError(cached)
                        bars=cached
                    else:
                        bars=self.feed.get_rates(name,600);self._rates_cache[name]=bars
                except FeedError as e:
                    self._rates_cache[name]=str(e)
                    result['timeframes'].append({'timeframe':name,'available':False,'reason':str(e)});continue
                closed=[b for b in bars if b['time']+seconds<=asof]
                result['charts'][name]=bars
                needed=max(60,self.config.ema_slow*3,self.config.sma_period,self.config.bb_period)
                if len(closed)<needed:
                    result['timeframes'].append({'timeframe':name,'available':False,'reason':f'{len(closed)}/{needed} closed bars available'});continue
                row=features(closed,self.config).iloc[-1].to_dict();signal=analyze(row,self.config,closed[-1]['time']+seconds)
                signal.update({'timeframe':name,'strategy_version':self.version,'source':self.provider,'dataset_id':self.dataset_id,'symbol':self.config.symbol,
                    'broker_utc_offset':self.feed_settings.broker_utc_offset if self.provider=='MT5' else None,'analysis_timezone':self.config.timezone,
                    'input_hash':digest(closed),'observed_at':wall,'late_observation_seconds':max(0,wall-signal['timestamp']),
                    'status':'historical reconstruction' if self.provider!='MT5' or wall-signal['timestamp']>seconds else 'closed-bar observation'})
                key=digest([self.provider,self.dataset_id,self.config.symbol,name,self.version,signal['timestamp']])
                sid=self.db.log_signal(signal,key)
                result['timeframes'].append({'timeframe':name,'available':True,'signal_id':sid,**{k:signal[k] for k in ['direction','label','confidence','structure','momentum','numerical_signal']}})
                result['analyses'][name]=signal;result['signal_ids'][name]=sid
                if name in self.execution.settings.selected_timeframes and self.provider=='MT5':self.execution.consider(signal,sid)
                if name=='M1':
                    # Append outcomes only; immutable original forecasts are never replaced.
                    for saved in self.db.signals(200):
                        original=saved['payload']
                        if original.get('timeframe')!=name or original.get('source')!=self.provider or original.get('dataset_id')!=self.dataset_id or original.get('symbol')!=self.config.symbol:continue
                        for outcome in forward_results(original,closed,seconds):
                            if outcome['available']:self.db.save_result(saved['id'],outcome['horizon_seconds'],outcome)
            if refresh_rates:self._rates_updated=wall
            return result
