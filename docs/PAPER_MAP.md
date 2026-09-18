# Mapping the paper to the code and results

The baseline is the latest **34-page language-edited manuscript**. Its source and PDF SHA-256 hashes are recorded in [`reference/provenance.json`](../reference/provenance.json). Section and page numbers below refer to that baseline. The numerical-section source fragment is preserved in [`reference/numerical_revision.tex`](../reference/numerical_revision.tex); it retains the paper's macros and serves as a provenance record, not a standalone LaTeX document.

## Tables and figures

| Paper item | Content | Generating study/function | Archived inputs | Generated asset |
|---|---|---|---|---|
| Table 1, p. 26 | Calibration sample use, confidence allocation, and mission spending | `study_A()`; `make_paper_assets.py` | `results/A/seed_0/*_atlas.json`, `*_summary.json` | `tables/calibration_budget_A.tex` |
| Table 2, p. 26 | Benchmark A control metrics and feasible-domain fractions | `study_A()` and `study_grid()` | `results/A/seed_0/`; `results/feasible_grid/` | `tables/benchmark_A.tex` |
| Figure 1, p. 27 | Mean position half-widths across contexts | `study_A()`; `make_paper_assets.py` | `results/A/seed_0/*_atlas.json` | `figures/benchmark_A_tightening.pdf` |
| Table 3, p. 29 | Shift sweep, including rejected corrected designs | `study_B()`; `make_paper_assets.py` | `results/B/shift_sweep.csv` | `tables/shift_sweep.tex` |
| Figure 2, p. 30 | Worst conditional test escape versus shift factor | `study_B()`; `make_paper_assets.py` | `results/B/shift_sweep.csv` | `figures/benchmark_B_shift.pdf` |

All `results/`, `tables/`, and `figures/` paths in this table are relative to `reference/`. In a regenerated full run, results are under `runs/full/experiments/results/`, while the tables and figures are under `runs/full/`.

## Numerical statements outside the tables

| Manuscript passage | Archived evidence | Reproduction |
|---|---|---|
| Equal-total-data comparison, Section 8.2 | `A/seed_0/collective_equal_total_*`; scenario-box files in the same directory | `run --study A` |
| Four independent calibration replications, Section 8.2 | `A/seed_{0,30000,40000,50000}/`; `A/all_summaries.json` | `run --study A` |
| Replication ranges and retained high empirical escape frequency | `paper_numeric_checks.json`, `replications` entry | `run --study all`, including asset generation |
| Pooled-mixture under-protection, Section 8.2 | `mixture_diagnostic.json` | `run --study mixture` |
| Context-dependent budget allocation, Section 8.3 | `budget/reserve_contextual_*` | `run --study budget` |
| Greedy exhaustion and preflight rejection, Section 8.3 | `budget/greedy_*`; `budget/preflight_*` | `run --study budget` |
| Recovery after the prescribed interior shock, Section 8.3 | `recovery/interior_shock_*` | `run --study recovery` |
| Detailed corrected/uncorrected shift performance, Section 8.4 | `B/Gamma_*/` and `B/shift_sweep.csv` | `run --study B` |
| Strong-shift simultaneous binomial intervals, Section 8.4 | `paper_numeric_checks.json`, `strong_shift_simultaneous_95pct_intervals` | `run --study all`, including asset generation |

## Scientific functions

`experiments/mpc_core.py` supplies the two plant definitions and the primitive random-stream generator. The function `calibration_trajectories()` implements the reference residual recursion. `order_parameter()` and `scenario_n()` implement the finite-sample calibration formulas. `MPC` constructs and solves the condensed quadratic program.

`experiments/compatible.py:build()` implements compatibility-first box closure followed by a common calibrated scale. `mpc_core.py:build_atlas()` contains the calibrate-then-close construction and the coordinatewise baselines. `close_edges()` and `terminal_geometry()` perform the geometric construction; `reserves()` computes the finite-mission continuation reserve.

`mpc_core.py:run_missions()` is the common closed-loop simulation engine. `tail()` evaluates the selected ancillary continuation, and `diagnostic_B()` carries out the predeclared feedback-tail conditional test in Benchmark B. The study functions in `experiments/reproduce.py` select the sample counts and pair the random streams. The entire paper protocol is visible in that 205-line driver.

The root `reproduce.py` provides output isolation and validation. The `tools/` directory adds data export and consistency checks. Those additions leave the four preserved experiment scripts unchanged.
