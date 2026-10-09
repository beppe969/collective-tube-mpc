# Numerical validation report

**Paper:** Giuseppe C. Calafiore, *Contextual Collective-Tube Model Predictive Control with Finite-Sample Safety Certificates*.

**Reference:** the supplied 33-page PDF, included as `paper/contextual_collective_tube_mpc.pdf`.

**Validation date:** 8 October 2026.

## Outcome

**PASS in the tested numerical environment.** The full release protocol was executed from scratch and then repeated from a fresh extraction of the upload package. Both executions reproduced the scientific reference outputs. The supplied input code was also run in full before the release changes were made.

All three tables and the checked numerical statements in Section 8 agree with the included paper at its printed precision. Both regenerated figure PDFs match the supplied figure assets pixel-for-pixel when rendered with the same PDF renderer. Timing quantities are host-dependent and are excluded from scientific equality tests.

## Checks performed

| Check | Result |
|---|---|
| Input-code consistency | All four numerical scripts match between the two supplied archives. |
| Input-result consistency | All 121 supplied result files match between the archives. |
| Full release execution | PASS; 207.75 seconds including asset generation and validation. |
| Full execution after fresh ZIP extraction | PASS; 205.41 seconds, with `--exact-csv`. |
| Unit and regression tests | 31 passed; repeated successfully after extraction. |
| Scientific CSV comparison | 42 of 42 byte-identical; maximum numerical difference 0. |
| Scientific JSON comparison | 78 of 78 match; timing fields excluded. |
| Direct correspondence with the paper | 216 checks passed. |
| Independent numerical audit | 11,677 checks passed across 36 atlases and 36 mission logs. |
| Logged rows inspected | 71,305. |
| Formatted tables | All six CSV/Markdown files match the reference exports. |
| Figure rendering | Both figures match at 180 dpi; maximum channel difference 0. |
| Installed dependency versions | All 15 match `requirements.txt`. |
| Smoke simulation and data exports | Both benchmark smoke tests and both full-data export commands passed. |
| Included reference PDF | Byte-identical to the supplied PDF; 33 pages; no embedded file attachments. |

Each full execution performed 71,303 applied control steps across 3,243 configured missions. There were 71,837 accepted QP solves, including candidate evaluations. The largest recorded accepted-QP primal violation was approximately **1.47e-11**, below the paper's acceptance threshold of **2e-7**. The feasible-domain comparison additionally solved **37,515 grid LPs** in each full execution.

Of the 3,243 configured missions, 3,241 completed their full horizons. The two other cases are the specified greedy budget-exhaustion diagnostic and reserve-based preflight rejection. Their stopping behavior reproduces the paper.

## Representative paper correspondence

| Quantity | Paper value | Reproduced value at the same precision |
|---|---:|---:|
| Benchmark A, compatibility-first mean cost | 25.879 | 25.879 |
| Benchmark A, state tightening | 5.10% | 5.10% |
| Benchmark A, input tightening | 25.82% | 25.82% |
| Benchmark A, weighted feasible-grid fraction | 88.01% | 88.01% |
| Benchmark A, horizon escapes in the main run | 7 / 2,640 | 7 / 2,640 |
| Benchmark A, scalar chart charge | 0.003993875 | 0.003993875 |
| Benchmark B, corrected Gamma=3 mean cost | 10.969 | 10.969 |
| Benchmark B, corrected state tightening | 11.91% | 11.91% |
| Benchmark B, corrected input tightening | 28.17% | 28.17% |
| Benchmark B, corrected mission spending | 0.087947 | 0.087947 |
| Benchmark B, corrected final budget | 0.012053 | 0.012053 |

The complete direct comparison is stored in the `paper_correspondence` section of each full-run verification JSON. The expected targets are transcribed in `tools/paper_checks.py`, with the corresponding PDF page references. Printed decimals allow half a unit in the final displayed place plus `1e-12` for roundoff; integer counts match exactly.

### Diagnostic outcomes retained

The no-edge diagnostic fails **89 scalar inclusion checks** and verifies **none of its nine candidate transitions**. Its sampled control performance remains explicitly separate from an atlas-level feasibility certificate.

The contextual reserve experiment produces **12 risk-level schedules** across 40 missions. Spending ranges from **0.062348 to 0.064881**. The greedy diagnostic spends **0.019969** and exhausts its smaller budget after five contained steps. The reserve admission test rejects the same 22-step specification before applying an input.

The recovery stress test enters recovery at step **4** and completes **14 feasible nominal recovery QPs**. It records the **four subsequent state violations** described in the paper, while preserving the hard input bound. These are the only state violations in the complete reproduced set; the artificial shock remains excluded from stochastic coverage estimates.

The four full-sample collective replications complete **480 missions** without physical violations or reset failures. The reported empirical horizon-escape frequency of **0.5682%** in one replication is retained. Independent context-conditional tests remain below the target for those replications.

Corrected designs at **Gamma=100** and **Gamma=59,049** remain rejected for insufficient calibration data. Their minimum per-context counts are **190,019** and **112,206,419**, respectively. The uninflated large-shift conditional escape rates remain **0.59625%** and **0.73875%**. Rejected designs have no manufactured corrected-performance entries.

## Release changes

The package exports the three tables in CSV and Markdown and the two figures in PDF and PNG. It also exports the full-precision plotting coordinates. The attached paper is included unchanged, and the documentation points to its current section numbers.

The command-line verifier adds the 216 PDF-derived numerical checks. Existing geometric and mission-log audits remain available. The source and reference hashes identify the exact tested release.

The QP failure path now distinguishes numerical LP failure from reported infeasibility. Invalid or nonfinite primal solutions raise explicit errors. Terminal construction checks the required infinity-norm contraction before selecting its radius. Regression tests cover these guards and verify shifted-plan witnesses at first-error box corners. The successful numerical paths reproduce the supplied CSVs byte-for-byte.

The plant definitions and experimental parameters are unchanged. Sample counts and random-stream seeds are also unchanged. No manuscript source or Git-history directory is included.

## Environment and remaining validation limits

The tests used **CPython 3.13.5 on Linux x86-64**, with **NumPy 2.3.5** and **SciPy 1.17.0**. Data export and plotting used **pandas 2.2.3** and **Matplotlib 3.10.8**. All pinned dependency versions match the installed environment, and each run records its numerical backend configuration.

An isolated network installation was attempted, including an explicit public-index request. The available package-index path returned no candidates for the first pinned requirement, so **fresh dependency installation could not be verified in this environment**. The logs retain that failure. This result does not establish that the package is unavailable on public PyPI.

Hosted GitHub Actions and Docker execution were not performed. macOS and Windows execution also remain untested here. The supplied workflows use the same numerical verification criteria, with continuous tolerances available for platform-dependent roundoff.

The validation concerns the specified numerical experiments. Applying the methods to another system requires verification of that system's statistical assumptions and transition geometry.

## Evidence and use

The main evidence is in `validation/full_run_verification.json` and `validation/fresh_extraction_verification.json`. Corresponding execution logs and environment records are alongside them. Unit-test logs and figure-render comparisons are included. Raw-array export manifests contain their seeds and hashes.

The reference PDF SHA-256 is:

```text
aea6842491cd3c45646d5a509fdb1a32902e3d35a16198baa8cf19a88be300b0
```

Upload the contents of the extracted `collective-tube-mpc/` folder to the repository root. The archive carries no Git history and performs no remote writes. The GitHub repository has not been changed as part of this package-generation task.
