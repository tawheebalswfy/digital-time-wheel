"""Constructed fixtures verify research correctness, never predictive performance."""
import copy
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from research_ablation import (TECHNICAL, WHEEL, Recorder, ablated_signal,
                               choose_entry, isolated_simulator, paired_bootstrap)
from backend.app import backtest
from backend.app.config import Strategy
from backend.app.database import digest
from backend.app.signals import analyze, targets
from backend.app.technical import features
from test_system import fixture


class AblationCorrectness(unittest.TestCase):
    def test_technical_entry_is_independent_of_all_wheel_votes(self):
        c = Strategy()
        base = {'components': {k: 0 for k in (*TECHNICAL, *WHEEL)}, 'numerical_signal': -1}
        base['components'].update(structure=1, momentum=1)
        direction, scores = choose_entry(base, c, 'B')
        self.assertEqual(direction, 1)
        self.assertEqual(scores['buy'], 62.5)
        for d in [-1, 0, 1]:
            alternate = copy.deepcopy(base)
            alternate['components'].update({k: d for k in WHEEL})
            alternate['numerical_signal'] = d
            self.assertEqual(choose_entry(alternate, c, 'B'), (direction, scores))

    def test_wheel_entry_needs_no_technical_confirmation(self):
        c = Strategy()
        base = {'components': {k: 1 for k in WHEEL}, 'numerical_signal': 1}
        base['components'].update({k: -1 for k in TECHNICAL})
        self.assertEqual(choose_entry(base, c, 'C')[0], 1)
        before = choose_entry(base, c, 'C')
        base['components'].update({k: 1 for k in TECHNICAL})
        self.assertEqual(choose_entry(base, c, 'C'), before)
        base['numerical_signal'] = 0
        self.assertEqual(choose_entry(base, c, 'C')[0], 0)

    def test_threshold_and_ties_are_not_reoptimized(self):
        c = Strategy()
        base = {'components': {k: 0 for k in (*TECHNICAL, *WHEEL)}, 'numerical_signal': 0}
        base['components'].update(structure=1, fibonacci=1)
        self.assertEqual(choose_entry(base, c, 'B')[1]['buy'], 50)
        self.assertEqual(choose_entry(base, c, 'B')[0], 0)
        base['components'].update(momentum=-1, support_resistance=-1)
        self.assertEqual(choose_entry(base, c, 'B')[0], 0)

    def test_same_exit_generator_and_baseline_identity(self):
        bars = fixture(180)
        c = Strategy(anchor_price=2000)
        frame = features(bars, c)
        for i in [78, 100, 150, 179]:
            row, ts = frame.iloc[i].to_dict(), bars[i]['time'] + 60
            base = analyze(row, c, ts)
            for arm in ['A', 'D']:
                self.assertEqual(ablated_signal(row, c, ts, arm), base)
            for arm in ['B', 'C']:
                result = ablated_signal(row, c, ts, arm)
                expected = targets(row['close'], result['direction_value'], row, base['wheel'], c, ts)
                for key in ['targets', 'invalidation', 'candidates']:
                    self.assertEqual(result[key], expected[key])

    def test_isolated_simulation_matches_engine_without_mutation(self):
        bars = fixture(180)
        c = Strategy(anchor_price=2000)
        original_binding = backtest.analyze
        before = c.model_dump(mode='json')
        actual = isolated_simulator(lambda row, config, ts: ablated_signal(row, config, ts, 'A'))(bars, c, keep_signals=False)
        expected = backtest.run_backtest(bars, c, keep_signals=False)
        self.assertEqual(digest(actual), digest(expected))
        self.assertIs(backtest.analyze, original_binding)
        self.assertEqual(c.model_dump(mode='json'), before)

    def test_all_entry_families_are_prefix_invariant(self):
        bars, c = fixture(240), Strategy(anchor_price=2000)
        full, prefix = features(bars, c), features(bars[:150], c)
        ts = bars[149]['time'] + 60
        for arm in ['A', 'B', 'C', 'D']:
            self.assertEqual(digest(ablated_signal(full.iloc[149].to_dict(), c, ts, arm)),
                             digest(ablated_signal(prefix.iloc[-1].to_dict(), c, ts, arm)))

    def test_future_outcomes_do_not_enter_decisions_or_cross_end(self):
        bars, c = fixture(180), Strategy(anchor_price=2000)
        row = features(bars, c).iloc[100].to_dict()
        ts = bars[100]['time'] + 60
        original = Recorder('B', bars, 180, io.BytesIO())(row, c, ts)
        modified = copy.deepcopy(bars)
        modified[105]['close'] += 100
        altered = Recorder('B', modified, 180, io.BytesIO())(row, c, ts)
        self.assertEqual(original, altered)
        limited = Recorder('B', bars, 105, io.BytesIO())
        self.assertEqual(limited(row, c, ts), original)
        self.assertEqual(limited.horizon['unavailable'], 1)

    def test_paired_bootstrap_zero_control_and_determinism(self):
        rows = [{'date_utc': str(i), 'marked_pnl': i - 3., 'entry_trades': i + 1,
                 'entry_trade_pnl': i - 2.} for i in range(6)]
        same = paired_bootstrap(rows, rows)
        self.assertEqual(same['net_expectancy_delta_exploratory_95_interval'], [0, 0])
        self.assertEqual(same['mean_daily_marked_pnl_delta_exploratory_95_interval'], [0, 0])
        different = [{**r, 'marked_pnl': r['marked_pnl'] - 2,
                      'entry_trade_pnl': r['entry_trade_pnl'] - r['entry_trades']} for r in rows]
        first = paired_bootstrap(rows, different)
        self.assertEqual(first, paired_bootstrap(rows, different))
        for v in first['net_expectancy_delta_exploratory_95_interval']:
            self.assertAlmostEqual(v, -1)
        for v in first['mean_daily_marked_pnl_delta_exploratory_95_interval']:
            self.assertAlmostEqual(v, -2)


if __name__ == '__main__':
    unittest.main()
