#!/usr/bin/env python3
"""Reproduce the compact revision rebuilt from the original submission.

Each construction has confidence allowance delta=0.001 per experiment.
The grid is a deterministic feasibility diagnostic, not a probability experiment.
Run `python make_paper_assets.py` afterwards to regenerate manuscript assets.
"""
from __future__ import annotations
import argparse, hashlib, json, platform, sys, time
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import linprog
import mpc_core as r
from compatible import build

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments'/'results'
BETA=.004; DELTA=.001; T=22; EPSILON=.1
NDES=1800; NCAL=50000; NTEST=80000; MISSIONS=120
OFFSETS=[0,30000,40000,50000]
SHIFT_FACTORS=[1.,3.,10.,25.,100.,3.**10]


def dump(obj,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False))


def datasets(p,offset=0,test=True):
    design=[r.calibration_trajectories(p,NDES,offset+1100+g,g) for g in range(p.ng)]
    cal=[r.calibration_trajectories(p,NCAL,offset+2100+g,g) for g in range(p.ng)]
    Etest=[r.calibration_trajectories(p,NTEST,offset+3100+g,g) for g in range(p.ng)] if test else None
    return design,cal,Etest


def hashes(arrays):
    return [hashlib.sha256(x.tobytes()).hexdigest() for x in arrays]


def save_run(atlas,folder,stem,seed,nmissions=MISSIONS,epsilon=EPSILON,horizon=T,Etest=None,**kwargs):
    frame,summary=r.run_missions(atlas,nmissions,horizon,epsilon,seed,**kwargs)
    if Etest is not None:
        rates=r.contextual_test_A(atlas,Etest)
        summary.update(test_rates=rates,worst_context_test_pct=100*max(rates))
    summary['audit']=atlas.audit
    folder.mkdir(parents=True,exist_ok=True)
    frame.to_csv(folder/f'{stem}_missions.csv',index=False)
    dump(r.serialize_atlas(atlas),folder/f'{stem}_atlas.json')
    dump(summary,folder/f'{stem}_summary.json')
    print(stem,'completed',summary['completed_missions'],'cost',summary.get('cost_mean'),
          'tightenings',summary.get('state_tightening_pct'),summary.get('input_tightening_pct'),flush=True)
    return summary


def study_A():
    p=r.make_plant('A'); all_rows=[]; data_manifest={}
    for off in OFFSETS:
        design,cal,Etest=datasets(p,off)
        folder=OUT/'A'/f'seed_{off}'
        data_manifest[str(off)]={'design_hashes':hashes(design),'calibration_hashes':hashes(cal),
                                 'test_hashes':hashes(Etest),'mission_seed':off+5100}
        methods={
            'collective_compatible':build(p,design,cal),
            'calibrate_then_close':r.build_atlas(p,'collective',design,cal,BETA,DELTA),
            'global_compatible':build(p,design,cal,global_geometry=True),
            'bonferroni':r.build_atlas(p,'bonferroni',design,cal,BETA,DELTA),
            'scenario':r.build_atlas(p,'scenario',design,cal,BETA,DELTA)}
        if off==0:
            methods['noedge']=r.build_atlas(p,'noedge',design,cal,BETA,DELTA)
            # Equal TOTAL data: both methods receive exactly the same 8,295
            # trajectories per context. The scalar method reserves the first
            # 1,800 for design and uses the independent suffix for calibration.
            methods['collective_equal_total']=build(p,[x[:NDES] for x in cal],
                [x[NDES:8295] for x in cal],name='collective_equal_total')
        for name,atlas in methods.items():
            if name!='noedge': atlas.name=name
            summary=save_run(atlas,folder,name,off+5100,Etest=Etest)
            summary['seed_offset']=off; all_rows.append(summary)
    dump(all_rows,OUT/'A'/'all_summaries.json')
    dump(data_manifest,OUT/'A'/'data_manifest.json')


def study_mixture():
    p=r.make_plant('A'); _,_,Etest=datasets(p)
    des=r.calibration_trajectories(p,NDES,7100,None); cal=r.calibration_trajectories(p,NCAL,7200,None)
    shape=np.sqrt(np.mean(des**2,axis=0)); s,ub=r.order_parameter(NCAL,BETA,DELTA)
    scores=np.max(np.abs(cal)/shape,axis=(1,2)); rho=float(np.partition(scores,NCAL-s-1)[NCAL-s-1])
    rates=[float(np.mean(np.any(np.abs(E)>rho*shape,axis=(1,2)))) for E in Etest]
    dump({'initial_mode_weights':r.stationary(p.transition).tolist(),'mixture_certificate':ub,
          'conditional_escape_rates':rates,'mixture_weighted_test_rate':float(r.stationary(p.transition)@rates)},
          OUT/'mixture_diagnostic.json')


def study_budget():
    p=r.make_plant('A'); design,cal,_=datasets(p,test=False)
    levels=[[.004,.0012],[.0037,.0015],[.0031,.0018]]
    atlas=build(p,design,cal,context_levels=levels,name='reserve_contextual')
    summary=save_run(atlas,OUT/'budget','reserve_contextual',9100,nmissions=40,epsilon=.065)
    df=pd.read_csv(OUT/'budget'/'reserve_contextual_missions.csv');df['level']=df['chart'].astype(int)%2
    spending=df.groupby('mission')['risk'].sum()
    schedules=df.groupby('mission')['level'].apply(lambda x:tuple(x)).tolist()
    counts=df.groupby('mission')['level'].apply(lambda x:int((x==0).sum()))
    summary.update(context_risk_targets=levels,distinct_level_schedules=len(set(schedules)),
                   high_risk_steps_min=int(counts.min()),high_risk_steps_max=int(counts.max()),
                   total_risk_min=float(spending.min()),total_risk_max=float(spending.max()),
                   budget_guard_min_slack=float((df['budget_before']-df['risk']-df['reserve']).min()))
    dump(summary,OUT/'budget'/'reserve_contextual_summary.json')
    base=build(p,design,cal)
    save_run(base,OUT/'budget','greedy',10100,nmissions=1,epsilon=.02,reserve_guard=False,tag='greedy')
    save_run(base,OUT/'budget','preflight',10100,nmissions=1,epsilon=.02,tag='preflight')


def study_recovery():
    p=r.make_plant('A'); design,cal,_=datasets(p,test=False); atlas=build(p,design,cal)
    for name,vector in [('interior_shock',[6.5,3.])]:
        summary=save_run(atlas,OUT/'recovery',name,11100,nmissions=1,horizon=18,shock_vector=vector,tag=name)
        df=pd.read_csv(OUT/'recovery'/f'{name}_missions.csv');entry=df.query('reset_failed == 1').iloc[0]
        summary.update(shock_vector=vector,recovery_entry_step=int(entry.k),
                       recovery_entry_state=[float(entry.x0),float(entry.x1)],
                       recovery_entry_inside_X=bool(abs(entry.x0)<=p.xmax[0] and abs(entry.x1)<=p.xmax[1]))
        dump(summary,OUT/'recovery'/f'{name}_summary.json')


def study_B():
    base=r.make_plant('B'); design,cal,_=datasets(base,100000,test=False)
    manifest={'design':hashes(design),'calibration':hashes(cal),'factors':SHIFT_FACTORS}; rows=[]
    for Gamma in SHIFT_FACTORS:
        p=replace(base,gamma=Gamma); folder=OUT/'B'/f'Gamma_{Gamma:g}'
        uncorrected=build(p,design,cal,correct_shift=False,name='uninflated')
        unctest=r.diagnostic_B(uncorrected,NTEST,104100)
        unc=save_run(uncorrected,folder,'uninflated',105100,nmissions=MISSIONS if Gamma==3 else 40)
        unc.update(Gamma=Gamma,test_rates=unctest,worst_context_test_pct=100*max(unctest),
                   legitimate_deployment_risk=min(1.,Gamma*uncorrected.charts[0].risk),
                   legitimate_required_budget=T*min(1.,Gamma*uncorrected.charts[0].risk))
        dump(unc,folder/'uninflated_summary.json')
        row={'Gamma':Gamma,'one_step_ratio':Gamma**(1/p.H),'maximum_heavy_weight':p.alpha0*Gamma**(1/p.H),
             'minimum_calibration_samples':int(np.ceil(np.log(DELTA/p.ng)/np.log1p(-BETA/Gamma))),
             'uncorrected_test_pct':100*max(unctest),'uncorrected_legitimate_budget':unc['legitimate_required_budget'],
             'uncorrected_state_tightening_pct':unc['state_tightening_pct'],
             'uncorrected_input_tightening_pct':unc['input_tightening_pct']}
        try:
            corrected=build(p,design,cal,correct_shift=True,name='shift_corrected')
            corrtest=r.diagnostic_B(corrected,NTEST,104100)
            corr=save_run(corrected,folder,'shift_corrected',105100,nmissions=MISSIONS if Gamma==3 else 40)
            corr.update(Gamma=Gamma,test_rates=corrtest,worst_context_test_pct=100*max(corrtest))
            dump(corr,folder/'shift_corrected_summary.json')
            row.update(status='admissible',corrected_test_pct=100*max(corrtest),
                       corrected_state_tightening_pct=corr['state_tightening_pct'],
                       corrected_input_tightening_pct=corr['input_tightening_pct'],
                       risk_spent=corr['risk_spent_max'],completed=corr['completed_missions'])
        except ValueError as exc:
            row.update(status='sample_rejected' if 'sample size' in str(exc) else 'geometry_rejected',reason=str(exc))
        rows.append(row); print('shift sweep',row,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'B'/'shift_sweep.csv',index=False); dump(manifest,OUT/'B'/'data_manifest.json')


def load_atlas(path,p):
    o=json.loads(path.read_text())
    charts=[r.Chart(c['name'],c['g'],np.array(c['raw']),np.array(c['S']),c['certified_risk'],
                    c['radius'] if c['radius'] is not None else float('nan'),c['used_calibration_samples'],c['discard_count']) for c in o['charts']]
    return r.Atlas(o['name'],p,charts,np.array(o['edges'],bool),np.array(o['terminal_F']),np.array(o['terminal_b']),o['audit'])


def study_grid():
    p=r.make_plant('A'); grid=np.array([(x,v) for x in np.linspace(-8,8,61) for v in np.linspace(-4,4,41)]);rows=[]
    for name in ['collective_compatible','calibrate_then_close','global_compatible','bonferroni','scenario']:
        atlas=load_atlas(OUT/'A'/'seed_0'/f'{name}_atlas.json',p);mpc=r.MPC(atlas);masks=[]
        for j,c in enumerate(atlas.charts):
            C,b,D=mpc.data[j];mask=[]
            for point in grid:
                result=linprog(np.zeros(p.H),A_ub=C,b_ub=b-D@point,bounds=[(None,None)]*p.H,method='highs')
                if result.status not in (0,2): raise RuntimeError(f'Unexpected grid LP status {result.status}: {result.message}')
                if result.success and np.max(C@result.x-(b-D@point))>2e-7: raise AssertionError('LP primal residual failed.')
                mask.append(bool(result.success))
            masks.append(np.array(mask))
        weighted=float(r.stationary(p.transition)@np.mean(masks,axis=1))
        rows.append({'method':name,'points_per_context':len(grid),'weighted_feasible_pct':100*weighted,
                     'context_feasible_pct':(100*np.mean(masks,axis=1)).tolist()})
        folder=OUT/'feasible_grid';folder.mkdir(parents=True,exist_ok=True)
        pd.DataFrame({'position':grid[:,0],'velocity':grid[:,1],**{f'context_{g}':masks[g] for g in range(p.ng)}}).to_csv(folder/f'{name}.csv',index=False)
        print('feasible grid',name,weighted,flush=True)
    dump(rows,OUT/'feasible_grid'/'summary.json')


def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',choices=['all','A','budget','recovery','B','grid','mixture'],default='all')
    parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
    studies={'A':study_A,'mixture':study_mixture,'budget':study_budget,'recovery':study_recovery,'B':study_B,'grid':study_grid}
    start=time.perf_counter()
    for name,func in studies.items():
        if args.study in ['all',name]: print('START',name,flush=True);func()
    manifest={'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pd.__version__,
              'platform':platform.platform(),'study':args.study,'elapsed_seconds':time.perf_counter()-start,
              'N_design':NDES,'N_calibration':NCAL,'N_test':NTEST,'main_missions':MISSIONS,'T':T,'epsilon':EPSILON,
              'beta':BETA,'delta_per_method_per_experiment':DELTA,'replication_offsets':OFFSETS,
              'shift_factors':SHIFT_FACTORS,
              'script_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}}
    dump(manifest,OUT/f'run_manifest_{args.study}.json');print('COMPLETE',manifest['elapsed_seconds'],'seconds',flush=True)

if __name__=='__main__': main()
