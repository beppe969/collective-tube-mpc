"""Compare regenerated quantities with the included 33-page reference paper.

The printed targets below were transcribed from Tables 1--3 and Section 8,
then checked against the rendered PDF. Targets are independent of the archived
JSON/CSV files. A printed decimal allows half a unit in its final decimal place;
integer event counts and categorical outcomes are checked exactly.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd
from tools.common import load_json


def check_paper(results: Path) -> dict:
    entries: list[dict] = []
    errors: list[str] = []

    def check(name, actual, expected, source, rounded=False):
        if isinstance(actual, np.generic):
            actual = actual.item()
        tolerance = 0.0
        if rounded:
            exponent = Decimal(str(expected)).as_tuple().exponent
            tolerance = .5 * 10.**exponent + 1e-12
            ok = bool(np.isfinite(actual) and abs(float(actual)-float(expected)) <= tolerance)
        else:
            ok = bool(actual == expected)
        row = {'quantity': name, 'paper_location': source, 'paper_value': expected,
               'recomputed_value': actual, 'absolute_tolerance': tolerance, 'ok': ok}
        entries.append(row)
        if not ok:
            errors.append(f'{source}: {name}: expected {expected}, got {actual}')

    def rounded(name, actual, expected, source):
        check(name, actual, expected, source, rounded=True)

    def read(rel):
        return load_json(results / rel)

    try:
        A = {name: read(f'A/seed_0/{name}_summary.json') for name in
             ('collective_compatible','calibrate_then_close','global_compatible',
              'bonferroni','scenario','noedge','collective_equal_total')}
        # Table 1, page 25: N, s, risk charge, spending, final balance.
        expected = {
            'collective_compatible': (50000,153,'0.003993875','0.087865','0.012135'),
            'bonferroni': (50000,0,'0.003448894','0.075876','0.024124'),
            'scenario': (8295,0,'0.003999847','0.087997','0.012003')}
        for name, values in expected.items():
            c = read(f'A/seed_0/{name}_atlas.json')['charts'][0]
            for field, value in zip(('used_calibration_samples','discard_count'),values[:2]):
                check(f'{name}/{field}',c[field],value,'Table 1, p.25')
            for field, actual, target in zip(('risk','spending','balance'),
                (c['certified_risk'],A[name]['risk_spent_max'],A[name]['budget_final_min']),values[2:]):
                rounded(f'{name}/{field}',actual,target,'Table 1, p.25')
        # Table 2, page 26. Percent units are as printed in the paper.
        table2 = {
            'collective_compatible':['25.879','0.2652','0.2988','5.10','25.82','88.01'],
            'calibrate_then_close':['25.912','0.0000','0.0000','9.33','47.42','81.02'],
            'global_compatible':['25.929','0.0000','0.3425','5.68','29.44','86.81'],
            'bonferroni':['25.887','0.0000','0.0037','7.01','35.50','86.83'],
            'scenario':['25.884','0.0000','0.0325','6.46','32.60','87.38'],
            'noedge':['25.890','0.1894','0.3387','2.16','11.30',None]}
        grid = {s['method']:s['weighted_feasible_pct'] for s in read('feasible_grid/summary.json')}
        fields = ('cost_mean','horizon_escape_pct','worst_context_test_pct',
                  'state_tightening_pct','input_tightening_pct')
        for name,values in table2.items():
            for field,target in zip(fields,values[:5]):
                rounded(f'{name}/{field}',A[name][field],target,'Table 2, p.26')
            if values[5] is not None:
                rounded(f'{name}/feasible_pct',grid[name],values[5],'Table 2, p.26')
            for field,target in (('completed_missions',120),('steps',2640),
                                 ('state_violation_count',0),('input_violation_count',0),
                                 ('reset_failure_count',0),('budget_exhaustions',0)):
                check(f'{name}/{field}',A[name][field],target,'Section 8.2, pp.25-26')
            atlas = read(f'A/seed_0/{name}_atlas.json')
            check(f'{name}/verified_edges',atlas['audit']['verified_edge_pairs'],
                  0 if name=='noedge' else 9,'Section 8.2, pp.25-26')
        c = A['collective_compatible']
        check('collective/first_error_escapes',c['first_escape_count'],7,'Section 8.2, p.25')
        check('collective/horizon_escapes',round(c['horizon_escape_pct']/100*c['steps']),7,'Section 8.2, p.25')
        for g,target in enumerate(('0.29875','0.29625','0.27750')):
            rounded(f'collective/context_{g}_test_pct',100*c['test_rates'][g],target,'Section 8.2, p.25')
        check('noedge/failed_scalar_inclusions',read('A/seed_0/noedge_atlas.json')['audit']['failed_scalar_cross_section_inequalities'],89,'Section 8.2, p.26')
        num = read('paper_numeric_checks.json')
        for name,target in (('scalar',1998),('scenario',8295),('bonferroni',43111)):
            check(f'minimum_calibration/{name}',num['minimum_calibration_counts'][name],target,'Section 8.2, p.25')
        fair=A['collective_equal_total']
        for field,target in (('state_tightening_pct','5.41'),('input_tightening_pct','27.37'),
             ('cost_mean','25.880'),('risk_spent_max','0.087618'),('budget_final_min','0.012382')):
            rounded('equal_total/'+field,fair[field],target,'Data fairness, p.26')
        fair_chart=read('A/seed_0/collective_equal_total_atlas.json')['charts'][0]
        check('equal_total/calibration_count',fair_chart['used_calibration_samples'],6495,'Data fairness, p.26')
        rounded('equal_total/risk',fair_chart['certified_risk'],'0.003982643','Data fairness, p.26')
        reps=[read(f'A/seed_{off}/collective_compatible_summary.json') for off in (0,30000,40000,50000)]
        for field,lo,hi in (('state_tightening_pct','5.05','5.14'),('input_tightening_pct','25.54','26.02')):
            rounded('replication/min_'+field,min(s[field] for s in reps),lo,'Replication, p.26')
            rounded('replication/max_'+field,max(s[field] for s in reps),hi,'Replication, p.26')
        check('replication/completed_missions',sum(s['completed_missions'] for s in reps),480,'Replication, p.26')
        for field in ('state_violation_count','reset_failure_count'):
            check('replication/'+field,sum(s[field] for s in reps),0,'Replication, p.26')
        rounded('replication/max_horizon_escape_pct',max(s['horizon_escape_pct'] for s in reps),'0.5682','Replication, p.26')
        check('replication/all_conditional_test_rates_below_target',all(s['worst_context_test_pct'] < .4 for s in reps),True,'Replication, p.26')
        mixture=read('mixture_diagnostic.json')
        for g,target in enumerate(('0.88394','0.09109','0.02497')):
            rounded(f'mixture/stationary_{g}',mixture['initial_mode_weights'][g],target,'Conditional calibration, p.27')
        rounded('mixture/pooled_escape_pct',100*mixture['mixture_weighted_test_rate'],'0.3387','Conditional calibration, p.27')
        rounded('mixture/rare_mode_escape_pct',100*mixture['conditional_escape_rates'][2],'8.4013','Conditional calibration, p.27')
        budget=read('budget/reserve_contextual_summary.json')
        for field,target in (('completed_missions',40),('distinct_level_schedules',12),
            ('state_violation_count',0),('input_violation_count',0),('first_escape_count',0)):
            check('budget/'+field,budget[field],target,'Section 8.2.1, p.27')
        check('budget/all_36_edges',budget['audit']['verified_edge_pairs'],36,'Section 8.2.1, p.27')
        for field,target in (('total_risk_min','0.062348'),('total_risk_max','0.064881'),('budget_final_min','0.000119')):
            rounded('budget/'+field,budget[field],target,'Section 8.2.1, p.27')
        greedy=read('budget/greedy_summary.json');preflight=read('budget/preflight_summary.json')
        check('greedy/contained_steps',greedy['steps'],5,'Section 8.2.1, p.27')
        check('greedy/first_error_escapes',greedy['first_escape_count'],0,'Section 8.2.1, p.27')
        rounded('greedy/spending',greedy['risk_spent_max'],'0.019969','Section 8.2.1, p.27')
        check('preflight/applied_inputs',preflight['steps'],0,'Section 8.2.1, p.27')
        check('preflight/rejected_missions',preflight['budget_rejections'],1,'Section 8.2.1, p.27')
        shock=read('recovery/interior_shock_summary.json')
        for field,target in (('recovery_entry_step',4),('recovery_entry_inside_X',True),('backup_steps',14),
                             ('state_violation_count',4),('input_violation_count',0)):
            check('recovery/'+field,shock[field],target,'Section 8.2.1, p.28')
        for j,target in enumerate(('6.4969','2.9933')):
            rounded(f'recovery/entry_state_{j}',shock['recovery_entry_state'][j],target,'Section 8.2.1, p.28')
        rounded('recovery/spending',shock['risk_spent_max'],'0.015975','Section 8.2.1, p.28')
        # Table 3, page 29: alpha_max (%), Nmin, U tightening (%), test %, spending.
        table3={
            1:('5.00',1897,'22.82','0.3162','0.3162','0.087638'),
            3:('5.58',5697,'28.17','0.3312','0.0975','0.087947'),
            10:('6.29',18999,'37.10','0.3625','0.0087','0.083830'),
            25:('6.90',47502,'48.23','0.3887','0.0013','0.083604'),
            100:('7.92',190019,None,'0.4338',None,None),
            59049:('15.00',112206419,None,'0.7388',None,None)}
        sweep=pd.read_csv(results/'B/shift_sweep.csv')
        check('shift/factor_sequence',sweep.Gamma.astype(int).tolist(),list(table3),'Table 3, p.29')
        for row in sweep.to_dict('records'):
            g=int(row['Gamma']);target=table3[g]
            rounded(f'shift_{g}/maximum_heavy_weight_pct',100*row['maximum_heavy_weight'],target[0],'Table 3, p.29')
            check(f'shift_{g}/minimum_calibration_samples',int(row['minimum_calibration_samples']),target[1],'Table 3, p.29')
            for field,t in zip(('corrected_input_tightening_pct','uncorrected_test_pct','corrected_test_pct','risk_spent'),target[2:]):
                if t is None:
                    check(f'shift_{g}/{field}_unavailable',bool(pd.isna(row[field])),True,'Table 3, p.29')
                else:
                    rounded(f'shift_{g}/{field}',row[field],t,'Table 3, p.29')
            check(f'shift_{g}/status',row['status'],'admissible' if g<100 else 'sample_rejected','Table 3, p.29')
            if g<100:
                s=read(f'B/Gamma_{g}/shift_corrected_summary.json')
                for field,t in (('completed_missions',120 if g==3 else 40),('state_violation_count',0),('reset_failure_count',0),('budget_exhaustions',0)):
                    check(f'shift_{g}/{field}',s[field],t,'Section 8.3, p.28')
        corrected=read('B/Gamma_3/shift_corrected_summary.json');uncorrected=read('B/Gamma_3/uninflated_summary.json')
        for field,t in (('state_tightening_pct','11.91'),('input_tightening_pct','28.17'),('cost_mean','10.969'),('budget_final_min','0.012053')):
            rounded('B_Gamma3/'+field,corrected[field],t,'Section 8.3, p.28')
        rounded('B_Gamma3/certified_risk',read('B/Gamma_3/shift_corrected_atlas.json')['charts'][0]['certified_risk'],'0.003997602','Section 8.3, p.28')
        for field,t in (('state_tightening_pct','9.61'),('input_tightening_pct','22.75'),('risk_spent_max','0.087638'),('legitimate_required_budget','0.262914')):
            rounded('uninflated_Gamma3/'+field,uncorrected[field],t,'Section 8.3, p.28')
        large=read('B/Gamma_59049/uninflated_summary.json')
        for g,t in enumerate(('0.59625','0.73875')):
            rounded(f'strong_shift/context_{g}_escape_pct',100*large['test_rates'][g],t,'Section 8.3, p.29')
        for g,t in enumerate(('0.5369','0.6725')):
            rounded(f'strong_shift/context_{g}_lower_CI_pct',100*num['strong_shift_simultaneous_95pct_intervals'][g][0],t,'Section 8.3, p.29')
    except (FileNotFoundError, KeyError, ValueError, IndexError, TypeError) as exc:
        errors.append(f'Incomplete or malformed result set: {exc}')
    return {'ok': not errors, 'checks': len(entries), 'reference_paper_pages':33,
            'coverage':'Tables 1-3 and numerical statements in Section 8; figures checked separately',
            'rounding_rule':'Half a unit in the final printed decimal place plus 1e-12; counts exact',
            'entries':entries,'errors':errors}
