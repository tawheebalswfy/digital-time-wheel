import csv,io,math,threading,time
from datetime import datetime,timezone
from typing import Protocol
from zoneinfo import ZoneInfo
from .config import TIMEFRAMES
from .time_normalization import normalize_broker_time,timestamp_audit,validate_not_future

class FeedError(RuntimeError):pass

class MarketAdapter(Protocol):
    def get_current_tick(self):...
    def get_rates(self,timeframe,count=500):...
    def get_historical_data(self,timeframe,start,end):...

def validate_bars(bars,seconds,require_alignment=True):
    if not bars:raise ValueError('No candles supplied')
    previous=None
    for b in bars:
        t=b['time']
        if type(t) is not int or t<0 or (require_alignment and t%seconds):raise ValueError('Bar open timestamps must align to the selected UTC timeframe')
        if previous is not None and t<=previous:raise ValueError('Candles must be strictly increasing; duplicates rejected')
        previous=t
        if any(not math.isfinite(b[k]) or b[k]<=0 for k in ['open','high','low','close']):raise ValueError('OHLC must be finite and positive')
        if b['low']>min(b['open'],b['close']) or b['high']<max(b['open'],b['close']) or b['low']>b['high']:raise ValueError('Inconsistent OHLC bounds')
        if not math.isfinite(b['tick_volume']) or b['tick_volume']<0:raise ValueError('Invalid tick volume')
    return bars

def parse_csv(content,timeframe='M1',source_timezone='UTC'):
    if timeframe not in TIMEFRAMES:raise ValueError('Unsupported timeframe')
    text=content.decode('utf-8-sig');reader=csv.DictReader(io.StringIO(text));bars=[]
    required={'time','open','high','low','close'}
    if not required<=set(reader.fieldnames or []):raise ValueError('CSV requires time,open,high,low,close; tick_volume optional')
    zone=ZoneInfo(source_timezone)
    for i,r in enumerate(reader,2):
        if i>200002:raise ValueError('MVP limit: 200,000 candles per import')
        try:
            raw=r['time']
            if raw.isdigit():t=int(raw)
            else:
                dt=datetime.fromisoformat(raw.replace('Z','+00:00'))
                if dt.tzinfo is None:
                    dt=dt.replace(tzinfo=zone)
                    if dt.utcoffset()!=dt.replace(fold=1).utcoffset():raise ValueError('Ambiguous DST time; supply explicit UTC offset')
                    if dt.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)!=dt.replace(tzinfo=None):raise ValueError('Nonexistent DST timestamp')
                if dt.microsecond:raise ValueError('Whole-second bar timestamps required')
                t=int(dt.timestamp())
            bars.append({'time':t,**{k:float(r[k]) for k in ['open','high','low','close']},'tick_volume':float(r.get('tick_volume') or 0)})
        except (ValueError,KeyError,TypeError) as e:raise ValueError(f'CSV row {i}: {e}') from e
    return validate_bars(bars,TIMEFRAMES[timeframe])

def resample(bars,source_tf,target_tf,asof):
    base=TIMEFRAMES[source_tf];step=TIMEFRAMES[target_tf]
    if step<base or step%base:return []
    groups={}
    for b in bars:
        if b['time']+base>asof:continue
        start=b['time']//step*step
        if start+step>asof:continue
        groups.setdefault(start,[]).append(b)
    result=[]
    for start,rows in sorted(groups.items()):
        # Missing source intervals are not silently turned into complete higher-TF candles.
        if len(rows)!=step//base or any(r['time']!=start+i*base for i,r in enumerate(rows)):continue
        result.append({'time':start,'open':rows[0]['open'],'high':max(r['high'] for r in rows),'low':min(r['low'] for r in rows),'close':rows[-1]['close'],'tick_volume':sum(r['tick_volume'] for r in rows)})
    return result

class CSVAdapter:
    def __init__(self,bars,timeframe):self.bars=bars;self.timeframe=timeframe
    def get_current_tick(self):raise FeedError('Historical CSV has no live bid/ask tick')
    def get_rates(self,timeframe,count=500):
        return resample(self.bars,self.timeframe,timeframe,self.bars[-1]['time']+TIMEFRAMES[self.timeframe])[-count:]
    def get_historical_data(self,timeframe,start,end):return [b for b in self.get_rates(timeframe,len(self.bars)) if start.timestamp()<=b['time']<end.timestamp()]

class MT5Adapter:
    def __init__(self):
        self.mt5=None;self.symbol=None;self.lock=threading.RLock();self.connected=False;self.timestamp_offset_seconds=0
        self.initialize_calls=0;self.shutdown_calls=0;self.tick_calls=0;self.rate_calls=0;self.last_tick_debug={};self.terminal_path=None;self.last_reconnect_reason=None;self.reconnect_attempts=0
    def diagnostics(self):
        try: terminal=self.mt5.terminal_info() if self.connected and self.mt5 else None
        except Exception: terminal=None
        try: account=self.mt5.account_info() if self.connected and self.mt5 else None
        except Exception: account=None
        return {'connected':self.connected,'symbol':self.symbol,'terminal_path':getattr(terminal,'path',None) or self.terminal_path,'terminal_build':getattr(terminal,'build',None),'account_login':getattr(account,'login',None),'account_server':getattr(account,'server',None),'account_mode':getattr(account,'trade_mode',None),'algo_trading_available':bool(getattr(terminal,'trade_allowed',False) and not getattr(terminal,'tradeapi_disabled',True) and getattr(account,'trade_expert',False)) if terminal and account else False,'initialize_calls':self.initialize_calls,'shutdown_calls':self.shutdown_calls,'reconnect_attempts':self.reconnect_attempts,'last_reconnect_reason':self.last_reconnect_reason,'tick_calls':self.tick_calls,'rate_calls':self.rate_calls,'timestamp_offset_seconds':self.timestamp_offset_seconds,'last_tick':self.last_tick_debug.copy()}
    def connect_mt5(self,symbol='XAUUSD',path=None,timestamp_offset_seconds=0):
        with self.lock:
            if self.connected:
                if path and path!=self.terminal_path:raise FeedError('Disconnect before choosing a different terminal')
                if symbol!=self.symbol:
                    if not self.mt5.symbol_select(symbol,True):raise FeedError('Cannot select requested symbol')
                    self.symbol=symbol
                self.timestamp_offset_seconds=timestamp_offset_seconds
                return self.get_symbol_info()
            try:import MetaTrader5 as mt5
            except ImportError as e:raise FeedError('Install the optional MetaTrader5 package on Windows') from e
            self.mt5=mt5;self.timestamp_offset_seconds=timestamp_offset_seconds
            self.initialize_calls+=1
            ok=mt5.initialize(path,timeout=10000) if path else mt5.initialize(timeout=10000)
            if not ok:raise FeedError(f'MT5 initialization failed: {mt5.last_error()}. Open and sign in to your broker terminal.')
            terminal=mt5.terminal_info()
            if terminal is None or not terminal.connected:
                mt5.shutdown();raise FeedError('MT5 terminal is not connected to a broker')
            info=mt5.symbol_info(symbol)
            if info is None:
                candidates=[s.name for s in (mt5.symbols_get() or []) if s.name.upper().startswith(('XAUUSD','GOLD'))]
                if not candidates:mt5.shutdown();raise FeedError('No compatible gold symbol found')
                # Deterministic preference; alternatives disclosed to user.
                symbol=sorted(candidates,key=lambda x:(not x.upper().startswith('XAUUSD'),len(x),x))[0]
            if not mt5.symbol_select(symbol,True):mt5.shutdown();raise FeedError('Cannot select gold symbol')
            self.symbol=symbol;self.connected=True;self.terminal_path=path
            return self.get_symbol_info()
    def disconnect_mt5(self):
        with self.lock:
            if self.mt5 and self.connected:self.mt5.shutdown();self.shutdown_calls+=1
            self.connected=False
    def refresh_session(self,reason):
        """Perform one serialized shutdown/reinitialize cycle; caller controls backoff."""
        with self.lock:
            self.last_reconnect_reason=str(reason); self.reconnect_attempts+=1
            path=self.terminal_path; symbol=self.symbol or 'XAUUSD'; offset=self.timestamp_offset_seconds
            if self.connected:self.disconnect_mt5()
            time.sleep(0.25)
            return self.connect_mt5(symbol,path,offset)
    def check(self):
        if not self.connected:raise FeedError('MT5 disconnected')
    def get_symbol_info(self):
        with self.lock:
            self.check();s=self.mt5.symbol_info(self.symbol)
            if s is None:raise FeedError('Symbol metadata unavailable')
            return {'symbol':s.name,'digits':s.digits,'point':s.point,'description':s.description,'source':'MT5','trade_stops_level':int(getattr(s,'trade_stops_level',0)),'trade_freeze_level':int(getattr(s,'trade_freeze_level',0)),'trade_mode':int(getattr(s,'trade_mode',-1)),'visible':bool(getattr(s,'visible',True)),'volume_min':float(getattr(s,'volume_min',0)),'volume_max':float(getattr(s,'volume_max',0)),'volume_step':float(getattr(s,'volume_step',0))}
    def discover_symbols(self,query=''):
        with self.lock:
            self.check(); q=query.upper().strip(); result=[]
            for item in (self.mt5.symbols_get() or []):
                name=str(getattr(item,'name',''))
                if not name or (q and q not in name.upper() and q not in str(getattr(item,'description','')).upper()): continue
                info=self.mt5.symbol_info(name)
                if info is None or not bool(getattr(info,'visible',True)): continue
                result.append({'symbol':name,'description':str(getattr(info,'description','')),'path':str(getattr(info,'path','')),'digits':int(getattr(info,'digits',0)),'point':float(getattr(info,'point',0)),'bid':float(getattr(info,'bid',0)),'ask':float(getattr(info,'ask',0)),'spread':float(getattr(info,'ask',0)-getattr(info,'bid',0)),'trade_mode':int(getattr(info,'trade_mode',-1)),'volume_min':float(getattr(info,'volume_min',0)),'volume_max':float(getattr(info,'volume_max',0)),'volume_step':float(getattr(info,'volume_step',0))})
            return sorted(result,key=lambda x:x['symbol'])[:2000]
    def tradeability(self,direction=None):
        with self.lock:
            self.check(); terminal=self.mt5.terminal_info(); account=self.mt5.account_info(); s=self.mt5.symbol_info(self.symbol)
            if terminal is None or not getattr(terminal,'connected',False): return False,'MT5 terminal disconnected'
            if account is None or not getattr(account,'trade_allowed',False) or not getattr(account,'trade_expert',False): return False,'Account trading permission unavailable'
            if s is None or not getattr(s,'visible',True) or not self.mt5.symbol_select(self.symbol,True): return False,f'{self.symbol} is unavailable or not selected'
            mode=int(getattr(s,'trade_mode',-1)); disabled=int(getattr(self.mt5,'SYMBOL_TRADE_MODE_DISABLED',0)); closeonly=int(getattr(self.mt5,'SYMBOL_TRADE_MODE_CLOSEONLY',3))
            if mode in (disabled,closeonly): return False,'Market closed or symbol trade mode does not permit new orders'
            if direction=='BUY' and mode==int(getattr(self.mt5,'SYMBOL_TRADE_MODE_SHORTONLY',2)): return False,'Broker permits SELL only'
            if direction=='SELL' and mode==int(getattr(self.mt5,'SYMBOL_TRADE_MODE_LONGONLY',1)): return False,'Broker permits BUY only'
            tick=self.mt5.symbol_info_tick(self.symbol)
            if tick is None or not math.isfinite(float(tick.bid)) or not math.isfinite(float(tick.ask)) or float(tick.bid)<=0 or float(tick.ask)<float(tick.bid): return False,'Valid live bid/ask unavailable'
            corrected=float(normalize_broker_time(tick.time,self.timestamp_offset_seconds))
            if time.time()-corrected>120:return False,'Quote is stale'
            return True,'Tradeable'
    def execution_account(self):
        with self.lock:
            if not self.connected or not self.mt5:return {'demo_confirmed':False,'algo_trading_available':False,'reason':'MT5 is not connected'}
            account=self.mt5.account_info();terminal=self.mt5.terminal_info()
            if account is None or terminal is None:return {'demo_confirmed':False,'algo_trading_available':False,'reason':'MT5 account or terminal information unavailable'}
            demo=getattr(account,'trade_mode',None)==getattr(self.mt5,'ACCOUNT_TRADE_MODE_DEMO',object())
            allowed=bool(getattr(terminal,'connected',False) and getattr(terminal,'trade_allowed',False) and not getattr(terminal,'tradeapi_disabled',True) and getattr(account,'trade_allowed',False) and getattr(account,'trade_expert',False))
            margin_mode=getattr(account,'margin_mode',None);hedging=margin_mode==getattr(self.mt5,'ACCOUNT_MARGIN_MODE_RETAIL_HEDGING',object())
            return {'demo_confirmed':demo,'algo_trading_available':allowed,'reason':'DEMO confirmed' if demo and allowed else ('Connected account is not positively identified as DEMO' if not demo else 'Algo Trading permission unavailable'),'login':getattr(account,'login',None),'server':getattr(account,'server',None),'trade_mode':getattr(account,'trade_mode',None),'margin_mode':margin_mode,'hedging_supported':hedging}
    def positions(self):
        with self.lock:
            self.check();rows=self.mt5.positions_get(symbol=self.symbol) or []
            return [{'ticket':int(getattr(p,'ticket',0)),'type':'BUY' if getattr(p,'type',1)==getattr(self.mt5,'POSITION_TYPE_BUY',0) else 'SELL','volume':float(getattr(p,'volume',0)),'price_open':float(getattr(p,'price_open',0)),'sl':float(getattr(p,'sl',0)),'tp':float(getattr(p,'tp',0)),'profit':float(getattr(p,'profit',0)),'magic':int(getattr(p,'magic',0)),'comment':str(getattr(p,'comment','')),'time':int(getattr(p,'time',0)),'identifier':int(getattr(p,'identifier',getattr(p,'ticket',0)))} for p in rows]
    def build_order(self,signal,volume,magic):
        with self.lock:
            self.check();account=self.execution_account()
            if not account['demo_confirmed']:raise FeedError(account['reason'])
            ok,reason=self.tradeability(signal.get('direction'))
            if not ok: raise FeedError(reason)
            s=self.mt5.symbol_info(self.symbol);tick=self.get_current_tick()
            if s is None:raise FeedError('Symbol metadata unavailable')
            step=float(getattr(s,'volume_step',0));minimum=float(getattr(s,'volume_min',0));maximum=float(getattr(s,'volume_max',0))
            if step<=0 or volume<minimum or volume>maximum or abs(round((volume-minimum)/step)-((volume-minimum)/step))>1e-7:raise FeedError('Requested lot violates broker volume limits')
            direction=signal['direction'];digits=int(s.digits);point=float(s.point);entry=tick['ask'] if direction=='BUY' else tick['bid']
            invalidation=(signal.get('invalidation') or {}).get('price');targets=signal.get('targets') or []
            if invalidation is None or not targets:raise FeedError('Current strategy did not supply both invalidation and target')
            sl=round(float(invalidation),digits);tp=round(float(targets[0]['price']),digits);minimum_distance=max(float(getattr(s,'trade_stops_level',0))*point,float(getattr(s,'trade_freeze_level',0))*point,point)
            bid,ask=tick['bid'],tick['ask']
            valid=(direction=='BUY' and sl<=bid-minimum_distance and tp>=ask+minimum_distance) or (direction=='SELL' and sl>=ask+minimum_distance and tp<=bid-minimum_distance)
            if not valid:raise FeedError('Strategy SL/TP violates direction or broker stop-level requirements')
            typ=getattr(self.mt5,'ORDER_TYPE_BUY') if direction=='BUY' else getattr(self.mt5,'ORDER_TYPE_SELL')
            return {'action':getattr(self.mt5,'TRADE_ACTION_DEAL'),'symbol':self.symbol,'volume':volume,'type':typ,'price':round(entry,digits),'sl':sl,'tp':tp,'deviation':20,'magic':magic,'comment':'DTW demo signal','type_time':getattr(self.mt5,'ORDER_TIME_GTC'),'type_filling':getattr(self.mt5,'ORDER_FILLING_IOC'),'spread':tick['spread']}
    def send_order(self,request):
        with self.lock:
            account=self.execution_account()
            if not account['demo_confirmed'] or not account['algo_trading_available']:return {'accepted':False,'sent':False,'message':account['reason']}
            ok,reason=self.tradeability('BUY' if request.get('type')==getattr(self.mt5,'ORDER_TYPE_BUY',-999) else 'SELL')
            if not ok:return {'accepted':False,'sent':False,'message':reason}
            result=self.mt5.order_send(request)
            if result is None:return {'accepted':False,'sent':True,'message':str(self.mt5.last_error())}
            retcode=int(getattr(result,'retcode',0));accepted=retcode in {getattr(self.mt5,'TRADE_RETCODE_DONE',10009),getattr(self.mt5,'TRADE_RETCODE_PLACED',10008)}
            order_ticket=int(getattr(result,'order',0) or 0);deal_ticket=int(getattr(result,'deal',0) or 0)
            payload={'accepted':accepted,'sent':True,'retcode':retcode,'message':str(getattr(result,'comment','')),
                     'ticket':order_ticket,'deal':deal_ticket,
                     'mt5_order_ticket':order_ticket or None,'mt5_deal_ticket_open':deal_ticket or None,
                     'actual_fill_price':float(getattr(result,'price',0) or 0),'mt5_comment':request.get('comment'),
                     'magic_number':request.get('magic'),'volume':request.get('volume')}
            if accepted:
                try:
                    # On hedging accounts order/deal/position are distinct.  A
                    # returned deal is the strongest bridge to position_id.
                    candidates=self.history_deals(max(0,time.time()-30))
                    related=[d for d in candidates if (deal_ticket and d.get('ticket')==deal_ticket) or (order_ticket and d.get('order')==order_ticket)]
                    opened=[d for d in related if d.get('entry') in (0,)]
                    if opened:
                        d=opened[-1]; payload.update({'mt5_position_ticket':d.get('position_id') or None,'position_ticket':d.get('position_id') or None,'open_time':datetime.fromtimestamp(d['time'],timezone.utc).isoformat(),'actual_fill_price':d.get('price') or payload['actual_fill_price'],'commission':d.get('commission'),'swap':d.get('swap')})
                    else:
                        direction='BUY' if request.get('type')==getattr(self.mt5,'ORDER_TYPE_BUY',-999) else 'SELL'
                        candidates=[p for p in self.positions() if p.get('magic')==request.get('magic') and p.get('type')==direction and str(p.get('comment','')).startswith('DTW')]
                        if candidates: payload.update({'position_ticket':candidates[-1]['ticket'],'mt5_position_ticket':candidates[-1]['ticket'],'open_time':datetime.fromtimestamp(candidates[-1]['time'],timezone.utc).isoformat() if candidates[-1].get('time') else None})
                except Exception: pass
            return payload
    def history_deals(self,start_epoch,end_epoch=None):
        with self.lock:
            self.check(); from datetime import datetime,timedelta
            # MT5 history requests use the broker wall-clock range.  Convert
            # our canonical UTC boundaries exactly once at this adapter edge.
            end_epoch=time.time() if end_epoch is None else end_epoch
            start=max(0,float(start_epoch));end=max(start,float(end_epoch))
            offset=self.timestamp_offset_seconds
            rows=self.mt5.history_deals_get(datetime.fromtimestamp(start+offset,timezone.utc),datetime.fromtimestamp(end+offset,timezone.utc)+timedelta(minutes=1)) or []
            return [{'ticket':int(getattr(d,'ticket',0)),'order':int(getattr(d,'order',0)),'position_id':int(getattr(d,'position_id',0)),'type':int(getattr(d,'type',-1)),'entry':int(getattr(d,'entry',-1)),'time':int(normalize_broker_time(getattr(d,'time',0),offset)),'price':float(getattr(d,'price',0)),'profit':float(getattr(d,'profit',0)),'commission':float(getattr(d,'commission',0)),'swap':float(getattr(d,'swap',0)),'reason':int(getattr(d,'reason',-1)),'volume':float(getattr(d,'volume',0)),'symbol':str(getattr(d,'symbol','')),'magic':int(getattr(d,'magic',0) or 0),'comment':str(getattr(d,'comment',''))} for d in rows]
    def get_current_tick(self):
        with self.lock:
            self.check();self.tick_calls+=1;tick=self.mt5.symbol_info_tick(self.symbol)
            if tick is None or not math.isfinite(tick.bid) or not math.isfinite(tick.ask) or tick.bid<=0 or tick.ask<tick.bid:raise FeedError('Valid bid/ask tick unavailable')
            corrected=int(normalize_broker_time(tick.time,self.timestamp_offset_seconds))
            self.last_tick_debug={'raw_time':int(tick.time),'normalized_utc':corrected,'observed_system_utc':time.time(),'raw_minus_system_seconds':int(tick.time)-time.time(),'offset_seconds':self.timestamp_offset_seconds,'bid':float(tick.bid),'ask':float(tick.ask)}
            try:validate_not_future(corrected,time.time())
            except ValueError as e:raise FeedError(str(e)+'. Verify the separately configured broker UTC offset.') from e
            return {'time':corrected,'time_msc':int(tick.time_msc)-self.timestamp_offset_seconds*1000,'raw_time':int(tick.time),'raw_time_msc':int(tick.time_msc),'timestamp_offset_seconds':self.timestamp_offset_seconds,'bid':float(tick.bid),'ask':float(tick.ask),'spread':float(tick.ask-tick.bid),'volume':float(tick.volume),'symbol':self.symbol,'source':'MT5',**timestamp_audit(tick.time,self.timestamp_offset_seconds)}
    def get_rates(self,timeframe,count=500):
        with self.lock:
            self.check()
            if timeframe not in TIMEFRAMES:raise FeedError('Unsupported timeframe')
            self.rate_calls+=1
            rates=self.mt5.copy_rates_from_pos(self.symbol,getattr(self.mt5,'TIMEFRAME_'+timeframe),0,count)
            return self._convert(rates,timeframe)
    def get_historical_data(self,timeframe,start,end):
        with self.lock:
            self.check()
            if start.tzinfo is None or end.tzinfo is None:raise ValueError('UTC-aware dates required')
            if timeframe not in TIMEFRAMES:raise ValueError('Unsupported timeframe')
            from datetime import timedelta
            offset=timedelta(seconds=self.timestamp_offset_seconds)
            rates=self.mt5.copy_rates_range(self.symbol,getattr(self.mt5,'TIMEFRAME_'+timeframe),start.astimezone(timezone.utc)+offset,end.astimezone(timezone.utc)+offset)
            return [b for b in self._convert(rates,timeframe) if start.timestamp()<=b['time'] and b['time']+TIMEFRAMES[timeframe]<=end.timestamp()]
    def _convert(self,rates,timeframe):
        if rates is None or not len(rates):raise FeedError(f'MT5 returned no rates: {self.mt5.last_error()}')
        bars=[{'time':int(normalize_broker_time(int(r['time']),self.timestamp_offset_seconds)),**{k:float(r[k]) for k in ['open','high','low','close','tick_volume']},**timestamp_audit(int(r['time']),self.timestamp_offset_seconds)} for r in rates]
        try:
            for bar in bars:validate_not_future(bar['time'],time.time())
        except ValueError as e:raise FeedError(str(e)) from e
        return validate_bars(bars,TIMEFRAMES[timeframe],False)
