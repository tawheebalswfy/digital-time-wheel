import tempfile,unittest,time
from pathlib import Path
from backend.app.database import Database
from backend.app.execution import ExecutionController
from backend.app.config import ExecutionSettings
from backend.app.data import FeedError

class FakeMT5:
    def __init__(self,demo=True):self.demo=demo;self.sent=0
    def execution_account(self):return {'demo_confirmed':self.demo,'algo_trading_available':True,'reason':'DEMO confirmed' if self.demo else 'Connected account is not positively identified as DEMO'}
    def positions(self):return []
    def build_order(self,*args):return {'price':1,'sl':.9,'tp':1.1,'spread':.01}
    def send_order(self,r):self.sent+=1;return {'accepted':True,'sent':True,'ticket':1}

class ExecutionSafety(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.db=Database(Path(self.tmp.name)/'db.sqlite')
    def tearDown(self):self.db.conn.close();self.tmp.cleanup()
    def test_live_account_is_rejected(self):
        with self.assertRaises(FeedError):ExecutionController(self.db,FakeMT5(False)).enable()
    def test_duplicate_signal_is_reserved_once(self):
        c=ExecutionController(self.db,FakeMT5());c.enable();signal={'timeframe':'M15','direction':'BUY','timestamp':time.time(),'status':'closed-bar observation','strategy_version':'v','confidence':70,'reasons':[]};sid=self.db.log_signal({'wheel':{}},'signal-1')
        c.consider(signal,sid);c.consider(signal,sid)
        self.assertEqual(c.mt5.sent,1);self.assertEqual(len(self.db.execution_orders()),1)
    def test_restart_default_is_disabled(self):self.assertFalse(ExecutionController(self.db,FakeMT5()).enabled)
    def test_execution_settings_persist_but_enable_does_not(self):
        c=ExecutionController(self.db,FakeMT5());c.save_settings(ExecutionSettings(selected_timeframes=['H1'],fixed_lot=.02,max_trades_per_day=None,max_positions=3,cooldown_minutes=5,maximum_spread=.5));c.enable();self.db.conn.close()
        self.db=Database(Path(self.tmp.name)/'db.sqlite');restored=ExecutionController(self.db,FakeMT5())
        self.assertEqual(restored.settings.selected_timeframes,['H1']);self.assertEqual(restored.settings.fixed_lot,.02);self.assertIsNone(restored.settings.max_trades_per_day);self.assertFalse(restored.enabled)
