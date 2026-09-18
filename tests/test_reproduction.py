"""Unit and archived-result tests (standard-library unittest runner)."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
import numpy as np
from scipy.stats import binom
from tools.common import ROOT, REFERENCE, check_reference, load_engine, load_json, set_threads
from tools.compare import compare_json, compare_csv, compare_results

set_threads()
engine = load_engine()
core = engine.r


class NumericalPrimitives(unittest.TestCase):
    def test_plant_stability_and_markov_probabilities(self):
        for name in ("A", "B"):
            p = core.make_plant(name)
            self.assertLess(max(abs(np.linalg.eigvals(p.AK))), 1)
            np.testing.assert_allclose(p.transition.sum(axis=1), 1)
            stationary = core.stationary(p.transition)
            np.testing.assert_allclose(stationary @ p.transition, stationary, atol=1e-14)
            self.assertTrue((stationary > 0).all())
            np.testing.assert_allclose(p.AK.T @ p.P @ p.AK-p.P,
                -(p.Q+p.R*(p.K.T@p.K)), atol=1e-12)

    def test_repeated_primitive_seed(self):
        p = core.make_plant("A")
        a = core.calibration_trajectories(p, 13, 1100, 0)
        b = core.calibration_trajectories(p, 13, 1100, 0)
        c = core.calibration_trajectories(p, 13, 1101, 0)
        self.assertTrue(np.array_equal(a, b))
        self.assertFalse(np.array_equal(a, c))

    def test_error_recursion_from_primitive_stream(self):
        p = core.make_plant("A")
        mode, eta, mix = core.paths(p, 7, 2345, 1)
        expected = core.calibration_trajectories(p, 7, 2345, 1)
        error = np.zeros((7, 2))
        for t in range(p.H):
            noise = np.einsum('nij,nj->ni', p.L[mode[:,t]], eta[:,t])+p.means[mode[:,t]]
            error = error @ p.AK.T + noise
            np.testing.assert_allclose(error, expected[:,t], atol=1e-15)

    def test_order_statistic_rank_is_maximal(self):
        s, upper = core.order_parameter(50000, .004, .001/3)
        self.assertLessEqual(binom.cdf(s, 50000, .004), .001/3)
        self.assertGreater(binom.cdf(s+1, 50000, .004), .001/3)
        self.assertLessEqual(upper, .004)

    def test_small_sample_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'sample size'):
            core.order_parameter(100, .004, .001/3)

    def test_scenario_count_and_scalar_minimum(self):
        self.assertEqual(core.scenario_n(16, .004, .001/3, 50000)[0], 8295)
        minimum = int(np.ceil(np.log(.001/3)/np.log1p(-.004)))
        self.assertEqual(minimum, 1998)
        core.order_parameter(minimum, .004, .001/3)
        with self.assertRaises(ValueError):
            core.order_parameter(minimum-1, .004, .001/3)

    def test_A_residual_law_does_not_depend_on_nominal_control_tail(self):
        p = core.make_plant("A")
        g, eta, mix = core.paths(p, 1, 3456, 2)
        initial = np.array([1., -.1])
        errors = []
        for v in (np.zeros(p.H), np.linspace(-.2, .2, p.H)):
            z = [initial.copy()]
            for u in v:
                z.append(p.A @ z[-1]+p.B.ravel()*u)
            errors.append(core.tail(p, initial, np.array(z), v, g[0], eta[0], mix[0]))
        np.testing.assert_allclose(errors[0], errors[1], atol=1e-13)

    def test_controlled_mixture_weight_bound(self):
        base = core.make_plant("B")
        rng = np.random.default_rng(491)
        for gamma in engine.SHIFT_FACTORS:
            p = replace(base, gamma=gamma)
            for x, u in zip(rng.normal(size=(40,2))*5, rng.normal(size=40)*3):
                alpha = core.alpha_deploy(p, x, u)
                self.assertGreaterEqual(alpha, p.alpha0)
                self.assertLessEqual(alpha, p.alpha0*gamma**(1/p.H)+1e-15)
                self.assertLessEqual(alpha/p.alpha0, gamma**(1/p.H)+1e-13)
                self.assertLessEqual((1-alpha)/(1-p.alpha0), 1+1e-15)


class GeometricAndOperationalChecks(unittest.TestCase):
    def atlas(self, name='collective_compatible'):
        return engine.load_atlas(REFERENCE / f'results/A/seed_0/{name}_atlas.json', core.make_plant('A'))

    def test_common_scaling_preserves_all_inclusions(self):
        atlas = self.atlas()
        for factor in (.25, 1., 3.):
            for c in atlas.charts:
                for d in atlas.charts:
                    for t in range(atlas.p.H):
                        margin = factor*c.S[t+1]-np.abs(np.linalg.matrix_power(atlas.p.AK,t))@(factor*c.S[1])-factor*d.S[t]
                        self.assertGreaterEqual(float(margin.min()), -1e-10)

    def test_noedge_diagnostic_is_retained(self):
        atlas = self.atlas('noedge')
        self.assertEqual(atlas.audit['failed_scalar_cross_section_inequalities'], 89)
        self.assertFalse(atlas.edges.any())

    def test_origin_QP_and_infeasible_reset(self):
        atlas = self.atlas()
        solver = core.MPC(atlas)
        result = solver.solve(np.zeros(2), 0)
        self.assertIsNotNone(result)
        self.assertLess(abs(result[0]), 1e-9)
        self.assertIsNone(solver.solve(np.array([100., 100.]), 0))

    def test_contextual_reserve_recursion(self):
        atlas = engine.load_atlas(REFERENCE / 'results/budget/reserve_contextual_atlas.json', core.make_plant('A'))
        J = core.reserves(atlas, 22)
        np.testing.assert_array_equal(J[0], 0)
        for ell in range(1, 23):
            for i, chart in enumerate(atlas.charts):
                minima = []
                for g in range(atlas.p.ng):
                    ds = [j for j, d in enumerate(atlas.charts) if d.g == g and atlas.edges[i,j]]
                    minima.append(min(atlas.charts[j].risk+J[ell-1,j] for j in ds))
                self.assertAlmostEqual(J[ell,i], max(minima), places=14)

    def test_budget_exhaustion_and_preflight_are_different(self):
        greedy = load_json(REFERENCE / 'results/budget/greedy_summary.json')
        preflight = load_json(REFERENCE / 'results/budget/preflight_summary.json')
        self.assertEqual(greedy['steps'], 5)
        self.assertEqual(greedy['budget_exhaustions'], 1)
        self.assertEqual(preflight['steps'], 0)
        self.assertEqual(preflight['budget_rejections'], 1)

    def test_recovery_remains_a_stress_diagnostic(self):
        summary = load_json(REFERENCE / 'results/recovery/interior_shock_summary.json')
        self.assertTrue(summary['recovery_entry_inside_X'])
        self.assertEqual(summary['backup_steps'], 14)
        self.assertEqual(summary['state_violation_count'], 4)
        self.assertEqual(summary['input_violation_count'], 0)

    def test_largest_shift_is_sample_rejected(self):
        import pandas as pd
        sweep = pd.read_csv(REFERENCE / 'results/B/shift_sweep.csv')
        self.assertEqual(list(sweep.query('Gamma >= 100').status), ['sample_rejected', 'sample_rejected'])
        self.assertTrue(sweep.query('Gamma >= 100').corrected_test_pct.isna().all())


class RepositoryRegression(unittest.TestCase):
    def test_reference_integrity(self):
        self.assertTrue(check_reference()['ok'])

    def test_config_matches_engine(self):
        cfg = load_json(ROOT / 'config/paper.json')
        common = cfg['common']
        self.assertEqual(common['design_trajectories_per_context'], engine.NDES)
        self.assertEqual(common['calibration_trajectories_per_context'], engine.NCAL)
        self.assertEqual(common['test_trajectories_per_context'], engine.NTEST)
        self.assertEqual(common['replication_offsets_A'], engine.OFFSETS)
        self.assertEqual(common['shift_factors_B'], engine.SHIFT_FACTORS)
        for name in ('A','B'):
            p = core.make_plant(name)
            for field, value in cfg['plants'][name].items():
                actual = getattr(p, field)
                if hasattr(actual, 'tolist'):
                    self.assertEqual(value, actual.tolist())
                else:
                    self.assertEqual(value, actual)

    def test_independent_audit_of_archive(self):
        from tools.audit import audit_results
        report = audit_results(REFERENCE / 'results')
        self.assertTrue(report['ok'], report['errors'][:10])
        self.assertEqual(report['mission_logs_checked'], 36)

    def test_json_corruption_is_detected(self):
        errors = []
        compare_json({'risk': .004, 'count': 2}, {'risk': .02, 'count': 3}, 'test', errors, 2e-7, 1e-8)
        self.assertEqual(len(errors), 2)

    def test_timing_difference_is_excluded(self):
        errors = []
        compare_json({'cost': 1., 'solve_median_ms': 1.}, {'cost': 1., 'solve_median_ms': 100.}, 'test', errors, 2e-7, 1e-8)
        self.assertFalse(errors)

    def test_missing_results_never_pass_a_full_comparison(self):
        with tempfile.TemporaryDirectory() as folder:
            report = compare_results(REFERENCE / 'results', Path(folder))
            self.assertFalse(report['ok'])
            self.assertFalse(report['complete_reference_coverage'])

    def test_csv_flags_and_missing_cells_are_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder)/'a.csv', Path(folder)/'b.csv'
            a.write_text('mode,flag,x\nreset,0,1.0\nrecovery,1,\n')
            b.write_text('mode,flag,x\nreset,1,1.0\nrecovery,1,2.0\n')
            errors, _ = compare_csv(a, b, 2e-7, 1e-8)
            self.assertEqual(len(errors), 2)


if __name__ == '__main__':
    unittest.main()
