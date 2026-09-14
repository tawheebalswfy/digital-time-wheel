import tempfile,time,unittest
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from backend.app.time_normalization import normalize_broker_time,offset_seconds,timestamp_audit,validate_not_future
from backend.app.data import MT5Adapter,FeedError
from backend.app.config import FeedSettings,Strategy
from backend.app.database import Database
from backend.app.service import Service

class BrokerTime(unittest.TestCase):
    def adapter(self,delta=10800,bid=4400.,ask=4400.2):
        now=int(time.time());a=MT5Adapter();a.mt5=Mock();a.connected=True;a.symbol='XAUUSD';a.timestamp_offset_seconds=10800
        a.mt5.symbol_info_tick.return_value=SimpleNamespace(time=now+delta,time_msc=(now+delta)*1000+123,bid=bid,ask=ask,volume=1)
        return a,now
    def test_utc_plus_three_preserves_raw(self):
        a,now=self.adapter();t=a.get_current_tick()
        self.assertEqual(t['time'],now);self.assertEqual(t['raw_time'],now+10800)
        self.assertEqual(t['time_msc'],now*1000+123)
        self.assertEqual(t['broker_utc_offset'],'+03:00')
        self.assertEqual(datetime.fromisoformat(t['normalized_utc_time']).utcoffset().total_seconds(),0)
        self.assertEqual(datetime.fromisoformat(t['broker_time']).timestamp(),now)
        self.assertAlmostEqual(t['spread'],.2)
    def test_future_guard_runs_after_normalization(self):
        a,now=self.adapter();self.assertEqual(a.get_current_tick()['time'],now)
        a.timestamp_offset_seconds=0
        with self.assertRaises(FeedError):a.get_current_tick()
        a,now=self.adapter(delta=11000)
        with self.assertRaises(FeedError):a.get_current_tick()
    def test_stale_time_is_not_automatically_shifted_to_now(self):
        a,now=self.adapter(delta=10800-600)
        self.assertEqual(now-a.get_current_tick()['time'],600)
    def test_invalid_quotes_rejected(self):
        for bid,ask in [(0,1),(4400,4399),(float('nan'),4400),(4400,float('inf'))]:
            a,_=self.adapter(bid=bid,ask=ask)
            with self.assertRaises(FeedError):a.get_current_tick()
    def test_bar_conversion_and_history_query_boundaries(self):
        a,now=self.adapter();start=(now//60-10)*60;end=start+120
        rows=[dict(time=start+10800+i*60,open=4400,high=4401,low=4399,close=4400,tick_volume=10) for i in range(3)]
        a.mt5.copy_rates_range.return_value=rows;a.mt5.TIMEFRAME_M1=1
        result=a.get_historical_data('M1',datetime.fromtimestamp(start,timezone.utc),datetime.fromtimestamp(end,timezone.utc))
        self.assertEqual([r['time'] for r in result],[start,start+60])
        self.assertEqual(result[0]['original_broker_timestamp'],start+10800)
        args=a.mt5.copy_rates_range.call_args.args
        self.assertEqual(args[2].timestamp(),start+10800);self.assertEqual(args[3].timestamp(),end+10800)
    def test_offsets_are_explicit(self):
        self.assertEqual(offset_seconds('+03:00'),10800);self.assertEqual(offset_seconds('-05:30'),-19800)
        self.assertEqual(FeedSettings().broker_utc_offset,'+00:00')
        for value in ['3','+24:00','+03:99']:
            with self.assertRaises(ValueError):offset_seconds(value)
    def test_connect_and_shutdown_are_idempotent(self):
        a,_=self.adapter();a.mt5.symbol_info.return_value=SimpleNamespace(name='XAUUSD',digits=2,point=.01,description='Gold')
        for _ in range(4):a.connect_mt5('XAUUSD',timestamp_offset_seconds=10800)
        a.mt5.initialize.assert_not_called()
        for _ in range(4):a.disconnect_mt5()
        a.mt5.shutdown.assert_called_once();self.assertEqual(a.shutdown_calls,1)

class CollectionOwnership(unittest.TestCase):
    def test_snapshot_consumers_do_not_poll_or_initialize(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Database(Path(directory)/'data.sqlite');service=Service(db)
            service.mt5.get_current_tick=Mock(side_effect=AssertionError('consumer must not poll'))
            service.mt5.connect_mt5=Mock(side_effect=AssertionError('consumer must not initialize'))
            for _ in range(100):service.snapshot()
            self.assertEqual(service.poll_count,0)
            db.conn.close()
    def test_feed_profile_persists_separately_from_analysis_zone(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Database(Path(directory)/'data.sqlite');service=Service(db)
            service.configure(Strategy(timezone='Asia/Aden'))
            service.set_feed_settings(FeedSettings(broker_utc_offset='+03:00'))
            restored=Service(db)
            self.assertEqual(restored.config.timezone,'Asia/Aden')
            self.assertEqual(restored.feed_settings.broker_utc_offset,'+03:00')
            self.assertEqual(restored.feed_settings.auto_connect,False)
            db.conn.close()
