import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from research_higher_timeframes import SPECS,run
from backend.app.config import Strategy
from test_system import fixture

class HigherTimeframeProtocol(unittest.TestCase):
 def test_frozen_boundaries_preserve_warmup_and_purges(self):
  for _,(_,b)in SPECS.items():
   self.assertGreaterEqual(b['train'][0],78);self.assertEqual(b['validation'][0]-b['train'][1],31);self.assertEqual(b['test'][0]-b['validation'][1],31)
   self.assertGreater(b['train'][1]-b['train'][0],31);self.assertGreater(b['validation'][1]-b['validation'][0],31);self.assertGreater(b['test'][1]-b['test'][0],31)
 def test_generic_runner_keeps_bar_boundaries(self):
  bars=fixture(220)
  for i,b in enumerate(bars):b['time']=i*900
  r=run(bars,Strategy(anchor_price=2000), 'M15',78,200,'T','T')
  for t in r['trades']:
   self.assertLess(t['exit_index'],200);self.assertEqual((t['exit_time']-t['entry_time'])%900,0)
if __name__=='__main__':unittest.main()
