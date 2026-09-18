"""Design-stage box closure followed by a single jointly valid calibration scale.

The common scale is essential: independent final scales generally destroy the
cross-chart inclusions. Terminal conditions are checked after calibration.
"""
from __future__ import annotations
import numpy as np
import mpc_core as r


def build(p:r.Plant, design:list[np.ndarray], cal:list[np.ndarray], risk:float=.004,
          delta:float=.001, global_geometry:bool=False, correct_shift:bool=True,
          context_levels:list[list[float]]|None=None, name:str|None=None)->r.Atlas:
    if len(design)!=p.ng or len(cal)!=p.ng:
        raise ValueError('One independent design/calibration array per context is required.')
    levels = [[risk] for _ in range(p.ng)] if context_levels is None else context_levels
    if len(levels)!=p.ng or any(not v for v in levels):
        raise ValueError('Every context must have at least one risk level.')
    nc=sum(map(len,levels)); confidence=delta/nc
    shapes=[np.maximum(np.sqrt(np.mean(E**2,axis=0)),1e-8) for E in design]
    if global_geometry:
        common=np.max(shapes,axis=0)
        shapes=[common.copy() for _ in range(p.ng)]
    charts=[]; targets=[]
    for g,levs in enumerate(levels):
        for lev in levs:
            if not 0<lev<1: raise ValueError('Risk targets must lie in (0,1).')
            shape=shapes[g].copy()
            # Multiple templates may be learned on the design split. No
            # calibration values are used to determine these shapes.
            if len(levs)>1:
                score=np.max(np.abs(design[g])/shape,axis=(1,2))
                shape *= float(np.quantile(score,1-lev,method='higher'))
            S=np.vstack([np.zeros(p.A.shape[0]),shape])
            charts.append(r.Chart(f'{g}:{lev:g}',g,S.copy(),S.copy(),0.,0.,0,0))
            targets.append(lev)
    r.close_edges(charts,p.AK)
    templates=[c.S.copy() for c in charts]
    factor=p.gamma if correct_shift else 1.
    thresholds=[]
    for c,lev in zip(charts,targets):
        n=len(cal[c.g]); s,rr=r.order_parameter(n,lev/factor,confidence)
        scores=np.max(np.abs(cal[c.g])/c.S[None,1:,:],axis=(1,2))
        thresholds.append(float(np.partition(scores,n-s-1)[n-s-1]))
        c.risk=min(1.,factor*rr); c.count=n; c.discards=s
    rho=max(thresholds)
    for c in charts:
        c.S*=rho; c.raw=c.S.copy(); c.radius=rho
    terminal_F,terminal_b,audit=r.terminal_geometry(p,charts)
    edges=np.zeros((nc,nc),dtype=bool); minimum=float('inf'); failed=0
    for i,c in enumerate(charts):
        for j,d in enumerate(charts):
            slack=np.array([c.S[t+1]-np.abs(np.linalg.matrix_power(p.AK,t))@c.S[1]-d.S[t]
                            for t in range(p.H)])
            minimum=min(minimum,float(slack.min())); failed+=int(np.sum(slack < -1e-10))
            edges[i,j]=bool(slack.min()>=-1e-10)
    if not edges.all(): raise AssertionError('Common-scale closure failed edge verification.')
    audit.update(cross_section_slack_min=minimum,failed_scalar_cross_section_inequalities=failed,
                 edge_pairs=nc*nc,verified_edge_pairs=int(edges.sum()),all_terminal_conditions_checked=True,
                 template_sections=[s.tolist() for s in templates],context_thresholds=thresholds,
                 common_scale=rho,confidence_per_chart=confidence,risk_targets=targets,
                 construction='compatibility_first')
    name=name or ('global_compatible' if global_geometry else 'collective_compatible')
    return r.Atlas(name,p,charts,edges,terminal_F,terminal_b,audit)
