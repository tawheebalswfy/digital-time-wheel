"""Conservative, backend-only MT5 demo execution around immutable strategy signals."""
import threading,time
from datetime import datetime,timezone
from .data import FeedError
from .config import ExecutionSettings

class ExecutionController:
    magic=20260910
    def __init__(self,db,mt5):
        self.db=db;self.mt5=mt5;self.lock=threading.RLock();self.enabled=False;self.last_error=None;self.last_blocking_reason='Auto trading disabled'
        saved=db.execution_config() or {}
        if 'timeframe' in saved and 'selected_timeframes' not in saved:saved['selected_timeframes']=[saved.pop('timeframe')]
        self.settings=ExecutionSettings(**saved)
    def save_settings(self,settings):
        with self.lock:self.settings=settings;self.db.save_execution_config(settings.model_dump());return self.status()
    def status(self):
        positions=[]
        try: positions=self.mt5.positions(); self.reconcile(positions)
        except Exception as e: self.last_error=str(e)
        state='TRADING DISABLED' if not self.enabled else ('POSITION OPEN' if positions else ('EXECUTION ERROR' if self.last_error else 'DEMO TRADING ENABLED'))
        account=self.mt5.execution_account()
        owned=[p for p in positions if p.get('magic')==self.magic and str(p.get('comment','')).startswith('DTW')]
        external=[p for p in positions if p not in owned]
        symbol=getattr(self.mt5,'symbol',None)
        return {'state':state,'enabled':self.enabled,**self.settings.model_dump(),'execution_timeframes':self.settings.selected_timeframes,'daily_sent_trades':self.db.daily_sent_count(symbol),'account':account,'open_positions':positions,'owned_positions':owned,'external_positions':external,'last_error':self.last_error,'blocking_reason':self.last_blocking_reason,'last_executed_signal':(self.db.execution_orders(1,symbol) or [None])[0]}
    def reconcile(self,positions=None):
        """Reconcile durable records against live positions and MT5 deal history."""
        positions=positions if positions is not None else self.mt5.positions()
        live={int(p.get('ticket',0)):p for p in positions if p.get('magic')==self.magic and str(p.get('comment','')).startswith('DTW')}
        for row in self.db.execution_orders(500):
            if row['state']!='POSITION OPEN': continue
            ticket=int(row.get('mt5_position_ticket') or row.get('position_ticket') or (row.get('result') or {}).get('mt5_position_ticket') or (row.get('result') or {}).get('position_ticket') or 0)
            if ticket and ticket in live: continue
            try: deals=self.mt5.history_deals(datetime.fromisoformat(row['created_at']).timestamp())
            except Exception: continue
            result=row.get('result') or {}; order_ticket=result.get('mt5_order_ticket') or result.get('ticket'); deal_ticket=result.get('mt5_deal_ticket_open') or result.get('deal')
            related=[d for d in deals if (ticket and d.get('position_id')==ticket) or (order_ticket and d.get('order')==order_ticket) or (deal_ticket and d.get('ticket')==deal_ticket)]
            exits=[d for d in related if d.get('entry') in (1,2)]
            if exits:
                d=exits[-1]; self.db.close_execution(row['id'],{'close_timestamp':datetime.fromtimestamp(d['time'],timezone.utc).isoformat(),'close_price':d['price'],'realized_profit':sum(x.get('profit',0) for x in exits),'commission':sum(x.get('commission',0) for x in exits),'swap':sum(x.get('swap',0) for x in exits),'close_reason':d.get('reason'),'deal_ticket':d.get('ticket'),'order_ticket':d.get('order'),'position_id':d.get('position_id'),'mt5_deal_ticket_close':d.get('ticket'),'mt5_order_ticket_close':d.get('order')})
            elif ticket: self.db.mark_execution_sent(row['id'],{**(row.get('result') or {}),'position_missing':True},'POSITION UNKNOWN',sent=False)
    def enable(self):
        with self.lock:
            account=self.mt5.execution_account()
            if not account['demo_confirmed']: raise FeedError('DEMO AUTO TRADING blocked: '+account['reason'])
            if not account['algo_trading_available']: raise FeedError('DEMO AUTO TRADING blocked: Algo Trading permission unavailable')
            self.enabled=True;self.last_error=None;self.last_blocking_reason='Waiting for BUY/SELL signal'
            return self.status()
    def stop(self):
        with self.lock:self.enabled=False;self.last_blocking_reason='Auto trading disabled';return self.status()
    def preview(self,signal):
        return self.mt5.build_order(signal,self.settings.fixed_lot,self.magic)
    def consider(self,signal,signal_id):
        # Called only by the collector after the exact displayed signal is persisted.
        with self.lock:
            if not self.enabled:self.last_blocking_reason='Auto trading disabled';return
            if signal['timeframe'] not in self.settings.selected_timeframes or signal['direction'] not in ('BUY','SELL'):self.last_blocking_reason='Waiting for BUY/SELL signal';return
            if signal.get('status')!='closed-bar observation' or time.time()-signal['timestamp']>1020:self.last_blocking_reason='Signal is no longer current';return
            symbol=getattr(self.mt5,'symbol',None)
            if self.settings.max_trades_per_day is not None and self.db.daily_sent_count(symbol)>=self.settings.max_trades_per_day:self.last_blocking_reason='Daily trade limit reached';return
            positions=self.mt5.positions(); self.reconcile(positions)
            owned=[p for p in positions if p.get('magic')==self.magic and str(p.get('comment','')).startswith('DTW')]
            external=[p for p in positions if p not in owned]
            if self.settings.external_positions_block and external:self.last_blocking_reason='External/manual position present';return
            if self.settings.max_positions is not None and len(owned)>=self.settings.max_positions:self.last_blocking_reason='Existing position limit reached';return
            if self.settings.max_positions_per_timeframe is not None:
                open_for_tf=sum(1 for row in self.db.execution_orders(500,symbol) if row['state']=='POSITION OPEN' and row['request'].get('timeframe')==signal['timeframe'])
                if open_for_tf>=self.settings.max_positions_per_timeframe:self.last_blocking_reason='Timeframe position limit reached';return
            if not self.settings.allow_opposite_direction and any(p['type']!=signal['direction'] for p in positions):self.last_blocking_reason='Opposite-direction positions blocked';return
            if self.settings.allow_opposite_direction and not self.mt5.execution_account().get('hedging_supported',False):self.last_blocking_reason='Opposite positions require MT5 hedging mode';return
            recent=self.db.execution_orders(1)
            if self.settings.cooldown_minutes and recent and recent[0].get('sent_at'):
                sent=datetime.fromisoformat(recent[0]['sent_at']).timestamp()
                if time.time()<sent+self.settings.cooldown_minutes*60:self.last_blocking_reason='Cooldown active';return
            try: request=self.preview(signal)
            except Exception as e:self.last_error='Order preflight: '+str(e);self.last_blocking_reason=self.last_error;return
            if self.settings.maximum_spread is not None and request['spread']>self.settings.maximum_spread:self.last_blocking_reason='Spread too high';return
            # Compact deterministic broker comment; database remains authoritative.
            request['comment']=f"DTW|{signal_id[:10]}|{signal['timeframe']}"[:31]
            payload={'timestamp':datetime.now(timezone.utc).isoformat(),'strategy_version':signal['strategy_version'],'signal_id':signal_id,'symbol':symbol,'timeframe':signal['timeframe'],'direction':signal['direction'],'confidence':signal['confidence'],'entry_price':request['price'],'requested_lot':self.settings.fixed_lot,'sl':request['sl'],'tp':request['tp'],'spread':request['spread'],'original_strategy_reasoning':signal.get('reasons',[]),'signal_timestamp':signal['timestamp'],'request':request}
            eid=self.db.reserve_execution(signal_id,payload,symbol,signal['timeframe'])
            if not eid:self.last_blocking_reason='Duplicate signal';return
            self.db.update_execution_request(eid,request)
            account=self.mt5.execution_account()
            if not account['demo_confirmed'] or not account['algo_trading_available']:
                self.db.mark_execution_sent(eid,{'sent':False,'reason':account['reason']},'EXECUTION_ERROR',sent=False);self.last_error='Order blocked: '+account['reason'];self.last_blocking_reason=self.last_error;return
            # One and only one order_send call follows a durable reservation.
            result=self.mt5.send_order(request)
            state='POSITION OPEN' if result.get('accepted') else 'EXECUTION_ERROR'
            self.db.mark_execution_sent(eid,result,state)
            if result.get('accepted') and result.get('position_ticket'): self.db.set_position_ticket(eid,result['position_ticket'])
            self.last_error=None if result.get('accepted') else result.get('message','MT5 order rejected');self.last_blocking_reason='' if result.get('accepted') else self.last_error
