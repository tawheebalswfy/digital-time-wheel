import tempfile, unittest, time
from pathlib import Path
from backend.app.database import Database
from backend.app.execution import ExecutionController
from backend.app.config import ExecutionSettings

class PositionsMT5:
    def __init__(self): self.sent=0
    def execution_account(self): return {'demo_confirmed':True,'algo_trading_available':True,'reason':'DEMO confirmed','hedging_supported':True}
    def positions(self):
        return [
            {'ticket':11,'type':'BUY','magic':20260910,'comment':'DTW|system|M15','volume':.01},
            {'ticket':12,'type':'SELL','magic':0,'comment':'manual','volume':.01},
            {'ticket':13,'type':'BUY','magic':777,'comment':'OtherEA','volume':.01},
        ]

class Preflight(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=Database(Path(self.tmp.name)/'db.sqlite')
    def tearDown(self): self.db.conn.close(); self.tmp.cleanup()
    def test_same_candle_identity_is_deterministic_and_timeframe_scoped(self):
        base={'wheel':{},'symbol':'XAUUSD','timeframe':'M1','timestamp':1700000000,'strategy_version':'v1'}
        a=self.db.log_signal(base,'MT5|XAUUSD|M1|v1|1700000000'); b=self.db.log_signal(base,'MT5|XAUUSD|M1|v1|1700000000')
        c=self.db.log_signal({**base,'timeframe':'M5'},'MT5|XAUUSD|M5|v1|1700000000'); d=self.db.log_signal({**base,'timestamp':1700000060},'MT5|XAUUSD|M1|v1|1700000060')
        self.assertEqual(a,b); self.assertNotEqual(a,c); self.assertNotEqual(a,d)
    def test_schema_read_path_has_linkage_fields(self):
        required={'id','signal_id','symbol','timeframe','candle_time','direction','strategy_version','magic_number','mt5_order_ticket','mt5_deal_ticket_open','mt5_position_ticket','mt5_deal_ticket_close','mt5_order_ticket_close','mt5_comment','volume','entry_price','stop_loss','take_profit','open_time','close_time','realized_profit','commission','swap','final_status'}
        cols={r[1] for r in self.db.conn.execute('pragma table_info(execution_orders)')}; self.assertTrue(required<=cols)
    def test_manual_and_other_ea_positions_are_external(self):
        c=ExecutionController(self.db,PositionsMT5()); s=c.status(); self.assertEqual({p['ticket'] for p in s['owned_positions']},{11}); self.assertEqual({p['ticket'] for p in s['external_positions']},{12,13})

if __name__=='__main__': unittest.main()
