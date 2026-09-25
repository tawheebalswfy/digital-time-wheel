"""Read-only acquisition of XAUUSD H4/D1 for V6; contains no trading APIs."""
import csv, shutil
from datetime import datetime, timezone
from pathlib import Path
import MetaTrader5 as mt5

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'history'; SYMBOL='XAUUSD'; FIELDS=['time','open','high','low','close','tick_volume','spread','real_volume']
def iso(t):return datetime.fromtimestamp(int(t),timezone.utc).isoformat()
def rows(raw):return [] if raw is None else [{k:(r[k].item() if hasattr(r[k],'item') else r[k]) for k in raw.dtype.names} for r in raw]
def get(tf):
 constant=getattr(mt5,'TIMEFRAME_'+tf);all=[];audit=[]
 for page in range(20):
  pos=page*50000;raw=mt5.copy_rates_from_pos(SYMBOL,constant,pos,50000);x=rows(raw);audit.append({'position':pos,'requested':50000,'returned':len(x),'first_utc':iso(x[0]['time']) if x else None,'last_utc':iso(x[-1]['time']) if x else None,'last_error':list(mt5.last_error())})
  if not x:break
  all+=x
  if len(x)<50000:break
 unique={int(x['time']):x for x in all};return [unique[k] for k in sorted(unique)],audit
def main():
 if not mt5.initialize(timeout=10000):raise RuntimeError(mt5.last_error())
 try:
  if not mt5.symbol_select(SYMBOL,True):raise RuntimeError(mt5.last_error())
  for tf in ('H4','D1'):
   data,audit=get(tf);path=OUT/f'XAUUSD_{tf}.csv'
   if path.exists():shutil.copy2(path,path.with_name(f'{path.stem}.backup_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}{path.suffix}'))
   with path.open('w',newline='',encoding='utf-8') as h:
    w=csv.DictWriter(h,fieldnames=FIELDS,extrasaction='ignore');w.writeheader();w.writerows(data)
   print({'tf':tf,'candles':len(data),'first_utc':iso(data[0]['time']) if data else None,'last_utc':iso(data[-1]['time']) if data else None,'audit':audit})
 finally:mt5.shutdown()
if __name__=='__main__':main()
