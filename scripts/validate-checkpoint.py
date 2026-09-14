"""Replay retained MT5 research without starting services or writing to SQLite.

Run from the project root with .venv/Scripts/python.exe scripts/validate-checkpoint.py.
Each invocation creates a new evidence directory; existing artifacts are not replaced.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.backtest import run_backtest
from backend.app.config import Strategy, TIMEFRAMES
from backend.app.data import validate_bars
from backend.app.database import digest
from backend.app.signals import analyze
from backend.app.technical import features


def iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def fingerprints():
    paths = list((ROOT / 'backend').rglob('*.py'))
    paths += list((ROOT / 'tests').glob('*.py'))
    for folder in ['app', 'components', 'lib', 'tests', 'hooks']:
        paths += [p for p in (ROOT / 'frontend' / folder).rglob('*') if p.is_file()]
    paths += [p for p in (ROOT / 'frontend').glob('*') if p.is_file()]
    paths += list(ROOT.glob('requirements*.txt'))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def logical_state(conn):
    # Hash every retained logical row, independent of SQLite WAL/checkpoint layout.
    result = {}
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for table in tables:
        quoted = '"' + table.replace('"', '""') + '"'
        h = hashlib.sha256()
        count = 0
        for row in conn.execute(f'SELECT * FROM {quoted} ORDER BY rowid'):
            h.update(json.dumps(list(row), ensure_ascii=True, separators=(',', ':')).encode())
            h.update(b'\n')
            count += 1
        result[table] = {'rows': count, 'sha256': h.hexdigest()}
    return result


def summarize(values):
    return {'n': len(values), 'mean': statistics.mean(values) if values else None,
            'median': statistics.median(values) if values else None}


def ledger_metrics(trades, cost=None):
    pnl = [t['pnl'] if cost is None else t['pnl'] + t['costs'] - cost for t in trades]
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p < 0]
    return {'trades': len(pnl), 'net_pnl': sum(pnl),
            'expectancy': statistics.mean(pnl) if pnl else None,
            'win_rate': len(wins) / len(pnl) if pnl else None,
            'average_win': statistics.mean(wins) if wins else None,
            'average_loss': statistics.mean(losses) if losses else None,
            'profit_factor': sum(wins) / -sum(losses) if losses else None}


def diagnose(part):
    trades = part['trades']
    forecasts = {f['original']['timestamp']: f['original'] for f in part['forecasts']}
    groups = {name: defaultdict(list) for name in ['direction', 'exit_reason', 'entry_day_utc', 'first_target_source']}
    for trade in trades:
        forecast = forecasts[trade['signal_timestamp']]
        source = forecast['targets'][0]['reasons'][0]['source']
        for name, key in [('direction', trade['direction']), ('exit_reason', trade['reason']),
                          ('entry_day_utc', iso(trade['entry_time'])[:10]), ('first_target_source', source)]:
            groups[name][key].append(trade)
    avg_win, avg_loss = part['metrics']['average_win'], part['metrics']['average_loss']
    return {
        'net': ledger_metrics(trades), 'gross': ledger_metrics(trades, 0),
        'total_costs': sum(t['costs'] for t in trades),
        'cost_sensitivity': {str(c): ledger_metrics(trades, c) for c in [0, .2, .4, .8]},
        'cost_sensitivity_scope': 'Same saved entries/exits, changing only total per-trade deductions. No spread-aware order replay.',
        'reward_to_risk_at_entry': summarize([abs(t['target'] - t['entry']) / abs(t['entry'] - t['stop']) for t in trades]),
        'target_distance': summarize([abs(t['target'] - t['entry']) for t in trades]),
        'stop_distance': summarize([abs(t['entry'] - t['stop']) for t in trades]),
        'observed_payoff_breakeven_win_rate': abs(avg_loss) / (avg_win + abs(avg_loss)) if avg_win and avg_loss else None,
        'target_exits_with_nonpositive_net_pnl': sum(t['reason'] == 'target' and t['pnl'] <= 0 for t in trades),
        'breakdowns': {name: {key: ledger_metrics(rows) for key, rows in sorted(group.items())} for name, group in groups.items()},
        'breakdown_scope': 'Retrospective diagnostics of the existing trades. No subgroup was selected as a strategy.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', default='41ba0ea5-4b9d-4c09-8c2d-7947da46385b')
    args = parser.parse_args()
    out = ROOT / 'docs' / 'validation' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    source_before = fingerprints()
    conn = sqlite3.connect((ROOT / 'runtime' / 'timewheel.sqlite3').as_uri() + '?mode=ro', uri=True)
    conn.execute('PRAGMA query_only=ON')
    before = logical_state(conn)
    saved_row = conn.execute('SELECT created_at,payload FROM backtests WHERE id=?', (args.run_id,)).fetchone()
    if saved_row is None:
        raise ValueError('Requested checkpoint backtest does not exist')
    saved = json.loads(saved_row[1])
    git = subprocess.run(['git', 'status', '--short'], cwd=ROOT, capture_output=True, text=True)
    ports = {}
    for port in [8000, 5173]:
        with socket.socket() as probe:
            probe.settimeout(2)
            ports[str(port)] = probe.connect_ex(('127.0.0.1', port)) == 0
    evidence = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'run_id': args.run_id, 'original_run_created_at': saved_row[0],
                'original_payload_sha256': digest(saved), 'read_only_database': True,
                'git_status': {'exit_code': git.returncode, 'stdout': git.stdout, 'stderr': git.stderr},
                'local_ports_listening': ports, 'database_quick_check': conn.execute('PRAGMA quick_check').fetchone()[0],
                'database_before': before, 'source_before': source_before,
                'saved_feed_settings': json.loads(conn.execute('SELECT payload FROM feed_settings').fetchone()[0]),
                'saved_strategy': json.loads(conn.execute('SELECT payload FROM strategy_versions JOIN settings ON strategy_versions.id=settings.version_id').fetchone()[0]),
                'datasets': [], 'replay': {}, 'diagnostics': {}}
    previous = '0' * 64
    signal_count = 0
    for row in conn.execute('SELECT id,event_key,created_at,payload,previous_hash,hash FROM signals ORDER BY seq'):
        sid, key, created, payload, prior, signature = row
        assert prior == previous
        assert signature == digest({'id': sid, 'event_key': key, 'created_at': created,
                                    'payload': json.loads(payload), 'previous_hash': previous})
        previous = signature
        signal_count += 1
    evidence['signal_chain'] = {'valid': True, 'count': signal_count, 'head_hash': previous}
    bars = None
    for did, payload in conn.execute('SELECT id,payload FROM datasets ORDER BY created_at,id'):
        meta = json.loads(payload)
        rows = [json.loads(r[0]) for r in conn.execute('SELECT payload FROM candles WHERE dataset_id=? ORDER BY time', (did,))]
        seconds = TIMEFRAMES[meta['timeframe']]
        validate_bars(rows, seconds, require_alignment=False)
        assert digest(rows) == meta['content_hash']
        assert digest({'metadata': meta, 'bars': rows}) == did
        assert len(rows) == meta['bars']
        assert rows[0]['time'] == meta['start'] and rows[-1]['time'] + seconds == meta['end']
        assert all(b['original_broker_timestamp'] - meta['timestamp_offset_seconds'] == b['time'] for b in rows)
        gaps = [{'previous_close_utc': iso(a['time'] + seconds), 'next_open_utc': iso(b['time']),
                 'unrepresented_seconds': b['time'] - a['time'] - seconds}
                for a, b in zip(rows, rows[1:]) if b['time'] - a['time'] != seconds]
        evidence['datasets'].append({'id': did, **meta, 'hash_and_ohlc_valid': True,
                                     'normalization_valid': True, 'gaps': gaps,
                                     'gap_note': 'Unrepresented intervals; session closures versus missing feed data have not been independently classified.'})
        if did == saved['dataset_id']:
            bars = rows
    assert bars is not None
    c = Strategy(**saved['test']['strategy'])
    assert saved['train']['strategy'] == saved['test']['strategy']
    evidence['split'] = {'index': saved['split_index'], 'fraction': saved['split_index'] / len(bars),
                         'purge_bars': saved['purge_bars'], 'first_test_bar_open_utc': iso(bars[saved['split_index']]['time']),
                         'first_test_signal_utc': iso(saved['test']['start']), 'test_end_utc': iso(saved['test']['end'])}
    evidence['daily_m1_candle_counts'] = dict(sorted(Counter(iso(b['time'])[:10] for b in bars).items()))
    for name, bounds in [('train', {'end_index': saved['split_index'] - saved['purge_bars']}),
                         ('test', {'start_index': saved['split_index']})]:
        print(f'Replaying frozen {name} with existing engine...', flush=True)
        actual = run_backtest(bars, c, saved[name]['timeframe'], **bounds)
        equal = digest(actual) == digest(saved[name])
        evidence['replay'][name] = {'exact_payload_match': equal, 'saved_sha256': digest(saved[name]),
                                   'replayed_sha256': digest(actual), 'metrics': actual['metrics']}
        assert equal, f'{name} differs from checkpoint'
        assert all(digest(f['original']) == f['original_hash'] for f in saved[name]['forecasts'])
        assert abs(actual['equity'][-1]['value'] - c.initial_equity - actual['metrics']['net_pnl']) < 1e-8
        evidence['diagnostics'][name] = diagnose(saved[name])
        del actual
    full = features(bars, c)
    checks = []
    for index in [299, saved['split_index'] - 1, saved['split_index'], len(bars) - 2]:
        ts = bars[index]['time'] + 60
        prefix = features(bars[:index + 1], c).iloc[-1].to_dict()
        equal = digest(analyze(prefix, c, ts)) == digest(analyze(full.iloc[index].to_dict(), c, ts))
        assert equal
        checks.append({'bar_index': index, 'signal_utc': iso(ts), 'full_signal_prefix_invariant': equal})
    evidence['real_data_causality_spot_checks'] = checks
    evidence['source_after'] = fingerprints()
    evidence['database_after'] = logical_state(conn)
    conn.close()
    assert source_before == evidence['source_after'], 'Existing implementation changed during validation'
    assert before == evidence['database_after'], 'Retained database rows changed during validation'
    evidence['preservation_verified'] = True
    evidence['limitations'] = [
        'Saved MT5 provenance and content integrity verified; no independent second-provider verification.',
        'No services or MT5 terminal started; post-restart live quote/history/UI behavior not reverified.',
        'Previously inspected test period is reused for reproduction and diagnosis, not fresh out-of-sample evidence.',
        'Fixed-cost one-unit simulation, not broker-lot, tick-path, financing or account-return validation.',
        'Four prefix checks are spot checks, not an exhaustive causality proof.',
    ]
    output = out / 'evidence.json'
    output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'evidence': str(output), 'preservation_verified': True,
                      'replay_matches': {k: v['exact_payload_match'] for k, v in evidence['replay'].items()},
                      'test_diagnostics': evidence['diagnostics']['test']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
