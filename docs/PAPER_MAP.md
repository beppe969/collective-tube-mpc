# Paper-to-code map

The reference is the included **33-page PDF**, `paper/contextual_collective_tube_mpc.pdf`. Its exact SHA-256 is in `reference/provenance.json`. Section and page numbers below refer to that PDF.

## Tables and figures

| Paper item | Generator | Reference inputs | Release asset |
|---|---|---|---|
| Table 1, p.25 | `study_A()` and `make_paper_assets.py` | `results/A/seed_0/*_atlas.json` and `*_summary.json` | `tables/calibration_budget_A.csv` and `.md` |
| Table 2, p.26 | `study_A()` and `study_grid()` | `results/A/seed_0/` and `results/feasible_grid/` | `tables/benchmark_A.csv` and `.md` |
| Figure 1, p.27 | `study_A()` and `make_paper_assets.py` | `results/A/seed_0/*_atlas.json` | `figures/benchmark_A_tightening.pdf` |
| Table 3, p.29 | `study_B()` and `make_paper_assets.py` | `results/B/shift_sweep.csv` | `tables/shift_sweep.csv` and `.md` |
| Figure 2, p.30 | `study_B()` and `make_paper_assets.py` | `results/B/shift_sweep.csv` | `figures/benchmark_B_shift.pdf` |

The reference paths are relative to `reference/`. A regenerated run writes results under `experiments/results/`, with `tables/` and `figures/` at the run root. PNG previews and full-precision plotting-data CSVs accompany the figures.

## Numerical statements outside the tables

| Passage | Evidence under `reference/results/` | Reproduction study |
|---|---|---|
| Equal-total-data comparison, p.26 | `A/seed_0/collective_equal_total_*` and scenario files | `A` |
| Four calibration replications, p.26 | `A/seed_{0,30000,40000,50000}/` | `A` |
| Replication ranges, p.26 | `paper_numeric_checks.json` | `all` |
| Pooled-mixture conditional escape, p.27 | `mixture_diagnostic.json` | `mixture` |
| Context-dependent risk allocation, Section 8.2.1, p.27 | `budget/reserve_contextual_*` | `budget` |
| Greedy exhaustion and reserve rejection, p.27 | `budget/greedy_*` and `budget/preflight_*` | `budget` |
| Recovery stress test, Section 8.2.1, p.28 | `recovery/interior_shock_*` | `recovery` |
| Shift performance and rejection, Section 8.3, pp.28–29 | `B/Gamma_*/` and `B/shift_sweep.csv` | `B` |
| Strong-shift binomial intervals, p.29 | `paper_numeric_checks.json` | `all` |

`tools/paper_checks.py` contains independently transcribed targets from the PDF and checks 216 numerical entries or outcomes. Printed decimals use a half-unit rounding tolerance. Integer counts and categorical outcomes are exact.

## Mathematical constructions

| Paper | Implementation |
|---|---|
| Models and residual recursion, (2.2), (2.8), (8.3)–(8.9) | `mpc_core.py:make_plant`, `paths`, `calibration_trajectories`, `alpha_deploy` |
| Nested calibration, Proposition 4.2 and (8.2) | `mpc_core.py:order_parameter` |
| Scenario comparator, Section 8.1 | `mpc_core.py:scenario_n`, `build_atlas` |
| Compatibility-first construction, Section 7.2 | `compatible.py:build`, `mpc_core.py:close_edges` |
| Terminal checks, (7.6) | `mpc_core.py:terminal_geometry` |
| Condensed MPC, Sections 3.2 and 8.1 | `mpc_core.py:MPC` |
| Continuation reserve, (5.2) | `mpc_core.py:reserves` |
| Nominal recovery and input projection, (5.6)–(5.7) | `mpc_core.py:run_missions` |
| Hypothetical ancillary continuation, Section 6.1 | `mpc_core.py:tail` |
| Specified feedback-tail shift test, Section 8.3 | `mpc_core.py:diagnostic_B` |

The root command-line interface provides output isolation and validation. The `tools/` modules supply the independent audits and optional raw-data exports. All experimental sample counts and seeds remain those of the supplied code.
