import tempfile,time,unittest
from datetime import datetime,timezone
from pathlib import Path

from backend.app.database import Database
from backend.app.execution import ExecutionController


class HistoryMT5:
    """Fake MT5 history surface; it deliberately has no order-send capability."""
    def __init__(self,deals=None,positions=None):
        self.deals=deals or [];self._positions=positions or [];self.history_calls=[]
    def positions(self):return self._positions
    def history_deals(self,start,end=None):self.history_calls.append((start,end));return self.deals


class CloseLifecycleReconciliation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=Database(Path(self.tmp.name)/'db.sqlite')
    def tearDown(self):self.db.conn.close();self.tmp.cleanup()
    def execution(self,position=7001,open_time=None,comment='DTW|signal|M15'):
        sid=self.db.log_signal({'wheel':{},'symbol':'XAUUSD','timeframe':'M15'},f'event-{position}-{comment}')
        request={'symbol':'XAUUSD','timeframe':'M15','direction':'BUY','strategy_version':'v1','signal_timestamp':1000,
                 'entry_price':100.0,'request':{'symbol':'XAUUSD','comment':comment,'magic':20260910,'volume':.01,'price':100.0,'sl':99.0,'tp':101.0}}
        eid=self.db.reserve_execution(sid,request,'XAUUSD','M15')
        self.db.mark_execution_sent(eid,{'accepted':True,'mt5_order_ticket':6001,'mt5_deal_ticket_open':6002,'mt5_position_ticket':position,'open_time':open_time or datetime.fromtimestamp(1000,timezone.utc).isoformat()},'POSITION OPEN')
        return eid,sid
    def deal(self,entry=1,position=7001,stamp=1100,**more):
        return {'ticket':8001,'order':8002,'position_id':position,'entry':entry,'time':stamp,'price':101.0,'profit':1.25,'commission':-.04,'swap':.01,'volume':.01,'symbol':'XAUUSD','magic':20260910,**more}
    def row(self):return self.db.execution_orders(1)[0]
    def test_normal_close_uses_deal_position_id_and_persists_lifecycle(self):
        eid,sid=self.execution();opening=self.deal(entry=0,profit=0.0);closing=self.deal(entry=1)
        mt=HistoryMT5([opening,closing]);ExecutionController(self.db,mt).reconcile([]);row=self.row()
        self.assertEqual(row['state'],'CLOSED');self.assertEqual(row['mt5_deal_ticket_close'],8001);self.assertEqual(row['mt5_order_ticket_close'],8002)
        self.assertEqual(row['close_time'],datetime.fromtimestamp(1100,timezone.utc).isoformat());self.assertEqual(row['realized_profit'],1.25)
        self.assertAlmostEqual(row['commission'],-.08);self.assertAlmostEqual(row['swap'],.02)
        self.assertEqual(row['signal_id'],sid);self.assertEqual(row['timeframe'],'M15')
    def test_opening_deal_is_never_mistaken_for_close(self):
        self.execution();mt=HistoryMT5([self.deal(entry=0,profit=0.0)])
        ExecutionController(self.db,mt).reconcile([]);self.assertEqual(self.row()['state'],'POSITION UNKNOWN')
    def test_unknown_execution_is_retried_and_restart_finds_close(self):
        self.execution();first=ExecutionController(self.db,HistoryMT5([]));first.reconcile([]);self.assertEqual(self.row()['state'],'POSITION UNKNOWN')
        restarted=ExecutionController(self.db,HistoryMT5([self.deal(entry=1)]));restarted.reconcile([]);self.assertEqual(self.row()['state'],'CLOSED')
    def test_live_hedge_position_stays_open_using_identifier(self):
        self.execution();mt=HistoryMT5([self.deal(entry=1)],positions=[{'ticket':9000,'identifier':7001,'magic':20260910,'comment':'DTW|signal|M15'}])
        ExecutionController(self.db,mt).reconcile();self.assertEqual(self.row()['state'],'POSITION OPEN');self.assertEqual(len(mt.history_calls),0)
    def test_out_by_is_a_close_semantic(self):
        self.execution();ExecutionController(self.db,HistoryMT5([self.deal(entry=3)])).reconcile([]);self.assertEqual(self.row()['state'],'CLOSED')
    def test_wrong_position_symbol_magic_or_oversize_deal_is_not_claimed(self):
        self.execution();bad=[self.deal(position=9999),self.deal(symbol='EURUSD'),self.deal(magic=77),self.deal(volume=.02)]
        ExecutionController(self.db,HistoryMT5(bad)).reconcile([]);self.assertEqual(self.row()['state'],'POSITION UNKNOWN')
    def test_manual_or_other_ea_position_is_not_claimed(self):
        self.execution(comment='manual');mt=HistoryMT5([self.deal(entry=1)])
        ExecutionController(self.db,mt).reconcile([]);self.assertEqual(self.row()['state'],'POSITION OPEN');self.assertEqual(len(mt.history_calls),0)
    def test_impossible_close_timestamp_is_rejected_without_duplicate_row(self):
        self.execution(open_time=datetime.fromtimestamp(1200,timezone.utc).isoformat());mt=HistoryMT5([self.deal(stamp=1100)])
        ExecutionController(self.db,mt).reconcile([]);self.assertEqual(self.row()['state'],'POSITION OPEN');self.assertEqual(len(self.db.execution_orders()),1)
    def test_reconciliation_never_sends_an_order(self):
        self.execution();mt=HistoryMT5([self.deal()]);ExecutionController(self.db,mt).reconcile([])
        self.assertFalse(hasattr(mt,'send_order'))


if __name__=='__main__':unittest.main()
