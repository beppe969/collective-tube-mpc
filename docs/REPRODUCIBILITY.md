# Reproducibility and validation

## Reference and release scope

The included `paper/contextual_collective_tube_mpc.pdf` is the exact supplied 33-page manuscript. The two supplied code archives contain identical copies of all four numerical scripts, and identical copies of the 121 result files. Their input hashes and consistency checks are recorded in `reference/provenance.json` and `validation/input_comparison.json`.

The scientific reference consists of 42 CSVs and 78 JSONs. The originating run manifest is additional metadata. Full reproduction requires every scientific result file. Partial verification requires an explicit `--allow-partial` flag and reports incomplete coverage.

The release uses the supplied numerical protocol and random streams. Engineering changes are limited to output formats and validation safeguards. The asset generator writes CSV/Markdown tables, plus PDF/PNG figures and plotting-data CSVs. The documentation and citation metadata refer to the included paper.

### Solver safeguards

The condensed QP keeps SLSQP with analytic derivatives and the paper's tolerances. A solution is accepted only after successful termination and a finite primal residual at most `2e-7`. An independent HiGHS feasibility LP is used after an unsuccessful first QP attempt.

The release explicitly distinguishes an LP infeasibility status from a numerical solver failure. A numerical failure raises an error; a successful feasibility LP followed by an invalid QP result also raises an error. Nonfinite primal points are rejected. These guards prevent numerical breakdown from being logged as geometric infeasibility. They leave successful numerical paths unchanged.

Terminal construction also checks that its coordinate representation is contractive in the infinity norm before computing its admissible radius. This is the condition stated in Section 7.3. Unit tests exercise these failure paths, and shifted-plan witnesses are checked for every atlas edge and each first-error box corner in representative constructions.

The relevant solver status and tolerance definitions are documented by SciPy:

- [SciPy 1.17.0 SLSQP](https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.minimize-slsqp.html).
- [SciPy 1.17.0 HiGHS linear programming](https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.linprog-highs.html).

## Verification layers

### Integrity

`python reproduce.py check-reference` requires only the Python standard library. It checks the reference-file SHA-256 manifest, the released numerical scripts, and the included paper. The manifest records integrity; it supplies no external signature.

### Numerical output comparison

The verifier compares CSV schemas and row ordering, followed by values. Integer flags and categorical outcomes match exactly. Continuous quantities use absolute tolerance `2e-7` and relative tolerance `1e-8`. Missing-value locations must also agree, preserving the unavailable corrected designs and unobserved recovery horizon indicators.

Scientific JSON fields are compared recursively. The named timing fields `solve_median_ms` and `elapsed_seconds` are excluded, and run-environment manifests are recorded separately. `--exact-csv` adds a stronger byte-identity check. Byte identity depends on the numerical platform and is reported separately from tolerance-based agreement.

### Independent consistency audit

The audit recomputes all cross-chart box inclusions and terminal support inequalities. It checks each calibrated risk using the corresponding beta quantile. The common scale and continuation reserve are reconstructed from the stored chart data.

For each mission log, the audit regenerates the primitive random stream and verifies the plant dynamics. It recomputes stage costs and physical-violation flags. Budget updates and selected-chart tightenings are checked against the corresponding summaries. The feasible-grid percentages and shift sample requirements are recomputed as well.

The no-edge failures remain visible. Recovery and uninflated shifted-law runs retain their diagnostic interpretations. A normal-mode label in a shared simulation routine carries only the guarantee justified for its particular construction.

### Direct paper correspondence

`python reproduce.py check-paper` compares 216 reported entries or outcomes against targets transcribed from Tables 1–3 and the surrounding text of Section 8. This check uses explicit PDF-derived targets rather than deriving the expected values from the archived JSON files.

Printed decimals allow half a unit in the final displayed decimal place, with `1e-12` for numerical roundoff. Event counts and categorical outcomes are exact. The report records each paper location and its comparison result.

### Figures and tables

Three table pairs are regenerated as CSV and Markdown. Their formatted values are compared byte-for-byte with the reference exports. The figure formulas and plot settings match the supplied plotting script; the full-precision plotted coordinates are exported as CSV.

Validation also renders regenerated and supplied figure PDFs with the same local renderer and compares their pixels. PDF file hashes may vary because of creation timestamps. The PDF renderer is required only for this release-validation step, not for running the experiments.

## Tested environment

The numerical environment uses CPython 3.13.5 with NumPy 2.3.5 and SciPy 1.17.0. pandas 2.2.3 and Matplotlib 3.10.8 handle data export and plotting. All 15 versions in `requirements.txt` were checked against the installed environment.

The CLI requests one CPU thread for the numerical backends before importing their libraries. Matplotlib uses the noninteractive `Agg` backend. Every full run records package versions and `numpy.show_config()` in `environment.json`.

Fresh network installation was attempted in an isolated virtual environment. The available package-index path returned no candidates even for the first pinned dependency; installation therefore could not be validated here. This result does not establish that the dependency is unavailable on public PyPI. Full simulations and tests used the existing environment with all pinned versions present. The installation logs are retained under `validation/`.

Linux x86-64 is the locally exercised platform. macOS and Windows may produce small floating-point differences. The optional Docker image and hosted GitHub Actions workflows were not executed locally. Their supplied commands remain subject to the same result-verification checks.

## Runtime and storage

Measured run times are recorded in `validation/VALIDATION.md` and the full-run status files. Repeating a fixed-seed reproduction validates execution consistency; the four design/calibration replications specified in the paper provide the independent statistical repetitions.

The release stores compact logs and summaries. Large synthetic residual arrays are generated in memory or exported on demand. A complete run creates roughly another copy of the result tree, while raw-data exports require additional storage. See `docs/DATA_DICTIONARY.md` for array sizes.

## Optional Docker execution

The Dockerfile specifies the pinned Python version and numerical dependencies. Its base image uses a versioned tag, and the operating-system layer remains dependent on that tag.

```bash
docker build -t collective-tube-mpc .
mkdir -p runs/docker
docker run --rm -v "$PWD/runs/docker:/output" collective-tube-mpc
```

The default command writes a complete run under `/output/paper`. The mounted output directory retains the resulting logs and `verification.json`.

## GitHub Actions

Routine checks execute the tests and the smoke simulation. They also regenerate the assets from archived results. The full-reproduction workflow is launched manually from the Actions tab. Both use read-only repository permissions.

Action releases were checked against their official repositories on 8 October 2026:
[checkout](https://github.com/actions/checkout/releases),
[setup-python](https://github.com/actions/setup-python/releases), and
[upload-artifact](https://github.com/actions/upload-artifact/releases).
The workflow action versions are separate from the numerical dependency pins.
