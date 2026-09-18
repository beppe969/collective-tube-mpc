# Experimental protocol

This description follows Section 8 of the current manuscript and the preserved experiment scripts. Exact plant matrices and all fixed parameters are mirrored in [`config/paper.json`](../config/paper.json). The JSON file is a documentation/validation mirror; editing it alone does not alter the numerical engine.

## Common model and timing

Both plants obey

\[
x_{k+1}=Ax_k+Bu_k+w_k,\qquad A_K=A+BK.
\]

The horizon has length `H`; a mission contains `T=22` applied control steps in the main comparisons. The exogenous context is an observed finite-state Markov chain. Its current value is known when planning begins, and it continues to evolve over the prediction horizon. `mpc_core.py:paths()` generates the complete context paths together with the Gaussian innovations and the mixture uniforms.

A calibration observation is the array `(e_1,...,e_H)`, obtained by starting at `e_0=0` and applying `e_{t+1}=A_K e_t+w_t`. Thus each observation has shape `(H,2)`. Dependence across time inside one observation is allowed; the simulation generator creates independent trajectories within each context-specific sample.

Design, calibration, and testing use separate seeded streams. The main protocol uses 1,800 design trajectories, 50,000 calibration trajectories, and 80,000 test trajectories per context. The trajectory-risk target is `beta=0.004`, and the confidence allowance is `delta=0.001` for each method and experiment. A confidence statement covering every experiment jointly would need an additional allocation.

Each main comparison uses 120 missions with paired initial states and primitive randomness. The initial context has the stationary distribution of the relevant chain. Benchmark A initial states are uniform on `[-6,6] × [-0.6,0.6]`; Benchmark B uses `[-3.2,3.2] × [-0.5,0.5]`. The default mission budget is `0.1`.

## Tube constructions

### Compatibility-first collective atlas

For each context, the independent design trajectories determine root-mean-square half-widths, floored at `1e-8`. The algorithm enlarges these preliminary sections so that every proposed cross-chart transition satisfies the deterministic inclusion conditions.

Calibration then evaluates the maximum normalized absolute coordinate over the entire residual trajectory. For a sample count `N`, the discard count is fixed as the largest integer `s` with

\[
\Pr\{\operatorname{Bin}(N,\beta)\le s\}\le\delta/G.
\]

The threshold is the `(N-s)`-th order statistic, which is index `N-s-1` in a zero-based sorted array. The common final scale is the maximum of the context thresholds. Applying that same scale to every compatible template preserves the cross-chart inclusions. Terminal conditions are checked after calibration.

The charged probability is the corresponding beta-quantile upper bound, rather than the empirical number of misses divided by the sample count. It may be slightly below the nominal target because of the integer rank selection.

### Calibrate-then-close and no-edge diagnostics

The calibrate-then-close construction calibrates the raw design-sample score and subsequently enlarges its boxes for compatibility. The no-edge diagnostic keeps the raw calibrated boxes. Its candidate transitions fail the inclusion tests, so its successful sampled trajectories carry no atlas-level recursive-feasibility certificate.

### Global compatible geometry

The global comparator starts from the componentwise maximum of the context-specific RMS templates. It then applies the same compatibility-first procedure and calibrates against every conditional law. This differs from calibrating only a pooled stationary mixture. The pooled-mixture experiment is a separate diagnostic.

### Bonferroni and scenario boxes

The Bonferroni construction has `d=2H` absolute-coordinate margins. Each margin receives risk `beta/d` and confidence `delta/(Gd)`. The charged risk is the sum of their beta-quantile bounds. The construction uses 50,000 calibration trajectories per context.

The scenario box contains the first `N_s` complete trajectories by taking coordinatewise absolute maxima. The code chooses the smallest sample count satisfying the dimension-`d` scenario bound at confidence `delta/G`. For Benchmark A, `d=16` and `N_s=8,295`. Both coordinatewise constructions undergo edge closure and terminal validation.

These are the specific implementations compared in the manuscript. A different score family or scenario parameterization can change their geometric ranking.

## Data fairness and replication

The equal-total-data experiment gives both methods the identical pool of 8,295 trajectories per context. The scenario box uses the whole pool for its maxima. The collective construction uses entries `0:1800` for design and `1800:8295` for calibration, leaving 6,495 independent calibration trajectories. These Python slices are half-open. No external design trajectories are added in this comparison.

Four full-calibration runs use offsets `0`, `30000`, `40000`, and `50000`. Every offset changes the design and calibration samples. Its test and mission streams are also independent of the other offsets. Within an offset, methods use paired streams. The equal-total-data and no-edge diagnostics are included only at offset zero.

## Optimization and evaluation

The ancillary gain is fixed at the paper's `K`, and `K_f=K`. The terminal cost matrix solves the discrete Lyapunov equation given in Section 8.1. The terminal set is a common parallelogram computed from the closed-loop eigencoordinates. This construction is specialized to two-dimensional plants with the complex-root structure checked in the code.

The condensed objective is a strictly convex quadratic function. SLSQP solves it with analytic derivatives and `ftol=1e-10`. An accepted solution must terminate successfully and have a maximum primal violation at most `2e-7`. The code uses an independent HiGHS linear-program feasibility check when the initial optimization attempt is unsuccessful. Its feasible point is then used for a second optimization attempt.

Mission cost is the mean realized sum of stage costs. The state-tightening measure averages box half-widths divided by the state bounds over prediction steps `1,...,H` and state coordinates. The input-tightening measure averages `|K|s_t/u_max` over steps `0,...,H-1`. Mission averages use the charts actually selected by the controller.

A horizon-escape indicator is evaluated using the selected ancillary continuation, coupled to the actual first disturbance. In Benchmark B its future state/input-dependent disturbance kernel is evaluated along that continuation's own path. Receding-horizon indicators overlap in time, so their observed frequency is not treated as an independent-binomial sample. The logs distinguish first-error escape from physical state/input violations.

The feasible-domain diagnostic solves LPs on a `61 × 41` grid in the Benchmark A state box. Its headline percentage is the stationary-context-weighted fraction of feasible grid points. This is a deterministic grid statistic.

## Mission budget diagnostics

The contextual budget experiment has two risk targets per context:

| Context | Higher risk | Lower risk |
|---|---:|---:|
| 0 | 0.0040 | 0.0012 |
| 1 | 0.0037 | 0.0015 |
| 2 | 0.0031 | 0.0018 |

The design-sample quantiles differentiate the six preliminary templates before common closure and calibration. Confidence is allocated as `delta/6`. The selector uses the QP objective plus `1e-3` times the sum of the chart's half-widths. A 40-mission study starts from budget `0.065`, enforcing the continuation reserve at every certified decision. Every risk charge is paid even when the realized disturbance is contained.

The greedy comparison uses only current affordability and starts from budget `0.02`. It runs out of budget after five contained steps. The reserve-based admission test rejects the same 22-step mission before applying an input. Both outcomes are retained.

## Recovery stress test

The recovery experiment starts from `(1,0.1)` and adds `(6.5,3)` to the disturbance at zero-based step `k=3`. At `k=4`, the measured state is still inside the physical state box but fails measured-state MPC initialization. The controller enters nominal recovery using the preceding predicted nominal state.

The simulator records 14 feasible recovery QPs. Applied inputs are projected into the input interval; four subsequent states violate the state constraints. Statistical charging ends when recovery begins. This artificial-shock experiment is excluded from stochastic coverage estimates, and its nominal feasibility should be interpreted separately from physical state safety.

## Benchmark B: controlled deployment shift

The reference residual noise is a two-component Gaussian mixture. The heavy component scales the innovation by three and has probability `alpha0=0.05`. Deployment uses

\[
\alpha_\star(x,u)=\alpha_0\bigl[1+(\Gamma^{1/H}-1)
\tanh((x_1/2)^2+(x_2/1.5)^2+(u/2)^2)\bigr].
\]

The mixture-weight ratios give the uniform trajectory likelihood bound `Gamma`. The sweep uses `1`, `3`, `10`, `25`, `100`, and `59049`. The corrected construction calibrates at reference risk `beta/Gamma`, then multiplies its certified reference-law escape bound by `Gamma` for mission charging.

The conditional tests use 80,000 independent trajectories per context with nominal `K`-feedback tails and specified initial-state ranges. The theorem's uniform guarantee comes from the likelihood-ratio argument. The empirical test examines those particular tails.

At `Gamma=3`, both variants use 120 missions; the other settings use 40. The same reference samples and paired primitive test streams are retained across the sweep. Corrected designs at `Gamma=100` and `Gamma=59049` are rejected because 50,000 calibration trajectories are insufficient. Their corrected performance cells remain empty.

The uninflated runs are diagnostic at `Gamma>1`. The common simulation loop logs their internal operating mode as `certified_reset`, but that label does not supply a shifted-law certificate. `legitimate_deployment_risk` and `legitimate_required_budget` expose the charge that the uniform shift bound would justify. The manuscript retains the resulting undercoverage and excessive-budget cases.
