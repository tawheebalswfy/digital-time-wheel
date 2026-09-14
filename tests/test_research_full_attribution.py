"""Constructed-fixture correctness checks for TW-FULL-EXIT-1 only."""
from pathlib import Path
import copy,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from research_full_attribution import technical_entry,wheel_entry,technical_exit,wheel_exit,run_variant
from backend.app.config import Strategy
from backend.app.technical import features
from test_system import fixture

class FullAttribution(unittest.TestCase):
 def setUp(self):self.bars=fixture(240);self.c=Strategy(anchor_price=2000);self.row=features(self.bars,self.c).iloc[160].to_dict();self.ts=self.bars[160]['time']+60
 def test_wheel_entry_has_no_technical_indicator_dependency(self):
  expected=wheel_entry(self.row,self.c,self.ts)
  altered=copy.deepcopy(self.row)
  for k in ['ema_fast','ema_slow','sma','rsi','adx','plus_di','minus_di','macd_hist','bb_mid','atr','support','resistance','swing_high','swing_low']:altered[k]=999999 if k!='rsi'else 0
  self.assertEqual(wheel_entry(altered,self.c,self.ts),expected)
 def test_technical_exit_has_no_wheel_dependency(self):
  expected=technical_exit(self.row,self.c,self.ts,1)
  altered=self.c.model_copy(update={'anchor_price':9000,'increment':13,'harmonics':[90,180], 'clockwise':False})
  self.assertEqual(technical_exit(self.row,altered,self.ts,1),expected)
 def test_wheel_exit_needs_no_technical_columns(self):
  minimal={'close':self.row['close']}
  self.assertTrue(wheel_exit(minimal,self.c,self.ts,1)[0])
  self.assertTrue(wheel_exit(minimal,self.c,self.ts,-1)[1])
 def test_trade_rules_are_segment_bounded_and_nonoverlapping(self):
  r=run_variant(self.bars,self.c,78,220,'T','T')
  for t in r['trades']:
   self.assertLess(t['exit_index'],220)
  for a,b in zip(r['trades'],r['trades'][1:]):self.assertGreater(b['entry_time'],a['exit_time'])
 def test_no_future_data_changes_current_signal_or_exit(self):
  before=(technical_entry(self.row,self.c,self.ts),technical_exit(self.row,self.c,self.ts,1),wheel_entry(self.row,self.c,self.ts),wheel_exit(self.row,self.c,self.ts,1))
  altered=copy.deepcopy(self.bars);altered[200]['close']+=100;row=features(altered,self.c).iloc[160].to_dict()
  after=(technical_entry(row,self.c,self.ts),technical_exit(row,self.c,self.ts,1),wheel_entry(row,self.c,self.ts),wheel_exit(row,self.c,self.ts,1))
  self.assertEqual(before,after)
if __name__=='__main__':unittest.main()
