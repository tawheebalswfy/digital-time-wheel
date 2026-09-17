import json
from pathlib import Path

d = json.loads(Path('runtime/cooldown_walk_forward.json').read_text())
x = d['symbols']['XAUUSD']
names = ['baseline','cooldown_60s','cooldown_120s','cooldown_180s','cooldown_300s','cap_1','cap_2','cooldown_60s_cap_1','cooldown_120s_cap_1','cooldown_300s_cap_1']
def f(v): return '—' if v is None else f'{v:.3f}'
lines = ['# Cooldown Walk-Forward Report','', 'This report evaluates only execution-risk filters around the existing strategy. Auto trading remained disabled and no MT5 order was sent. The forensic week was excluded.', '', '## Data status', '', '- Genuine MT5 XAUUSD data: 2026-08-11 through 2026-09-10 UTC, causally resampled to M1/M5/M15/M30/H1.', '- BTCUSD and EURUSD history for non-overlapping windows was unavailable from the saved database and direct read-only MT5 history request; no synthetic data was substituted.', '- H4/D1 are not included because the available sample is insufficient for a reliable separate holdout.', '', '## Aggregate candidate metrics', '', '| Window | Variant | Trades | Wins | Losses | Win rate | Gross profit | Gross loss | Net P/L | PF | Expectancy | Avg win | Avg loss | Max DD | Max loss | Max exposure | Blocked |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for w in ['discovery','validation','holdout']:
    for n in names:
        m=x[w][n]
        lines.append(f"| {w} | {n} | {m['trades']} | {m['wins']} | {m['losses']} | {m['win_rate']*100:.1f}% | {m['gross_profit']:.2f} | {m['gross_loss']:.2f} | {m['net_pnl']:.2f} | {f(m['profit_factor'])} | {f(m['expectancy'])} | {f(m['average_win'])} | {f(m['average_loss'])} | {m['max_drawdown']:.2f} | {m['max_single_loss']:.2f} | {m['max_simultaneous_same_direction_exposure']} | {m['blocked_entries']} |")
lines += ['', '## XAUUSD BUY / SELL attribution', '', '| Window | Variant | BUY trades | BUY net | BUY PF | BUY expectancy | SELL trades | SELL net | SELL PF | SELL expectancy |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for w in ['validation','holdout']:
    for n in ['baseline','cap_1','cooldown_60s','cooldown_300s','cooldown_60s_cap_1']:
        m=x[w][n]; b=m['buy']; s=m['sell']
        lines.append(f"| {w} | {n} | {b['trades']} | {b['net_pnl']:.2f} | {f(b['profit_factor'])} | {f(b['expectancy'])} | {s['trades']} | {s['net_pnl']:.2f} | {f(s['profit_factor'])} | {f(s['expectancy'])} |")
lines += ['', '## Holdout by timeframe', '', '| Variant | M1 trades/net/PF | M5 trades/net/PF | M15 trades/net/PF | M30 trades/net/PF | H1 trades/net/PF |', '|---|---|---|---|---|---|']
for n in names:
    m=x['holdout'][n]; cells=[]
    for tf in ['M1','M5','M15','M30','H1']:
        q=m['by_timeframe'][tf]; cells.append(f"{q['trades']} / {q['net_pnl']:.2f} / {f(q['profit_factor'])}")
    lines.append('| '+n+' | '+' | '.join(cells)+' |')
lines += ['', '## Holding time', '', 'Holdout duration buckets for the frozen validation candidate (`cap_1`). No time-based exit was added.', '', '| Bucket | Trades | Win rate | Net P/L | PF | Expectancy |', '|---|---:|---:|---:|---:|---:|']
for k,m in x['holdout']['cap_1']['holding_buckets'].items(): lines.append(f"| {k} | {m['trades']} | {m['win_rate']*100:.1f}% | {m['net_pnl']:.2f} | {f(m['profit_factor'])} | {f(m['expectancy'])} |")
lines += ['', '## Walk-forward decision', '', 'The validation freeze is `cap_1` because it had the strongest available XAUUSD validation PF and expectancy among the fixed candidates. On the XAUUSD holdout it improved PF from 0.491 to 0.551, expectancy from -0.535 to -0.426, and max drawdown from 439.56 to 289.14. The result remains negative and is based on one symbol, so it does not satisfy the multi-symbol support rule.', '', '**Conclusion:** improvement replicated on the available XAUUSD holdout, but evidence is insufficient to promote a production default. Production defaults remain unchanged.', '', '## Required next step', '', 'Acquire non-overlapping genuine MT5 history for BTCUSD and EURUSD, rerun the frozen candidate set, and forward-test `cap_1` as an optional DEMO setting only if the multi-symbol validation and holdout criteria pass.']
Path('docs/COOLDOWN_WALK_FORWARD_REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')

if __name__ == '__main__':
    print('wrote docs/COOLDOWN_WALK_FORWARD_REPORT.md')
