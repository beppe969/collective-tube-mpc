# Contextual Collective-Tube MPC: reproducibility package

This repository accompanies the paper

**Contextual Collective-Tube Model Predictive Control with Finite-Sample Safety Certificates**.

It regenerates the numerical data, tables, and figures for Section 8.  The repository is organized so that a public GitHub release can be created after adding the final paper metadata, repository URL, archival DOI, and license chosen by the author.

## Contents

- `experiments/systems/linear_benchmarks.py` defines the double-integrator and mass-spring benchmarks, predictable contexts, residual generators, and the bounded-shift model.
- `experiments/calibration/certificates.py` implements finite-sample risk certificates and box-containment diagnostics.
- `experiments/atlas_design/build_methods.py` constructs the contextual atlas and benchmark controllers.
- `experiments/controllers/tightened_mpc.py` solves the deterministic tightened MPC subproblem used in closed-loop evaluation.
- `experiments/evaluation/simulate.py` runs receding-horizon missions and records violations, tube escapes, infeasibility, risk spending, and context switches.
- `experiments/plots/make_plots.py` regenerates the PDF figures.
- `experiments/results/` contains deterministic design/calibration/deployment caches, per-row summaries, transition logs, and the final summary tables.
- `figures/` contains the figures regenerated from the cached summaries.

## Environment

The code uses Python 3 and depends on NumPy, SciPy, and Matplotlib.

```bash
python -m pip install -r requirements.txt
```

## Full reproduction

From the repository root, run:

```bash
./reproduce.sh
```

The driver regenerates deterministic caches, evaluates each table row in a separate Python process, writes `experiments/results/summary.csv` and `experiments/results/summary.json`, and updates the PDF figures in `figures/`.

## Cached-table verification

The package includes deterministic cached row summaries.  To rebuild the paper tables and figures from these cached files, run:

```bash
python -m experiments.make_summary
```

## Regenerating a single row

Single rows can be rerun as follows:

```bash
python -m experiments.evaluate_one --benchmark A --method 1 --transition-log experiments/results/transitions_A_1.csv
```

Benchmark A method indices are:

| Index | Method |
| ---: | --- |
| 0 | Oracle contextual tube |
| 1 | Contextual collective atlas |
| 2 | Contextual collective atlas, no edge inflation |
| 3 | Global collective tube |
| 4 | Bonferroni marginal tube |
| 5 | Scenario reachable-set tube |
| 6 | One-step contextual risk map |

Benchmark B method indices are:

| Index | Method |
| ---: | --- |
| 0 | Oracle contextual tube |
| 1 | Contextual atlas, Gamma=1 |
| 2 | Contextual atlas, Gamma=3 |
| 3 | Global tube, Gamma=3 |

## Reported outputs

- `experiments/results/summary.csv` and `experiments/results/summary.json` contain the numerical table values reported in the manuscript.
- `experiments/results/cache_A.npz` and `experiments/results/cache_B.npz` contain deterministic design, calibration, and deployment diagnostic splits.
- `experiments/results/transitions_A_*.csv` and `experiments/results/transitions_B_*.csv` contain transition diagnostics for the closed-loop runs.
- `figures/*.pdf` contains the regenerated paper figures.

## Release checklist before making the repository public

1. Replace the placeholder repository URL in the paper and in `CITATION.cff`.
2. Select and add the final software license.
3. Archive the release, for example through Zenodo, and add the DOI to the paper and to `CITATION.cff`.
4. Check that the paper version, commit hash, and released artifacts match the submission.
