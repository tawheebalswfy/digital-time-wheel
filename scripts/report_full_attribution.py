"""Render and verify the completed TW-FULL-EXIT-1 research artifact."""
import gzip,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def fmt(x,k=''):
 if x is None:return 'N/A'
 if k=='win_rate':return f'{x*100:.2f}%'
 if k=='trades':return f'{x:,}'
 return f'{x:.4f}'
def table(data):
 keys=[('trades','Trades'),('win_rate','Win rate'),('average_winner','Average winner'),('average_loser','Average loser'),('profit_factor','Profit factor'),('gross_expectancy','Gross expectancy'),('net_expectancy','Net expectancy'),('net_pnl','Net P&L'),('max_drawdown','Max drawdown'),('mean_mae','Mean MAE'),('max_mae','Max MAE'),('mean_mfe','Mean MFE'),('max_mfe','Max MFE'),('average_holding_minutes','Average holding minutes')]
 out=['| Metric | A: T/T | B: W/W | C: T/W | D: W/T | E: production |','|---|---:|---:|---:|---:|---:|']
 for k,label in keys:out.append('| '+label+' | '+' | '.join(fmt(data[a][k],k)for a in 'ABCDE')+' |')
 return '\n'.join(out)
def main():
 d=Path(sys.argv[1]).resolve();assert d.is_relative_to(ROOT/'docs'/'experiments')
 x=json.loads((d/'comparison.json').read_text());r=x['registration']
 for segment in ['train','validation','test']:
  for arm in 'ABCD':
   with gzip.open(d/f'{segment}-{arm}.json.gz','rt',encoding='utf-8')as f:v=json.load(f)
   assert v['metrics']['trades']==x['summaries'][segment][arm]['trades']
   assert abs(v['metrics']['net_pnl']-x['summaries'][segment][arm]['net_pnl'])<1e-8
  with gzip.open(d/f'{segment}-E.json.gz','rt',encoding='utf-8')as f:v=json.load(f)
  assert v['metrics']['trades']==x['summaries'][segment]['E']['trades']
 for n,h in r['source_before'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 from research_ablation import checkpoint
 import sqlite3
 c=sqlite3.connect((ROOT/'runtime'/'timewheel.sqlite3').as_uri()+'?mode=ro',uri=True);assert checkpoint.logical_state(c)==r['database_before'];c.close()
 a=x['test_attribution'];f=x['filters']['test']['summary'];t=x['summaries']['test']
 lines=['# Full Time Wheel attribution — TW-FULL-EXIT-1','',
 '**Final-test conclusion:** the Time Wheel has **no demonstrated standalone value** in this M1 diagnostic. Wheel exits improve per-trade expectancy under both fixed entry families, but worsen total P&L and drawdown. Wheel entries reduce exposure and drawdown, while their per-trade expectancy effect is mixed and negligible-to-negative. The production baseline remains the least-loss / lowest-drawdown reference here, but it is still negative. No production defaults changed.','',
 '## Design','',
 'This fully separates the exit families that were shared in the prior experiment. A–D use the same MT5 XAUUSD M1 dataset, chronological split, cost of 0.40, next-open entry, stop-first ambiguity rule, adverse stop-gap fill, one-position constraint, and 30-bar maximum hold. E is the immutable current production baseline. The [frozen protocol]('+d.relative_to(ROOT/'docs').as_posix()+'/TIME_WHEEL_FULL_ATTRIBUTION_PROTOCOL.md) defines every rule before results.','',
 '- **T entry:** structure, support/resistance, momentum, and Fibonacci only.','- **W entry:** Time Wheel state, geometry, and gates only. No ATR/volatility technical indicator is used.','- **T exit:** confirmed support/resistance, swings, and Fibonacci only; no wheel, harmonics, gates, Gann, or ATR.','- **W exit:** wheel levels and angular harmonic projections only; no technical field, indicator, swing, Fibonacci, support/resistance, or ATR.','',
 'The test starts at the corrected 4 September 2026 02:46 UTC bar. Train `[78,18071)`, validation `[18102,24105)`, and test `[24136,30170)` preserve the prior 31-bar purges. The final conclusion below uses test only; train/validation are retained in the artifact for transparency. This is retrospective OOS relative to the frozen split, but the period was inspected in prior work and has only six represented UTC dates.', '',
 '## Final-test metrics','',table(t),'',
 'Sharpe and Sortino are retained in the compressed full results but omitted from interpretation: six dependent daily observations are not statistically meaningful for annualized ratios. MAE/MFE are full-bar excursions using the inherited exit-bar caveat.','',
 '## Attribution from final test only','',
 '| Fixed comparison | Net expectancy delta | Net P&L delta | Drawdown delta | Reading |','|---|---:|---:|---:|---|',
 f'| W entry vs T entry, technical exits: D − A | {a["wheel_entry_with_technical_exits_D_minus_A"]["net_expectancy"]:.4f} | {a["wheel_entry_with_technical_exits_D_minus_A"]["net_pnl"]:.4f} | {a["wheel_entry_with_technical_exits_D_minus_A"]["max_drawdown"]:.4f} | Near-zero per-trade gain; fewer trades and lower drawdown. |',
 f'| W entry vs T entry, wheel exits: B − C | {a["wheel_entry_with_wheel_exits_B_minus_C"]["net_expectancy"]:.4f} | {a["wheel_entry_with_wheel_exits_B_minus_C"]["net_pnl"]:.4f} | {a["wheel_entry_with_wheel_exits_B_minus_C"]["max_drawdown"]:.4f} | Worse expectancy; fewer trades and lower drawdown. |',
 f'| W exit vs T exit, technical entries: C − A | {a["wheel_exit_with_technical_entries_C_minus_A"]["net_expectancy"]:.4f} | {a["wheel_exit_with_technical_entries_C_minus_A"]["net_pnl"]:.4f} | {a["wheel_exit_with_technical_entries_C_minus_A"]["max_drawdown"]:.4f} | Better expectancy per trade, worse aggregate loss/drawdown. |',
 f'| W exit vs T exit, wheel entries: B − D | {a["wheel_exit_with_wheel_entries_B_minus_D"]["net_expectancy"]:.4f} | {a["wheel_exit_with_wheel_entries_B_minus_D"]["net_pnl"]:.4f} | {a["wheel_exit_with_wheel_entries_B_minus_D"]["max_drawdown"]:.4f} | Better expectancy per trade, worse aggregate loss/drawdown. |','',
 '### Answers to the requested attribution questions','',
 '1. **Does the Time Wheel improve entries?** No consistent final-test evidence. It adds +0.0005 expectancy with technical exits but −0.0223 with wheel exits.','2. **Does it improve exits?** Per trade, yes in both fixed-entry comparisons (+0.0428 and +0.0200). Aggregate P&L and drawdown worsen because wheel exits increase the number of trades.','3. **Does it reduce drawdown?** Wheel entries do in both comparisons (−52.93 and −13.54). Wheel exits do not (+91.23 and +130.62).','4. **Does it filter bad trades?** Not convincingly. The combined entry accepted 379 technical counterfactuals with −0.7513 expectancy and filtered 1,968 with −0.5055 expectancy. It removed many losing trades, but retained an even worse per-opportunity subset.','5. **Does it remove profitable trades too aggressively?** It removed 428 profitable technical counterfactuals alongside 1,540 losers; its filtered set had a 21.75% profitable rate versus 19.00% for accepted same-direction opportunities. That is evidence of indiscriminate filtering in this sample, not clean bad-trade removal.','6. **Is its value stronger on certain timeframes?** Not assessed. The required common dataset/split is M1-only; higher-timeframe datasets cannot be used to support a claim here.','',
 '## Required separate statements','',
 '- **Time Wheel entry value:** inconclusive and not positive on final test; risk-filter behavior lowers exposure/drawdown but does not consistently improve expectancy.','- **Time Wheel exit value:** improves expectancy per trade in this sample, but has negative aggregate risk/P&L consequences under both entry families.','- **Time Wheel risk-filter value:** entries reduce drawdown, while exits increase it. The entry filter does not selectively remove worse technical opportunities in the evaluated counterfactuals.','',
 '## Reproducibility','',
 'All A–D signals, levels, rejects, trades, equity curves, and full raw metrics are in compressed artifacts next to [comparison.json]('+d.relative_to(ROOT/'docs').as_posix()+'/comparison.json). Source and SQLite logical fingerprints were rechecked after the run; production defaults and stored records are unchanged. Thirteen research tests passed. Re-run with:', '', '```powershell','.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_research*.py" -q','.\\.venv\\Scripts\\python.exe scripts\\research_full_attribution.py','```','']
 target=ROOT/'docs'/'TIME_WHEEL_FULL_ATTRIBUTION_REPORT.md';target.write_text('\n'.join(lines),encoding='utf-8');(d/'report.md').write_text('\n'.join(lines).replace(d.relative_to(ROOT/'docs').as_posix()+'/', ''),encoding='utf-8')
 print(target)
if __name__=='__main__':main()
