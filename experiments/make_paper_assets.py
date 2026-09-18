#!/usr/bin/env python3
"""Regenerate the compact manuscript's tables, figures, and numeric checks."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import beta as beta_dist
import mpc_core as r

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'experiments'/'results'; TAB=ROOT/'tables'; FIG=ROOT/'figures'
for directory in [TAB,FIG]: directory.mkdir(exist_ok=True)
def load(path): return json.loads((RES/path).read_text())
def write_table(name,columns,head,rows):
    text='% Generated from experiments/results by experiments/make_paper_assets.py.\n'
    text+=r'\begin{tabular}{'+columns+'}\n'+r'\toprule'+'\n'
    text+=' & '.join(head)+r' \\'+'\n'+r'\midrule'+'\n'
    text+=''.join(' & '.join(row)+r' \\'+'\n' for row in rows)
    text+=r'\bottomrule'+'\n'+r'\end{tabular}'+'\n'
    (TAB/name).write_text(text)

p=r.make_plant('A')
methods=[('collective_compatible','Compatibility-first'),('calibrate_then_close','Calibrate then close'),
 ('global_compatible','Global, compatible'),('bonferroni','Bonferroni atlas'),
 ('scenario','Scenario-box atlas'),('noedge','No-edge diagnostic')]
A={key:load(f'A/seed_0/{key}_summary.json') for key,_ in methods}
grid={o['method']:o['weighted_feasible_pct'] for o in load('feasible_grid/summary.json')}
rows=[]
for key,label in methods:
    s=A[key]
    rows.append([label,f"{s['cost_mean']:.3f}",f"{s['horizon_escape_pct']:.4f}",
        f"{s['worst_context_test_pct']:.4f}",f"{s['state_tightening_pct']:.2f}",
        f"{s['input_tightening_pct']:.2f}",f'{grid[key]:.2f}' if key in grid else '--'])
write_table('benchmark_A.tex','lrrrrrr',['Method','Cost','Horizon','Test','$X$ tight.','$U$ tight.','Feas.'],rows)
rows=[]
for key,label,delta in [('collective_compatible','Collective score',r'$\delta/3$'),
 ('bonferroni','Bonferroni box',r'$\delta/48$'),('scenario','Scenario box',r'$\delta/3$')]:
    c=load(f'A/seed_0/{key}_atlas.json')['charts'][0]
    rows.append([label,f"{c['used_calibration_samples']:,}",delta,str(c['discard_count']),
      f"{c['certified_risk']:.9f}",f"{A[key]['risk_spent_max']:.6f}",f"{A[key]['budget_final_min']:.6f}"])
write_table('calibration_budget_A.tex','lrrrrrr',
 ['Construction','$N$ used','Confidence','$s$','Chart charge',r'$\sum_k p_k$','$B_T$'],rows)

sweep=pd.read_csv(RES/'B'/'shift_sweep.csv');rows=[]
for o in sweep.to_dict('records'):
    ok=o['status']=='admissible'
    rows.append([f"{o['Gamma']:,.0f}",f"{100*o['maximum_heavy_weight']:.2f}",
      f"{o['minimum_calibration_samples']:,.0f}",
      f"{o['corrected_input_tightening_pct']:.2f}" if ok else '--',
      f"{o['uncorrected_test_pct']:.4f}",f"{o['corrected_test_pct']:.4f}" if ok else '--',
      f"{o['risk_spent']:.6f}" if ok else 'Reject'])
write_table('shift_sweep.tex','rrrrrrr',
 [r'$\Gamma$',r'$100\alpha_{\max}$',r'$N_{\min}$','$U$ tight.','Uninflated','Corrected',r'$\sum_k p_k$'],rows)

# Plot each scientific figure on its own axes with default plotting colors.
fig,ax=plt.subplots(figsize=(6.1,2.85))
for key,label in methods[:5]:
    atlas=load(f'A/seed_0/{key}_atlas.json')
    sections=np.array([c['S'] for c in atlas['charts']])
    ax.plot(np.arange(1,p.H+1),sections[:,1:,0].mean(axis=0),marker='o',markersize=3,label=label)
ax.set(xlabel='Prediction step',ylabel='Position half-width',xticks=np.arange(1,9))
ax.legend(fontsize=8,ncol=2,loc='upper left')
ax.grid(True,alpha=.22);fig.tight_layout();fig.savefig(FIG/'benchmark_A_tightening.pdf');plt.close(fig)

fig,ax=plt.subplots(figsize=(6.1,2.65))
ax.plot(sweep.Gamma,sweep.uncorrected_test_pct,marker='o',label='Uninflated diagnostic')
a=sweep[sweep.status=='admissible']
ax.plot(a.Gamma,a.corrected_test_pct,marker='s',label='Shift-corrected atlas')
ax.axhline(.4,linestyle='--',label='Target 0.4%')
ax.set_xscale('log');ax.set(xlabel=r'Trajectory likelihood bound $\Gamma$',ylabel='Worst conditional escape (%)')
ax.legend(fontsize=8);ax.grid(True,alpha=.22);fig.tight_layout();fig.savefig(FIG/'benchmark_B_shift.pdf');plt.close(fig)

# Auditable calculations supporting the compact text (no extra experiments).
scalar=int(np.ceil(np.log(.001/3)/np.log1p(-.004)))
bonf=int(np.ceil(np.log(.001/48)/np.log1p(-.004/16)))
scenario=r.scenario_n(16,.004,.001/3,50000)[0]
big=load('B/Gamma_59049/uninflated_summary.json')
intervals=[]
for rate in big['test_rates']:
    m=round(rate*80000)
    # Bonferroni allocation across two two-sided intervals: tail probability .0125.
    intervals.append([float(beta_dist.ppf(.0125,m,80000-m+1)),float(beta_dist.ppf(.9875,m+1,80000-m))])
rep=[]
for off in [0,30000,40000,50000]:
    row={'offset':off}
    for key,label in methods[:5]:
        z=load(f'A/seed_{off}/{key}_summary.json')
        row[key]={q:z[q] for q in ['cost_mean','state_tightening_pct','input_tightening_pct','horizon_escape_pct','worst_context_test_pct','state_violation_count','reset_failure_count']}
    rep.append(row)
checks={'minimum_calibration_counts':{'scalar':scalar,'scenario':scenario,'bonferroni':bonf},
 'strong_shift_simultaneous_95pct_intervals':intervals,'replications':rep}
(RES/'paper_numeric_checks.json').write_text(json.dumps(checks,indent=2))
print('Generated three tables and two figures. Minimum counts:',scalar,scenario,bonf)
