"""Causal indicators and delayed-confirmed pivots; no centered future data exposed."""
import numpy as np
import pandas as pd
from .config import Strategy

FIB_RATIOS=[0,.236,.382,.5,.618,.786,1,1.272,1.618,2.618]

def features(bars,c:Strategy):
    f=pd.DataFrame(bars).copy();cl=f.close;hi=f.high;lo=f.low
    n=c.indicator_period
    f['ema_fast']=cl.ewm(span=c.ema_fast,adjust=False).mean()
    f['ema_slow']=cl.ewm(span=c.ema_slow,adjust=False).mean()
    f['sma']=cl.rolling(c.sma_period,min_periods=c.sma_period).mean()
    delta=cl.diff();gain=delta.clip(lower=0).ewm(alpha=1/n,adjust=False).mean();loss=(-delta.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    f['rsi']=100-100/(1+gain/loss.replace(0,np.nan))
    f.loc[(loss==0)&(gain>0),'rsi']=100;f.loc[(loss==0)&(gain==0),'rsi']=50
    tr=pd.concat([hi-lo,(hi-cl.shift()).abs(),(lo-cl.shift()).abs()],axis=1).max(axis=1)
    f['atr']=tr.ewm(alpha=1/n,adjust=False).mean()
    up=hi.diff();down=-lo.diff()
    plus=pd.Series(np.where((up>down)&(up>0),up,0),index=f.index).ewm(alpha=1/n,adjust=False).mean()
    minus=pd.Series(np.where((down>up)&(down>0),down,0),index=f.index).ewm(alpha=1/n,adjust=False).mean()
    f['plus_di']=100*plus/f.atr.replace(0,np.nan);f['minus_di']=100*minus/f.atr.replace(0,np.nan)
    dx=100*(plus-minus).abs()/(plus+minus).replace(0,np.nan)
    f['adx']=dx.fillna(0).ewm(alpha=1/n,adjust=False).mean()
    f['macd']=f.ema_fast-f.ema_slow;f['macd_signal']=f.macd.ewm(span=9,adjust=False).mean();f['macd_hist']=f.macd-f.macd_signal
    mid=cl.rolling(c.bb_period).mean();std=cl.rolling(c.bb_period).std(ddof=0)
    f['bb_mid']=mid;f['bb_upper']=mid+c.bb_std*std;f['bb_lower']=mid-c.bb_std*std
    f['volatility']=cl.pct_change().rolling(20).std(ddof=0)
    f['support']=lo.shift().rolling(20,min_periods=5).min();f['resistance']=hi.shift().rolling(20,min_periods=5).max()
    k=c.swing_strength
    # Compute confirmation using a trailing 2k+1 window whose middle bar is k bars ago.
    ph=hi.shift(k).where((hi.shift(k)==hi.rolling(2*k+1).max()) & (hi.shift(k)>hi.shift(k+1)))
    pl=lo.shift(k).where((lo.shift(k)==lo.rolling(2*k+1).min()) & (lo.shift(k)<lo.shift(k+1)))
    f['swing_high']=ph.ffill();f['swing_low']=pl.ffill()
    f['swing_high_time']=f.time.shift(k).where(ph.notna()).ffill();f['swing_low_time']=f.time.shift(k).where(pl.notna()).ffill()
    prior_hi=ph.dropna().shift().reindex(f.index).ffill();prior_lo=pl.dropna().shift().reindex(f.index).ffill()
    f['high_pattern']=np.where(f.swing_high>prior_hi,'HH',np.where(f.swing_high<prior_hi,'LH','—'))
    f['low_pattern']=np.where(f.swing_low>prior_lo,'HL',np.where(f.swing_low<prior_lo,'LL','—'))
    f['structure']=np.where((f.high_pattern=='HH')&(f.low_pattern=='HL'),'BULLISH',np.where((f.high_pattern=='LH')&(f.low_pattern=='LL'),'BEARISH','RANGING'))
    return f

def fibonacci(row,c,ts):
    manual=c.fib_low is not None and ts>=c.fib_anchor_time.timestamp()
    lo=c.fib_low if manual else row.get('swing_low');hi=c.fib_high if manual else row.get('swing_high')
    if lo is None or hi is None or not np.isfinite(lo) or not np.isfinite(hi) or hi<=lo:return []
    up=c.fib_direction=='up' if manual else row.get('swing_high_time',0)>row.get('swing_low_time',0)
    return [{'ratio':r,'price':float(lo+(hi-lo)*r if up else hi-(hi-lo)*r),'source':'fibonacci','formula':f'{lo if up else hi} {"+" if up else "-"} ({hi}-{lo})*{r}',
             'anchors':{'low':float(lo),'high':float(hi),'manual':manual}} for r in FIB_RATIOS]

def finite(value,default=0):
    return float(value) if value is not None and np.isfinite(value) else default
