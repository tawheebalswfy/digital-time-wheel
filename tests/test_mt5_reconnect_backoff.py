import tempfile,time,unittest
from pathlib import Path
from backend.app.data import FeedError
from backend.app.database import Database
from backend.app.service import Service

class FakeMT5:
    def __init__(self,fresh=True):
        self.fresh=fresh;self.refreshes=0;self.connected=True;self.stale_quote_count=0;self.last_stale_quote_at=None;self.last_refresh_attempt_at=None;self.refresh_backoff_seconds=0;self.last_reconnect_reason=None;self.session_health_reason='healthy'
    def refresh_session(self,reason):
        self.refreshes+=1;self.last_reconnect_reason=reason;self.last_refresh_attempt_at=time.time();return {}
    def get_current_tick(self): return {'time':time.time() if self.fresh else time.time()-121}
    def execution_account(self): return {'demo_confirmed':True}
    def positions(self): return []
    def diagnostics(self): return {}

class ReconnectBackoff(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=Database(Path(self.tmp.name)/'db.sqlite');self.service=Service(self.db);self.fake=FakeMT5();self.service.mt5=self.fake;self.service.execution.mt5=self.fake;self.service.provider='MT5';self.service.execution.reconcile_periodic=lambda:None
    def tearDown(self):self.db.conn.close();self.tmp.cleanup()
    def fail_collect(self,message):
        def fail():raise FeedError(message)
        self.service._collect=fail
    def test_connected_stale_quote_never_refreshes_session_loop(self):
        self.fail_collect('Quote is stale; MT5 session refresh required')
        self.service.poll();self.service.poll();self.service.poll()
        self.assertEqual(self.fake.refreshes,0);self.assertEqual(self.fake.stale_quote_count,3);self.assertEqual(self.fake.session_health_reason,'stale_quote');self.assertGreaterEqual(self.fake.refresh_backoff_seconds,1)
    def test_disconnected_session_refreshes_and_fresh_quote_clears_backoff(self):
        self.fail_collect('MT5 disconnected')
        self.service.poll()
        self.assertEqual(self.fake.refreshes,1);self.assertEqual(self.service._reconnect_index,0);self.assertEqual(self.fake.refresh_backoff_seconds,0);self.assertEqual(self.fake.session_health_reason,'healthy')
    def test_initialized_but_still_stale_does_not_reset_retry_loop(self):
        self.fake.fresh=False;self.fail_collect('MT5 disconnected')
        self.service.poll();self.service.poll()
        self.assertEqual(self.fake.refreshes,1);self.assertEqual(self.fake.session_health_reason,'stale_quote_after_refresh');self.assertGreaterEqual(self.fake.refresh_backoff_seconds,1);self.assertGreaterEqual(self.service._reconnect_index,1)
    def test_fresh_collection_clears_prior_stale_backoff(self):
        self.fail_collect('Quote is stale; MT5 session refresh required');self.service.poll()
        self.service._collect=lambda:{'tick':{'bid':1,'ask':1}}
        self.service.poll()
        self.assertEqual(self.service._reconnect_index,0);self.assertEqual(self.fake.refresh_backoff_seconds,0);self.assertEqual(self.fake.session_health_reason,'healthy')

if __name__=='__main__':unittest.main()
