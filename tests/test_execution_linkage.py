import tempfile, time, unittest
from pathlib import Path
from backend.app.database import Database
from backend.app.execution import ExecutionController
from backend.app.config import ExecutionSettings

class LinkMT5:
    def __init__(self): self.sent=[]; self.next=100
    def execution_account(self): return {'demo_confirmed':True,'algo_trading_available':True,'reason':'DEMO confirmed','hedging_supported':True}
    def positions(self): return []
    def build_order(self,signal,volume,magic): return {'price':100.0,'sl':99.0,'tp':101.0,'spread':0.01,'magic':magic,'volume':volume,'type':'BUY'}
    def send_order(self,request):
        self.next+=1; self.sent.append(request)
        return {'accepted':True,'sent':True,'retcode':10009,'ticket':self.next,'deal':self.next+1000,'position_ticket':self.next+2000,'actual_fill_price':100.01}

def signal(tf, ts=None):
    return {'timeframe':tf,'direction':'BUY','timestamp':ts or time.time(),'status':'closed-bar observation','strategy_version':'strategy-v1','confidence':70,'reasons':[]}

class ExecutionLinkage(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=Database(Path(self.tmp.name)/'db.sqlite'); self.mt=LinkMT5(); self.c=ExecutionController(self.db,self.mt); self.c.save_settings(ExecutionSettings(selected_timeframes=['M15','M30'],max_positions=3,max_positions_per_timeframe=3)); self.c.enable()
    def tearDown(self): self.db.conn.close(); self.tmp.cleanup()
    def reserve_signal(self, name): return self.db.log_signal({'wheel':{},'symbol':'XAUUSD','timeframe':name},name+'-event')
    def test_ticket_fields_and_comment_persist(self):
        sid=self.reserve_signal('M15'); self.c.consider(signal('M15'),sid); row=self.db.execution_orders(1)[0]
        self.assertEqual(row['mt5_order_ticket'],101); self.assertEqual(row['mt5_deal_ticket_open'],1101); self.assertEqual(row['mt5_position_ticket'],2101); self.assertTrue(row['mt5_comment'].startswith('DTW|')); self.assertEqual(row['timeframe'],'M15')
    def test_independent_timeframes_are_both_allowed(self):
        a=self.reserve_signal('M15'); b=self.reserve_signal('M30'); self.c.consider(signal('M15'),a); self.c.consider(signal('M30'),b); self.assertEqual(len(self.mt.sent),2); self.assertNotEqual(a,b)
    def test_same_signal_reserved_once(self):
        sid=self.reserve_signal('M15'); self.c.consider(signal('M15'),sid); self.c.consider(signal('M15'),sid); self.assertEqual(len(self.mt.sent),1); self.assertEqual(len(self.db.execution_orders()),1)
    def test_legacy_unresolved_remains_unresolved(self):
        sid=self.reserve_signal('M15'); eid=self.db.reserve_execution(sid,{'symbol':'XAUUSD','timeframe':'M15'},'XAUUSD','M15'); self.assertIsNone(self.db.execution_orders(1)[0]['mt5_position_ticket']); self.assertEqual(self.db.execution_orders(1)[0]['final_status'],'ORDER_PENDING')
    def test_close_fields_preserve_identity(self):
        sid=self.reserve_signal('M15'); self.c.consider(signal('M15'),sid); row=self.db.execution_orders(1)[0]; self.db.close_execution(row['id'],{'close_timestamp':'2026-09-17T00:00:00+00:00','close_price':101.0,'realized_profit':1.0,'commission':-.1,'swap':0.0,'deal_ticket':3001,'order_ticket_close':4001}); closed=self.db.execution_orders(1)[0]; self.assertEqual(closed['state'],'CLOSED'); self.assertEqual(closed['signal_id'],sid); self.assertEqual(closed['mt5_deal_ticket_close'],3001)
    def test_restart_reloads_durable_linkage(self):
        sid=self.reserve_signal('M15'); self.c.consider(signal('M15'),sid); row=self.db.execution_orders(1)[0]; self.db.conn.close()
        restored=Database(Path(self.tmp.name)/'db.sqlite'); loaded=restored.execution_orders(1)[0]; self.assertEqual(loaded['signal_id'],sid); self.assertEqual(loaded['mt5_position_ticket'],2101); self.assertEqual(loaded['timeframe'],'M15'); restored.conn.close()

if __name__=='__main__': unittest.main()
