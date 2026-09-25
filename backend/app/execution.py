"""Conservative, backend-only MT5 demo execution around immutable strategy signals."""
import logging,threading,time
from datetime import datetime,timezone
from .data import FeedError
from .config import ExecutionSettings

class ExecutionController:
    magic=20260910
    close_entries={1,2,3} # DEAL_ENTRY_OUT, DEAL_ENTRY_INOUT, DEAL_ENTRY_OUT_BY
    history_max_seconds=7*24*60*60
    reconcile_interval_seconds=30
    def __init__(self,db,mt5):
        self.db=db;self.mt5=mt5;self.lock=threading.RLock();self.enabled=False;self.last_error=None;self.last_blocking_reason='Auto trading disabled'
        saved=db.execution_config() or {}
        if 'timeframe' in saved and 'selected_timeframes' not in saved:saved['selected_timeframes']=[saved.pop('timeframe')]
        self.settings=ExecutionSettings(**saved);self._last_reconcile_monotonic=0.0
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
        """Bounded, ticket-first close reconciliation; it never sends orders."""
        positions=positions if positions is not None else self.mt5.positions()
        live={}
        for p in positions:
            if p.get('magic')==self.magic and str(p.get('comment','')).startswith('DTW'):
                for key in ('ticket','identifier'):
                    if p.get(key):live[int(p[key])]=p
        candidates=[]
        for row in self.db.execution_orders(500):
            if row['state'] not in {'POSITION OPEN','POSITION UNKNOWN'}:continue
            if not str(row.get('mt5_comment') or '').startswith('DTW'):continue
            ticket=int(row.get('mt5_position_ticket') or row.get('position_ticket') or 0)
            if not ticket:continue
            if ticket in live:
                if row['state']!='POSITION OPEN':self.db.set_execution_state(row['id'],'POSITION OPEN')
                continue
            candidates.append((row,ticket))
        if not candidates:return
        now_epoch=time.time();starts=[]
        for row,_ in candidates:
            try: starts.append(datetime.fromisoformat(row.get('open_time') or row['created_at']).timestamp())
            except (TypeError,ValueError): starts.append(now_epoch-self.history_max_seconds)
        try: deals=self.mt5.history_deals(max(now_epoch-self.history_max_seconds,min(starts)),now_epoch)
        except Exception as e:
            self.last_error=f'Close reconciliation history lookup failed: {e}';return
        for row,ticket in candidates:
            related=[d for d in deals if int(d.get('position_id') or 0)==ticket and self._deal_belongs_to_execution(d,row)]
            exits=[d for d in related if int(d.get('entry',-1)) in self.close_entries]
            if exits:
                d=max(exits,key=lambda item:item.get('time',0))
                # Profit is close-deal profit. Costs are position costs across
                # each linked deal, so opening commission is included once.
                closed=self.db.close_execution(row['id'],{'close_timestamp':datetime.fromtimestamp(d['time'],timezone.utc).isoformat(),'close_price':d.get('price'),'realized_profit':sum(float(x.get('profit') or 0) for x in exits),'commission':sum(float(x.get('commission') or 0) for x in related),'swap':sum(float(x.get('swap') or 0) for x in related),'close_reason':d.get('reason'),'deal_ticket':d.get('ticket'),'order_ticket':d.get('order'),'position_id':ticket})
                if not closed: logging.getLogger(__name__).warning('Close linkage found but timestamp validation rejected execution %s',row['id'])
            else:self.db.set_execution_state(row['id'],'POSITION UNKNOWN')
    def reconcile_periodic(self):
        """Run bounded recovery at most once per interval while the backend runs."""
        current=time.monotonic()
        if current-self._last_reconcile_monotonic<self.reconcile_interval_seconds:return
        self._last_reconcile_monotonic=current
        try:self.reconcile()
        except Exception as e:self.last_error=f'Close reconciliation failed: {e}'
    def _deal_belongs_to_execution(self,deal,row):
        """Additional ownership checks after exact DEAL_POSITION_ID linkage."""
        if deal.get('symbol') and row.get('symbol') and deal['symbol']!=row['symbol']:return False
        row_magic=row.get('magic_number')
        if row_magic is not None and deal.get('magic') not in (None,0,int(row_magic)):return False
        volume=row.get('volume')
        if volume is not None and deal.get('volume') and float(deal['volume'])>float(volume)+1e-9:return False
        return True
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
            try: request=self.preview({**signal,'signal_id':signal_id})
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
