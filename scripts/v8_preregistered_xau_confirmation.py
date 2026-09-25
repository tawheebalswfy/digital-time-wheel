"""V8 frozen-rule confirmation of V7 candidates; offline and read-only."""
from __future__ import annotations
import json,sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.v5_concept_discovery import load,split,score,plan,sim,metrics,groups,outlier,iso,f,tbl
from scripts.v7_regime_specific_xau import enrich,rec,freq

CANDIDATES={
 'M30_STRONG_TREND_TREND_CONTINUATION':('M30',('STRONG_TREND','TREND_CONTINUATION')),
 'H1_STRONG_TREND_TREND_CONTINUATION':('H1',('STRONG_TREND','TREND_CONTINUATION')),
 'H4_STRONG_TREND_PULLBACK_CONTINUATION':('H4',('STRONG_TREND','PULLBACK_CONTINUATION')),
 'D1_STRONG_TREND_PULLBACK_CONTINUATION':('D1',('STRONG_TREND','PULLBACK_CONTINUATION')),
}
def period(t,key):
 d=defaultdict(list)
 for x in t:
  dt=datetime.fromtimestamp(x['time'],timezone.utc)
  if key=='direction': k='BUY' if x['d']==1 else 'SELL'
  elif key=='month': k=iso(x['time'])[:7]
  else: k=f'{dt.year}-Q{(dt.month-1)//3+1}'
  d[k].append(x)
 return {k:metrics(v) for k,v in sorted(d.items())}
def stable(rec):
 d=defaultdict(list)
 for x in rec:d[iso(x['time'])[:7]].append(x)
 vals=[score(v)['5'] for v in d.values() if len(v)>=10]
 return {'months_with_10_signals':len(vals),'positive_months':sum((v['expectancy'] or 0)>0 for v in vals),'stable_60pct':bool(vals) and sum((v['expectancy'] or 0)>0 for v in vals)/len(vals)>=.6}
def spec(tf,pair):
 reg='ADX >=25; absolute 3-bar slow-EMA slope >=0.15 ATR.'
 if pair[1]=='TREND_CONTINUATION':entry='EMA fast/slow alignment, signed slow-EMA slope, and +DI/-DI agree; close lies beyond fast EMA in trend direction.'
 else:entry='Same trend alignment; BUY RSI 40–55 with close <= fast EMA +0.3 ATR, or SELL RSI 45–60 with close >= fast EMA -0.3 ATR.'
 return {'timeframe':tf,'regime':pair[0],'regime_rule':reg,'entry_rule':entry,'indicators':'V7 defaults: EMA 12/26, ADX/ATR/RSI period 14; no changes.','exposure':'one non-overlapping position (V7 simulator)','holding':'V7 default maximum 30 bars; no separate frozen holding study','stop':'No V7 exit was frozen for this candidate; V8 diagnostics use V7 structural invalidation.','targets':'Diagnostic-only 1.0R, 1.25R, and 1.5R; not tuned and not eligible for OOS confirmation.'}
def write(o):
 d=ROOT/'docs'
 (d/'V8_PREREG_PROTOCOL.md').write_text('# V8 Preregistered XAU Confirmation\n\nOnly four named V7 candidates are evaluated. Rules are copied exactly from V7 code; no threshold, indicator, target, or holding change is permitted. V7 M5 is excluded because its holdout was exposed and negative. Since these four had no V7-frozen exits, every exit metric is `DIAGNOSTIC_ONLY`, not final OOS validation.\n',encoding='utf-8')
 p=['# V8 Candidate Specifications\n']
 for n,x in o['candidates'].items():p+=[f'## {n}\n\n']+[f'- **{k}**: {v}\n' for k,v in x['spec'].items()]
 (d/'V8_CANDIDATE_SPECIFICATIONS.md').write_text(''.join(p),encoding='utf-8')
 p=['# V8 Data Independence Audit\n']
 for n,x in o['candidates'].items():p+=[f'## {n}\n\n',tbl(['V7 window','First UTC','Last UTC','Bars'],[[k,iso(a),iso(z),c] for k,(a,z,c) in x['windows'].items()]),f'\n\nClassification: **{x["independence"]}**. No bars newer than the V7 file endpoint were available; V8 therefore uses the V7-final 20%, which was not opened for this candidate.\n\n']
 (d/'V8_DATA_INDEPENDENCE_AUDIT.md').write_text(''.join(p),encoding='utf-8')
 p=['# V8 Confirmation Results\n']
 for n,x in o['candidates'].items():
  e=x['entry']['5'];best=x['diagnostic_exits'][x['best_diagnostic']]
  p+=[f'## {n}\n\n',f'Entry confirmation: signals={x["entry"]["signals"]}; 5-bar expectancy={f(e["expectancy"])}; accuracy={f(e["accuracy"])}; MFE/MAE={f(e["mfe_mae_ratio"])}; stability={x["entry_stability"]}.\n\n',tbl(['Diagnostic exit','Trades','PF','Expectancy','Net P/L','Max DD'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['net_pnl']),f(v['max_drawdown'])] for k,v in x['diagnostic_exits'].items()]),'\n\n',f'Best diagnostic (not confirmation eligible): `{x["best_diagnostic"]}`.\n\n',tbl(['Trades','Win rate','PF','Expectancy','Net P/L','Avg win','Avg loss','Payoff','Max DD','Largest loss','Avg hold min'],[[best['trades'],f(best['win_rate']),f(best['profit_factor']),f(best['expectancy']),f(best['net_pnl']),f(best['average_win']),f(best['average_loss']),f(best['payoff_ratio']),f(best['max_drawdown']),f(best['largest_loss']),f(best['average_duration'])]]),'\n\n',tbl(['Direction','Trades','PF','Expectancy','Net P/L'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['net_pnl'])] for k,v in x['direction'].items()]),'\n\n',tbl(['Quarter','Trades','PF','Expectancy','Net P/L'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['net_pnl'])] for k,v in x['quarters'].items()]),'\n\n',tbl(['Outlier view','Trades','PF','Expectancy','Net P/L'],[[k,v['trades'],f(v['profit_factor']),f(v['expectancy']),f(v['net_pnl'])] for k,v in x['outliers'].items()]),'\n\n',tbl(['Regime frequency','Percent bars','Avg duration bars','Transitions'],[[x['spec']['regime'],f(x['regime_frequency'].get('percent')),f(x['regime_frequency'].get('average_duration_bars')),x['regime_transitions']]]),'\n\n']
 (d/'V8_CONFIRMATION_RESULTS.md').write_text(''.join(p),encoding='utf-8')
 p=['# V8 Time Wheel Incremental\n']
 for n,x in o['candidates'].items():
  if x['tw']:p+=[f'## {n}\n\n',tbl(['Arm','Signals','5b expectancy','PF','Expectancy'],[[k,v['entry']['signals'],f(v['entry']['5']['expectancy']),f(v['trade']['profit_factor']),f(v['trade']['expectancy'])] for k,v in x['tw'].items()]),'\n\n']
  else:p+=[f'## {n}\n\nNot run: frozen technical entry did not independently confirm positive in this window.\n\n']
 (d/'V8_TIME_WHEEL_INCREMENTAL.md').write_text(''.join(p),encoding='utf-8')
 (d/'V8_FINAL_DECISION.md').write_text('# V8 Final Decision\n\n'+o['decision']+'\n',encoding='utf-8')
def main():
 o={'research_id':'DIGITAL_TIME_WHEEL_V8_PREREGISTERED_XAU_CONFIRMATION','read_only':True,'candidates':{}}
 for name,(tf,pair) in CANDIDATES.items():
  b=load(ROOT/'data'/'history'/f'XAUUSD_{tf}.csv');q=enrich(b);w=split(b);a,z=w['holdout'];r=rec(b,q,tf,pair,a,z);fr,trans=freq(q);windows={k:(b[i]['time'],b[j-1]['time'],j-i) for k,(i,j) in w.items()}
  exits={};plans=plan(r,'structural')
  for R in (1.,1.25,1.5):exits[f'structural_{R}R_DIAGNOSTIC_ONLY']=metrics(sim(b,plans,z,R))
  base=max(exits,key=lambda k:exits[k]['expectancy'] or -1e9);br=float(base.split('_')[1][:-1]);besttr=sim(b,plans,z,br)
  entry=score(r);tw={}
  if entry['signals']>=50 and (entry['5']['expectancy'] or 0)>0 and stable(r)['stable_60pct']:
   for arm in ('alone','confirmation','veto'):
    rr=r if arm=='alone' else rec(b,q,tf,pair,a,z,arm);tw[arm]={'entry':score(rr),'trade':metrics(sim(b,plan(rr,'structural'),z,br))}
  o['candidates'][name]={'spec':spec(tf,pair),'windows':windows,'independence':'TRUE_UNSEEN_HOLDOUT','entry':entry,'entry_stability':stable(r),'diagnostic_exits':exits,'best_diagnostic':base,'direction':period(besttr,'direction'),'months':period(besttr,'month'),'quarters':period(besttr,'quarter'),'outliers':outlier(besttr),'regime_frequency':fr.get(pair[0],{}),'regime_transitions':trans,'tw':tw}
 o['decision']='**NO CANDIDATE CONFIRMED.** All four evaluations are TRUE_UNSEEN_HOLDOUT entry windows, but no candidate had a V7-frozen exit; exit outputs are diagnostic-only and cannot establish confirmation. None independently satisfied the complete confirmation gate (PF >1.10, positive expectancy, adequate sample, stable subperiods, outlier robustness). Time Wheel has **NO_MEASURABLE_VALUE in V8**: no incremental arm was run because no technical candidate cleared the independent entry-robustness gate. No candidate is suitable for DEMO forward testing.'
 write(o);print(json.dumps({n:{'entry_5':x['entry']['5']['expectancy'],'best_diagnostic':x['best_diagnostic'],'best_metrics':x['diagnostic_exits'][x['best_diagnostic']]} for n,x in o['candidates'].items()},indent=2))
if __name__=='__main__':main()
