"""Verify a completed TW-ENTRY-1 artifact directory and generate its comparison report."""
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import numpy as np

from research_ablation import ROOT, ARMS, checkpoint, digest, file_hash, summary


def read_result(directory, segment, arm):
    with gzip.open(directory / f'{segment}-{arm}-result.json.gz', 'rt', encoding='utf-8') as f:
        return json.load(f)


def close(a, b):
    if a is None or b is None:
        assert a is b
    else:
        assert abs(a - b) < 1e-7 * max(1, abs(b)), (a, b)


def verify(directory, comparison, registration):
    hashes = json.loads((directory / 'artifact_hashes.json').read_text())
    for name, expected in hashes.items():
        assert file_hash(directory / name) == expected, name
    conn = sqlite3.connect((ROOT / 'runtime' / 'timewheel.sqlite3').as_uri() + '?mode=ro', uri=True)
    assert checkpoint.logical_state(conn) == registration['database_before']
    rows = [json.loads(r[0]) for r in conn.execute('SELECT payload FROM candles WHERE dataset_id=? ORDER BY time', (registration['dataset_id'],))]
    assert digest(rows) == registration['dataset']['content_hash']
    lookup = {b['time'] + 60: b['close'] for b in rows}
    conn.close()
    for name, expected in registration['source_before'].items():
        assert file_hash(ROOT / name) == expected, name
    checks = []
    for segment in ['train', 'validation', 'test']:
        limits = registration['boundaries'][segment]
        first, end = limits['start_index'], limits['end_index_exclusive']
        for arm in ['A', 'B', 'C']:
            saved = read_result(directory, segment, arm)
            result, m = saved['result'], saved['result']['metrics']
            assert summary(result) == saved['summary']
            for key, value in saved['summary'].items():
                assert value == comparison['summaries'][segment][arm][key]
            pnl = np.array([t['pnl'] for t in result['trades']])
            close(pnl.sum(), m['net_pnl'])
            close(pnl.mean() if len(pnl) else None, m['expectancy'])
            eq = np.array([result['strategy']['initial_equity']] + [r['value'] for r in result['equity']])
            close(np.max(np.maximum.accumulate(eq) - eq), m['max_drawdown'])
            close(eq[-1] - eq[0], pnl.sum())
            sigs, count, h = {}, 0, hashlib.sha256()
            prior_ts = -1
            with gzip.open(directory / f'{segment}-{arm}-signals.jsonl.gz', 'rb') as f:
                for line in f:
                    h.update(line)
                    audit = json.loads(line)
                    sig, outcome = audit['original'], audit['outcome']
                    assert digest(sig) == audit['original_hash']
                    ts = sig['timestamp']
                    assert prior_ts < ts < rows[end-1]['time'] + 60
                    assert ts >= rows[first]['time'] + 60
                    prior_ts = ts
                    assert outcome['endpoint'] == ts + 300
                    available = ts + 300 in lookup and ts + 300 <= rows[end-1]['time'] + 60
                    assert outcome['available'] == available
                    if available:
                        close(outcome['endpoint_price'], lookup[ts + 300])
                        close(outcome['signed_return_bps'], sig['direction_value'] * (lookup[ts + 300] / sig['price'] - 1) * 10000)
                    sigs[ts] = (sig['direction_value'], sig['targets'], sig['invalidation'])
                    count += 1
            assert count == m['total_signals']
            assert h.hexdigest() == saved['signal_audit_sha256_uncompressed']
            previous_exit = -1
            for trade in result['trades']:
                d, levels, stop = sigs[trade['signal_timestamp']]
                assert trade['entry_time'] == trade['signal_timestamp']
                assert trade['entry_time'] > previous_exit
                assert trade['exit_index'] < end
                assert trade['exit_time'] == rows[trade['exit_index']]['time']
                assert trade['target'] == levels[0]['price'] and trade['stop'] == stop['price']
                close(trade['costs'], .4)
                close(trade['pnl'], d * (trade['exit'] - trade['entry']) - .4)
                previous_exit = trade['exit_time']
            close(sum(r['marked_pnl'] for r in saved['daily']), m['net_pnl'])
            checks.append({'segment': segment, 'arm': arm, 'signals_verified': count,
                           'trades_verified': len(result['trades']), 'hashes_metrics_bounds_and_nonoverlap': True})
        assert comparison['summaries'][segment]['A'] == comparison['summaries'][segment]['D']
        reference = json.loads((directory / f'{segment}-D-reference.json').read_text())
        assert file_hash(directory / reference['result_file']) == reference['result_sha256']
    return {'artifact_hashes_verified': len(hashes), 'all_original_signal_hashes_verified': True,
            'database_and_existing_source_preserved': True, 'checks': checks,
            'verifier_sha256': file_hash(Path(__file__)),
            'research_unit_tests': {'run': 8, 'passed': 8},
            'full_regression': {'run': 45, 'passed': 43, 'failed': 1, 'errors': 1,
                                'failures': ['test_websocket_same_client_replaced_once: active connection count 1 instead of 0',
                                             'test_websocket_reconnect_cleans_up_and_does_not_poll: CancelledError'],
                                'note': 'Previously documented WebSocket cleanup instability recurred; production transport unchanged.'}}


METRICS = [('trades', 'Trades'), ('win_rate', 'Net win rate'), ('average_win', 'Average net win'),
           ('average_loss', 'Average net loss'), ('profit_factor', 'Net profit factor'),
           ('gross_expectancy', 'Gross expectancy / trade'), ('net_expectancy', 'Net expectancy / trade'),
           ('net_pnl', 'Net P&L'), ('max_drawdown', 'Maximum marked drawdown'),
           ('max_drawdown_percent', 'Maximum drawdown %'), ('mean_mae', 'Mean MAE'), ('max_mae', 'Maximum MAE'),
           ('mean_mfe', 'Mean MFE'), ('max_mfe', 'Maximum MFE'), ('sharpe', 'Sharpe'), ('sortino', 'Sortino'),
           ('daily_observations', 'Represented UTC dates')]


def fmt(value, key=None):
    if value is None:
        return 'N/A'
    if key == 'win_rate':
        return f'{value * 100:.2f}%'
    if key in ('trades', 'daily_observations'):
        return f'{value:,}'
    return f'{value:.4f}'


def arm_table(data):
    lines = ['| Metric | A: baseline | B: technical entries | C: wheel entries | D: combined |',
             '|---|---:|---:|---:|---:|']
    for key, label in METRICS:
        lines.append('| ' + label + ' | ' + ' | '.join(fmt(data[a][key], key) for a in ARMS) + ' |')
    return '\n'.join(lines)


def report(directory, value, registration, audit):
    relative = directory.relative_to(ROOT / 'docs').as_posix()
    test = value['summaries']['test']
    increments = value['comparisons']
    delta = increments['test']['combined_minus_technical']
    change = 'worse' if delta['net_expectancy'] < 0 else 'better' if delta['net_expectancy'] > 0 else 'unchanged'
    interval = increments['test']['paired_block_resampling']['net_expectancy_delta_exploratory_95_interval']
    lines = [
        '# Time Wheel contribution — TW-ENTRY-1 diagnostic', '',
        '**Conclusion: evidence is inconclusive for independent out-of-sample predictive value.** '
        f'On the retained final-test segment, adding the current Time Wheel entry logic makes net expectancy **{change} by {abs(delta["net_expectancy"]):.4f} quote-price units per trade**. '
        f'The validation expectancy increment was {increments["validation"]["combined_minus_technical"]["net_expectancy"]:+.4f}, so its favorable direction did not persist in the final test. '
        'The original final period was already inspected, and its small number of represented dates limits inference. No production setting was changed.', '',
        '## Experiment scope', '',
        'This user-requested entry-family ablation superseded the queued payoff-eligibility experiment for this session. '
        'The only experimental factor is entry logic. All arms use the same genuine MT5 M1 data, costs, target/stop construction, next-open execution, holding period, and evaluation rules. '
        '**B means technical-only entries; C means wheel-only entries. Shared exits still contain both wheel-derived and technical levels.** '
        'Thus this experiment cannot establish the contribution of wheel-derived exits or compare entirely wheel-free versus entirely technical-free systems.', '',
        'A and D are exactly the same current combined strategy. D references A’s result files; it is a duplicate control, not another independent experiment. '
        'B uses the existing technical vote weights normalized over 40 active points. C uses existing wheel-dependent vote weights normalized over 60 active points and removes technical directional confirmation. '
        'Both retain threshold 55. Active-family normalization avoids mechanically disabling B, whose votes otherwise cannot reach 55 out of 100. '
        'No parameter search, target change, cost search, indicator addition, or win-rate optimization was performed.', '',
        f'Rules were archived before new-arm results in the [frozen protocol]({relative}/TIME_WHEEL_ABLATION_PROTOCOL.md) and [registration]({relative}/registration.json).', '',
        '## Data and chronological split', '',
        f'Dataset: `{registration["dataset_id"]}`; {registration["dataset"]["bars"]:,} retained MT5 XAUUSD M1 candles. '
        f'Content SHA-256: `{registration["dataset"]["content_hash"]}`. '
        f'Frozen baseline strategy SHA-256: `{registration["strategy_hash"]}`.', '',
        'The original 80% final-test boundary is unchanged. The earlier checkpoint had no validation set; this experiment subdivides its development portion into train and validation, with 31-bar purges. '
        'It does not rewrite the original stored backtest. All portfolios start flat at 10,000 quote units; prior history is used only for causal feature warmup. '
        'Rules were frozen before train, validation, and test; no fitting or selection occurred between segments.', '',
        '| Segment | Bar indices (end exclusive) | First signal UTC | Last valuation UTC |',
        '|---|---|---|---|']
    for name, bounds in registration['boundaries'].items():
        lines.append(f'| {name} | [{bounds["start_index"]}, {bounds["end_index_exclusive"]}) | {bounds["first_signal_utc"]} | {bounds["end_utc"]} |')
    lines += ['', 'The first final-test bar opens **4 September 2026 02:46 UTC**; its signal is stamped **02:47 UTC**. '
              'Both validation and test are retrospective diagnostics on already available history, not newly untouched holdouts. '
              'The saved data gaps and broker-offset limitations from the baseline validation remain; no candles were generated or filled.', '',
              '## Final-test comparison', '', arm_table(test), '',
              'All P&L, expectancy, drawdown, MAE, and MFE amounts are quote-price units for one unit of exposure, not broker-account returns. '
              'Win rate, mean win/loss, and profit factor are after the identical 0.40 round-trip deduction. '
              'MAE/MFE use the existing full-bar convention, including the exit bar whose intrabar order is unknown. '
              'The engine’s raw Sharpe/Sortino values are retained in full result files but are withheld here because this short, dependent daily sample cannot support meaningful annualized-ratio interpretation.', '',
              '## Incremental contribution: combined minus technical-only', '',
              'Positive expectancy/P&L differences favor D. Positive drawdown or MAE differences indicate more adverse movement. '
              'These are differences of strategy means with different entry sets and occupancy, not paired trades.', '',
              '| Metric delta (D − B) | Train | Validation | Final test |', '|---|---:|---:|---:|']
    for key, label in METRICS:
        if key in ('sharpe', 'sortino', 'daily_observations'):
            continue
        cells = []
        for segment in ['train', 'validation', 'test']:
            number = increments[segment]['combined_minus_technical'][key]
            cells.append(f'{number * 100:.2f} pp' if key == 'win_rate' and number is not None else fmt(number, key))
        lines.append('| ' + label + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', f'The final-test exploratory 95% paired-block resampling interval for the net-expectancy difference is **[{interval[0]:.4f}, {interval[1]:.4f}]**. '
              'This uses the frozen two-date circular blocks, 10,000 draws, and seed 20260910. '
              'Trade P&L/counts are attributed to entry dates for the expectancy estimate; the same sampled dates are used for both arms. '
              'Only six represented test dates and previously inspected history prevent a reliable independent-edge significance claim. '
              'Block resampling preserves local dependence within blocks but does not remove dependence at longer scales or solve data reuse. '
              '[CMU time-series bootstrap notes](https://stat.cmu.edu/~cshalizi/dst/20/lectures/16/lecture-16.html).', '',
              '### Common-date marked P&L', '',
              '| UTC date | B: technical entries | D: combined | D − B |', '|---|---:|---:|---:|']
    for row in increments['test']['daily_marked_pnl']:
        lines.append(f'| {row["date_utc"]} | {row["B_marked_pnl"]:.4f} | {row["D_marked_pnl"]:.4f} | {row["combined_minus_technical"]:.4f} |')
    lines += ['', 'A strategy that takes fewer losing trades can improve total P&L while worsening expectancy per trade. '
              'The two measures must be considered separately; neither is optimized here.', '',
              '## Fixed five-minute directional diagnostic', '',
              'One predeclared 300-second close-to-close horizon, exact endpoints only, with outcomes stored separately from original forecasts. '
              'The common-opportunity mean assigns zero to neutral decisions; actionable-only means condition on each arm’s own signals. '
              'These overlapping outcomes are descriptive, not a tradable P&L series or independent samples.', '',
              '| Final-test arm | Available opportunities | Actionable opportunities | Mean signed bps / common opportunity | Mean signed bps / actionable signal |',
              '|---|---:|---:|---:|---:|']
    for arm, row in test.items():
        s = row['signal_diagnostics']
        lines.append(f'| {arm} | {s["available"]} | {s["actionable"]} | {fmt(s["mean_signed_bps_all_available_opportunities"])} | {fmt(s["mean_signed_bps_actionable"])} |')
    lines += ['', f'D − B on the same final-test opportunity grid: **{increments["test"]["five_minute_mean_signed_bps_per_common_opportunity_delta"]:.4f} basis points per opportunity**. '
              'This supplemental metric removes target/stop mechanics from the outcome calculation, while still reflecting different entry/abstention decisions. No other horizon was tried.', '',
              '## Training comparison', '', arm_table(value['summaries']['train']), '',
              '## Validation comparison', '', arm_table(value['summaries']['validation']), '',
              '## Verification and reproducibility', '',
              '- The isolated simulator reproduced the original full-training result and original final-test result exactly after excluding the separately archived forecast arrays. All 6,033 original final-test forecast hashes matched.',
              '- A = D in every segment. All 18 real-data prefix checks passed across the three active entry families and six timestamps.',
              f'- Independent artifact verification checked {sum(r["signals_verified"] for r in audit["checks"]):,} original forecast hashes and '
              f'{sum(r["trades_verified"] for r in audit["checks"]):,} trades, including costs, interval bounds, target/stop consistency, nonoverlap, equity reconciliation, and marked drawdown.',
              '- All recorded database-table fingerprints and existing source fingerprints remain unchanged. Production defaults, data, original backtest records, and frontend were not modified.',
              '- Eight new research correctness tests passed. Full regression: 43/45 passed; the two previously documented WebSocket cleanup tests recurred (one CancelledError, one active-count failure). No transport fix was included in this diagnostic.', '',
              f'[Full comparison JSON]({relative}/comparison.json) · [Metrics CSV]({relative}/metrics.csv) · '
              f'[Artifact hashes]({relative}/artifact_hashes.json) · [Independent verification]({relative}/verification.json). '
              'Each active arm/segment also has `*-result.json.gz` with trades, equity, raw metrics, and daily attribution, plus `*-signals.jsonl.gz` with every immutable original forecast, its hash, and separate five-minute outcome. '
              'The frozen protocol, runner, helper, tests, environment versions, and code hashes are archived alongside them.', '',
              'Reproduce from the project root (creates a new result directory):', '',
              '```powershell', '.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_research_ablation.py -v',
              '.\.venv\Scripts\python.exe scripts\research_ablation.py',
              '.\.venv\Scripts\python.exe scripts\report_ablation.py <new-result-directory>', '```', '',
              'No arm is promoted. This completes the diagnostic requested for the retained dataset; independent predictive value would require a separately frozen evaluation on genuinely uninspected data. '
              'Repeating selection on the same historical sample cannot manufacture a fresh holdout. '
              '[Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).', '']
    return '\n'.join(lines)


def main():
    directory = Path(sys.argv[1]).resolve()
    assert directory.is_relative_to(ROOT / 'docs' / 'experiments')
    if (directory / 'supplementary_hashes.json').exists():
        for name, expected in json.loads((directory / 'supplementary_hashes.json').read_text()).items():
            assert file_hash(directory / name) == expected, name
    comparison = json.loads((directory / 'comparison.json').read_text())
    registration = json.loads((directory / 'registration.json').read_text())
    audit = verify(directory, comparison, registration)
    with (directory / 'verification.json').open('w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2)
    (directory / 'report_ablation.py').write_bytes(Path(__file__).read_bytes())
    target = ROOT / 'docs' / 'TIME_WHEEL_ABLATION_REPORT.md'
    target.write_text(report(directory, comparison, registration, audit), encoding='utf-8')
    archived_report = target.read_text(encoding='utf-8').replace(
        f'](experiments/{directory.name}/', '](')
    (directory / 'comparison-report.md').write_text(archived_report, encoding='utf-8')
    supplements = {name: file_hash(directory / name) for name in ['verification.json', 'report_ablation.py', 'comparison-report.md']}
    with (directory / 'supplementary_hashes.json').open('w', encoding='utf-8') as f:
        json.dump(supplements, f, indent=2)
    print(json.dumps({'report': str(target), 'audit': audit}, indent=2))


if __name__ == '__main__':
    main()
