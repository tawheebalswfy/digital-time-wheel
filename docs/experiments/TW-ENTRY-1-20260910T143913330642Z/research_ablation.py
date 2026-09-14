"""TW-ENTRY-1: isolated, read-only entry-family ablation; production stays unchanged."""
from collections import defaultdict
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys
from types import FunctionType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import backtest
from backend.app.config import Strategy
from backend.app.database import canonical, digest
from backend.app.data import validate_bars
from backend.app.signals import analyze, targets
from backend.app.technical import features

spec = importlib.util.spec_from_file_location('checkpoint_validator', ROOT / 'scripts' / 'validate-checkpoint.py')
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)

TECHNICAL = ('structure', 'support_resistance', 'momentum', 'fibonacci')
WHEEL = ('wheel', 'geometry', 'volatility', 'gates')
ARMS = {'A': 'Existing baseline', 'B': 'Technical-only entries',
        'C': 'Wheel-only entries', 'D': 'Existing combined (identical to A)'}
RUN_ID = '41ba0ea5-4b9d-4c09-8c2d-7947da46385b'
PROTOCOL = ROOT / 'docs' / 'TIME_WHEEL_ABLATION_PROTOCOL.md'


def choose_entry(base, c, arm):
    if arm in ('A', 'D'):
        return base['direction_value'], base['scores']
    family = TECHNICAL if arm == 'B' else WHEEL if arm == 'C' else None
    if family is None:
        raise ValueError('Unknown arm')
    total = sum(c.weights[k] for k in family)
    scores = {label: round(100 * sum(c.weights[k] for k in family if base['components'][k] == sign) / total, 4)
              for label, sign in [('buy', 1), ('sell', -1), ('neutral', 0)]}
    winner = 1 if scores['buy'] > scores['sell'] else -1 if scores['sell'] > scores['buy'] else 0
    if max(scores['buy'], scores['sell']) < c.threshold:
        winner = 0
    if arm == 'C' and winner != base['numerical_signal']:
        winner = 0
    return winner, scores


def ablated_signal(row, c, ts, arm):
    base = analyze(row, c, ts)
    if arm in ('A', 'D'):
        return base
    direction, scores = choose_entry(base, c, arm)
    levels = ({k: base[k] for k in ('targets', 'invalidation', 'candidates')}
              if direction == base['direction_value'] else targets(base['price'], direction, row, base['wheel'], c, ts))
    label = 'BUY' if direction == 1 else 'SELL' if direction == -1 else 'NEUTRAL'
    confidence = scores['buy' if direction == 1 else 'sell' if direction == -1 else 'neutral']
    return {**base, 'direction_value': direction, 'direction': label,
            'label': ('STRONG ' if direction and confidence >= 75 else '') + label,
            'scores': scores, 'confidence': confidence,
            'reasons': [f'TW-ENTRY-1 arm {arm}: {ARMS[arm]}; active-family weights normalized; threshold unchanged.',
                        'Common baseline exit generator retained, including wheel and technical levels.'],
            **levels}


def isolated_simulator(signal_function):
    # A private globals dictionary; do not monkeypatch backtest.analyze or any module.
    namespace = dict(backtest.run_backtest.__globals__)
    namespace['analyze'] = signal_function
    return FunctionType(backtest.run_backtest.__code__, namespace,
                        backtest.run_backtest.__name__, backtest.run_backtest.__defaults__,
                        backtest.run_backtest.__closure__)


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def write_gzip(path, value):
    with path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as f:
            f.write(canonical(value).encode())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(result):
    m = result['metrics']
    trades = result['trades']
    return {'trades': m['trades'], 'win_rate': m['win_rate'], 'average_win': m['average_win'],
            'average_loss': m['average_loss'], 'profit_factor': m['profit_factor'],
            'gross_expectancy': float(np.mean([t['pnl'] + t['costs'] for t in trades])) if trades else None,
            'net_expectancy': m['expectancy'], 'net_pnl': m['net_pnl'], 'max_drawdown': m['max_drawdown'],
            'max_drawdown_percent': m['max_drawdown_percent'],
            'mean_mae': float(np.mean([t['mae'] for t in trades])) if trades else None,
            'max_mae': m['maximum_adverse_excursion'],
            'mean_mfe': float(np.mean([t['mfe'] for t in trades])) if trades else None,
            'max_mfe': m['maximum_favorable_excursion'],
            'sharpe': None, 'sortino': None, 'daily_observations': m['daily_observations'],
            'risk_ratio_note': 'Withheld: short dependent daily sample; raw engine values retained in results, not interpreted.',
            'actionable_signals': m['signal_counts']['BUY'] + m['signal_counts']['SELL'],
            'total_signals': m['total_signals']}


def daily_rows(result):
    marked = {}
    for row in result['equity']:
        marked[checkpoint.iso(row['time'])[:10]] = row['value']
    entries = defaultdict(lambda: {'trades': 0, 'net_pnl': 0.0})
    for trade in result['trades']:
        day = checkpoint.iso(trade['entry_time'])[:10]
        entries[day]['trades'] += 1
        entries[day]['net_pnl'] += trade['pnl']
    previous = result['strategy']['initial_equity']
    rows = []
    for day, value in sorted(marked.items()):
        rows.append({'date_utc': day, 'marked_pnl': value - previous,
                     'entry_trades': entries[day]['trades'], 'entry_trade_pnl': entries[day]['net_pnl']})
        previous = value
    return rows


def paired_bootstrap(technical, combined, seed=20260910, draws=10000):
    if [r['date_utc'] for r in technical] != [r['date_utc'] for r in combined]:
        raise ValueError('Date grids must match')
    n = len(technical)
    if n < 2:
        return {'available': False, 'days': n}
    b = np.array([[r[k] for k in ('marked_pnl', 'entry_trades', 'entry_trade_pnl')] for r in technical])
    d = np.array([[r[k] for k in ('marked_pnl', 'entry_trades', 'entry_trade_pnl')] for r in combined])
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(draws, (n + 1) // 2))
    indices = ((starts[:, :, None] + np.arange(2)) % n).reshape(draws, -1)[:, :n]
    bs, ds = b[indices].sum(axis=1), d[indices].sum(axis=1)
    valid = (bs[:, 1] > 0) & (ds[:, 1] > 0)
    expectancy_delta = ds[valid, 2] / ds[valid, 1] - bs[valid, 2] / bs[valid, 1]
    daily_delta = (ds[:, 0] - bs[:, 0]) / n
    return {'available': True, 'days': n, 'block_length_represented_dates': 2,
            'seed': seed, 'draws': draws, 'valid_expectancy_draws': int(valid.sum()),
            'net_expectancy_delta_exploratory_95_interval': np.quantile(expectancy_delta, [.025, .975]).tolist() if len(expectancy_delta) else None,
            'mean_daily_marked_pnl_delta_exploratory_95_interval': np.quantile(daily_delta, [.025, .975]).tolist(),
            'interpretation': 'Descriptive paired circular-block resampling; too few test dates and reused history for reliable significance or fresh predictive-edge claims.'}


class Recorder:
    def __init__(self, arm, bars, end, stream, expected_originals=None):
        self.arm, self.stream = arm, stream
        self.lookup = {b['time'] + 60: b['close'] for b in bars[:end]}
        self.expected_originals = expected_originals
        self.original_matches = 0
        self.hasher = hashlib.sha256()
        self.horizon = {'available': 0, 'unavailable': 0, 'actionable': 0,
                        'signed_bps_sum': 0.0, 'actionable_signed_bps_sum': 0.0}

    def __call__(self, row, c, ts):
        signal = ablated_signal(row, c, ts, self.arm)
        original = {k: v for k, v in signal.items() if k != 'candidates'}
        signature = digest(original)
        if self.expected_originals is not None:
            if signature != self.expected_originals[ts]:
                raise AssertionError('Baseline forecast changed')
            self.original_matches += 1
        outcome = {'horizon_seconds': 300, 'endpoint': ts + 300, 'available': ts + 300 in self.lookup}
        if outcome['available']:
            bps = signal['direction_value'] * (self.lookup[ts + 300] / signal['price'] - 1) * 10000
            outcome.update(signed_return_bps=bps, endpoint_price=self.lookup[ts + 300])
            self.horizon['available'] += 1
            self.horizon['signed_bps_sum'] += bps
            if signal['direction_value']:
                self.horizon['actionable'] += 1
                self.horizon['actionable_signed_bps_sum'] += bps
        else:
            self.horizon['unavailable'] += 1
        encoded = (canonical({'original': original, 'original_hash': signature, 'outcome': outcome}) + '\n').encode()
        self.hasher.update(encoded)
        self.stream.write(encoded)
        return signal

    def diagnostics(self):
        h = self.horizon
        return {**h, 'horizon_seconds': 300,
                'mean_signed_bps_all_available_opportunities': h['signed_bps_sum'] / h['available'] if h['available'] else None,
                'mean_signed_bps_actionable': h['actionable_signed_bps_sum'] / h['actionable'] if h['actionable'] else None,
                'scope': 'Descriptive overlapping 5-minute close-to-close forecasts, not executable trade P&L or independent observations.'}


def run_arm(arm, segment, bars, c, bounds, out, expected=None):
    name = f'{segment}-{arm}'
    print(f'Running {name}: {bounds[0]}:{bounds[1]}', flush=True)
    with (out / f'{name}-signals.jsonl.gz').open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            recorder = Recorder(arm, bars, bounds[1], stream, expected)
            result = isolated_simulator(recorder)(bars, c, 'M1', bounds[0], bounds[1], False)
    wrapped = {'experiment': 'TW-ENTRY-1', 'arm': arm, 'label': ARMS[arm],
               'start_index': bounds[0], 'end_index_exclusive': bounds[1],
               'result': result, 'summary': summary(result), 'daily': daily_rows(result),
               'signal_diagnostics': recorder.diagnostics(), 'signal_audit_sha256_uncompressed': recorder.hasher.hexdigest(),
               'baseline_original_forecast_matches': recorder.original_matches}
    write_gzip(out / f'{name}-result.json.gz', wrapped)
    return wrapped


def compare(segment, results):
    b, d = results['B'], results['D']
    delta = {k: d['summary'][k] - b['summary'][k]
             if isinstance(b['summary'][k], (int, float)) and isinstance(d['summary'][k], (int, float)) else None
             for k in b['summary']}
    daily = [{'date_utc': x['date_utc'], 'B_marked_pnl': x['marked_pnl'], 'D_marked_pnl': y['marked_pnl'],
              'combined_minus_technical': y['marked_pnl'] - x['marked_pnl']}
             for x, y in zip(b['daily'], d['daily'])]
    horizon_delta = d['signal_diagnostics']['mean_signed_bps_all_available_opportunities'] - b['signal_diagnostics']['mean_signed_bps_all_available_opportunities']
    return {'segment': segment, 'combined_minus_technical': delta, 'daily_marked_pnl': daily,
            'paired_block_resampling': paired_bootstrap(b['daily'], d['daily']),
            'five_minute_mean_signed_bps_per_common_opportunity_delta': horizon_delta,
            'expectancy_scope': 'Difference of strategy means, not matched-trade treatment effect; each strategy has different entries/occupancy.'}


def main():
    if len(sys.argv) != 1:
        raise ValueError('This frozen experiment accepts no tunable parameters')
    out = ROOT / 'docs' / 'experiments' / ('TW-ENTRY-1-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    code_before = checkpoint.fingerprints()
    archived = json.loads((ROOT / 'docs' / 'validation' / '20260910T142537938267Z' / 'evidence.json').read_text())
    for name, value in archived['source_before'].items():
        if file_hash(ROOT / name) != value:
            raise AssertionError(f'Verified baseline source changed: {name}')
    conn = sqlite3.connect((ROOT / 'runtime' / 'timewheel.sqlite3').as_uri() + '?mode=ro', uri=True)
    conn.execute('PRAGMA query_only=ON')
    db_before = checkpoint.logical_state(conn)
    saved = json.loads(conn.execute('SELECT payload FROM backtests WHERE id=?', (RUN_ID,)).fetchone()[0])
    c = Strategy(**saved['test']['strategy'])
    assert saved['train']['strategy'] == saved['test']['strategy']
    meta = json.loads(conn.execute('SELECT payload FROM datasets WHERE id=?', (saved['dataset_id'],)).fetchone()[0])
    bars = [json.loads(row[0]) for row in conn.execute('SELECT payload FROM candles WHERE dataset_id=? ORDER BY time', (saved['dataset_id'],))]
    validate_bars(bars, 60)
    assert len(bars) == 30170 and digest(bars) == meta['content_hash']
    assert digest({'metadata': meta, 'bars': bars}) == saved['dataset_id']
    assert saved['split_index'] == 24136 and saved['purge_bars'] == 31
    bounds = {'train': (78, 18071), 'validation': (18102, 24105), 'test': (24136, 30170)}
    # Archive exactly the executable/protocol/test sources used, before results exist.
    for path in [Path(__file__), PROTOCOL, ROOT / 'tests' / 'test_research_ablation.py', ROOT / 'scripts' / 'validate-checkpoint.py']:
        (out / path.name).write_bytes(path.read_bytes())
    registration = {'experiment': 'TW-ENTRY-1', 'frozen_before_results_utc': datetime.now(timezone.utc).isoformat(),
                    'baseline_run_id': RUN_ID, 'baseline_payload_sha256': digest(saved),
                    'dataset_id': saved['dataset_id'], 'dataset': meta, 'strategy': c.model_dump(mode='json'),
                    'strategy_hash': digest(c.model_dump(mode='json')), 'arms': ARMS,
                    'protocol_sha256': file_hash(PROTOCOL), 'runner_sha256': file_hash(Path(__file__)),
                    'boundaries': {k: {'start_index': v[0], 'end_index_exclusive': v[1],
                                      'first_bar_open_utc': checkpoint.iso(bars[v[0]]['time']),
                                      'first_signal_utc': checkpoint.iso(bars[v[0]]['time'] + 60),
                                      'end_utc': checkpoint.iso(bars[v[1]-1]['time'] + 60)} for k, v in bounds.items()},
                    'python': platform.python_version(), 'packages': {n: importlib.metadata.version(n) for n in ['numpy', 'pandas', 'pydantic']},
                    'source_before': code_before, 'database_before': db_before,
                    'evaluation_order': ['baseline_training_parity', 'train', 'validation', 'test'],
                    'parameter_search': False, 'final_period_previously_inspected': True,
                    'shared_exits_include_wheel_levels': True}
    write_json(out / 'registration.json', registration)
    print('Frozen registration: ' + str(out / 'registration.json'), flush=True)
    print('Verifying original full training checkpoint parity...', flush=True)
    baseline_train = backtest.run_backtest(bars, c, 'M1', end_index=24105, keep_signals=False)
    expected_train = {**saved['train'], 'forecasts': []}
    assert digest(baseline_train) == digest(expected_train)
    parity = {'original_training_result_without_forecasts_sha256': digest(baseline_train), 'original_training_match': True}
    del baseline_train, expected_train
    all_summaries, comparisons, per_segment = {}, {}, {}
    for segment, indices in bounds.items():
        parts = {}
        expected = {f['original']['timestamp']: f['original_hash'] for f in saved['test']['forecasts']} if segment == 'test' else None
        for arm in ['A', 'B', 'C']:
            parts[arm] = run_arm(arm, segment, bars, c, indices, out, expected if arm == 'A' else None)
            if arm == 'A' and segment == 'test':
                assert digest(parts[arm]['result']) == digest({**saved['test'], 'forecasts': []})
                parity['original_test_match'] = True
                parity['original_test_forecast_matches'] = parts[arm]['baseline_original_forecast_matches']
                parity['original_test_result_without_forecasts_sha256'] = digest(parts[arm]['result'])
        parts['D'] = parts['A']
        write_json(out / f'{segment}-D-reference.json', {'arm': 'D', 'identical_to': 'A',
                   'result_file': f'{segment}-A-result.json.gz', 'result_sha256': file_hash(out / f'{segment}-A-result.json.gz'),
                   'reason': 'The existing baseline is already the existing combined strategy; do not count it as an independent trial.'})
        all_summaries[segment] = {arm: {**p['summary'], 'signal_diagnostics': p['signal_diagnostics']} for arm, p in parts.items()}
        comparisons[segment] = compare(segment, parts)
        per_segment[segment] = {'A_equals_D': digest(parts['A']) == digest(parts['D'])}
        del parts
    # Real-data prefix checks include both sides of each split and every active entry family.
    f = features(bars, c)
    checks = []
    for i in [299, 18101, 18102, 24135, 24136, 30168]:
        prefix = features(bars[:i + 1], c).iloc[-1].to_dict()
        for arm in ['A', 'B', 'C']:
            assert digest(ablated_signal(prefix, c, bars[i]['time'] + 60, arm)) == digest(ablated_signal(f.iloc[i].to_dict(), c, bars[i]['time'] + 60, arm))
        checks.append({'bar_index': i, 'A_B_C_prefix_invariant': True})
    assert checkpoint.fingerprints() == code_before
    assert checkpoint.logical_state(conn) == db_before
    conn.close()
    output = {'experiment': 'TW-ENTRY-1', 'summaries': all_summaries, 'comparisons': comparisons,
              'parity': parity, 'control_identity': per_segment, 'real_data_prefix_checks': checks,
              'production_source_preserved': True, 'database_rows_preserved': True,
              'completed_utc': datetime.now(timezone.utc).isoformat(),
              'conclusion': 'Evidence is inconclusive for independent out-of-sample predictive value; report the observed sample effects separately.'}
    write_json(out / 'comparison.json', output)
    with (out / 'metrics.csv').open('x', newline='', encoding='utf-8') as file:
        keys = list(summary({'metrics': saved['test']['metrics'], 'trades': saved['test']['trades']}))
        writer = csv.DictWriter(file, ['segment', 'arm', 'label'] + keys)
        writer.writeheader()
        for segment, arms in all_summaries.items():
            for arm, row in arms.items():
                writer.writerow({'segment': segment, 'arm': arm, 'label': ARMS[arm], **{k: row[k] for k in keys}})
    write_json(out / 'artifact_hashes.json', {p.name: file_hash(p) for p in sorted(out.iterdir()) if p.is_file()})
    print(json.dumps({'output': str(out), 'parity': parity, 'test': all_summaries['test'],
                      'test_increment': comparisons['test'], 'preserved': True}, indent=2), flush=True)


if __name__ == '__main__':
    main()
