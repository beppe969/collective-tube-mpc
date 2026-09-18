# Reproducibility and validation

## Scope and baseline

The source archive is the latest language-edited manuscript with its synchronized response. Its numerical section and original four Python scripts are preserved in this repository. The source hashes in `reference/provenance.json` identify that exact baseline. All originally reported accepted cases and diagnostic failures are retained.

The public package separates immutable archived results in `reference/` from new output in a user-selected directory. The main CLI creates a fresh run directory and copies the four original scripts into it. The copied driver is then executed with its original parameter values. Asset generation uses the original plotting/table script.

The archive has 42 scientific CSVs and 78 scientific JSONs. Its historical run-environment JSON is retained as a separate provenance record. A full reproduction requires every scientific file. Missing studies are rejected unless `--allow-partial` is explicitly requested, and partial checks do not report complete coverage.

## Levels of checking

### Archive integrity

`python reproduce.py check-reference` requires only the Python standard library. It verifies all reference-file SHA-256 entries and the hashes of the unchanged numerical scripts. The checksum file is an integrity record, not an external cryptographic signature.

### Scientific reference comparison

The verifier checks each CSV's schema, row order, and values. Categorical outcomes and discrete flags must match exactly. For continuous quantities it uses absolute tolerance `2e-7` and relative tolerance `1e-8`. Missing-value locations must agree, which preserves unavailable corrected results and unobserved recovery horizon indicators.

JSON comparison checks every scientific field recursively, including test rates and array shapes. It ignores the explicitly named timing fields `solve_median_ms` and `elapsed_seconds`. Run-environment manifests are recorded separately because host details and timings change across executions. The optional `--exact-csv` flag additionally requires byte identity for all CSVs.

Default tolerance checks can expose changes in numerical backends. Exact-byte matching is a stronger local observation and is not promised across operating systems or BLAS implementations.

### Independent consistency audit

The audit recomputes the cross-chart inclusions from the stored section arrays. It then evaluates the support inequalities for the terminal parallelogram using its stored coordinate matrix. Each calibration charge is checked against the stated beta-quantile formula, and the common-scale construction is checked against the preserved compatible templates.

For every mission log, the audit checks state continuity and risk-account updates. It regenerates the primitive random stream and checks the physical state transitions. Stage costs and tightening measures are recomputed from the recorded states and selected charts. Physical violation flags and summary statistics are recomputed as well. It also checks the continuation-reserve recursion and the guard on certified decisions.

The audit retains the no-edge inclusion failures. It treats recovery and uninflated shifted-law runs according to their diagnostic status. It does not convert those cases into safety claims.

The LP-mask aggregation, pooled-mixture weighting, and shift sample requirements are independently recomputed. These checks supplement full rerunning: the archived files alone cannot prove that each optimizer call was made. The original numerical driver performs the optimization, and a full reproduction then compares its resulting logs with the archive.

### Figure and table checks

All three generated LaTeX table files are compared byte-for-byte with the paper assets. The original plotting code is preserved, and its numerical inputs are included in the comparison. Local PDF rendering checks reproduced both figures pixel-for-pixel. PDF file hashes can differ due to timestamps, even when the graphics match.

The figure-render comparison used a local PDF renderer during package validation. That renderer is not required to run the numerical experiments or generate the PDF figures.

## Environment

The tested numerical configuration is CPython 3.13.5 with NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, and Matplotlib 3.10.8. `requirements.txt` pins these packages and their default transitive runtime dependencies. The full run records installed package versions and `numpy.show_config()` in its `environment.json`.

The CLI requests one CPU thread for the standard numerical backends before importing NumPy/SciPy. It uses Matplotlib's noninteractive `Agg` backend. No GPU or proprietary solver is used.

Local validation used the existing pinned Linux x86-64 environment. A clean network installation was attempted, but the validation host could not resolve the package-index address. This was a network failure; it did not test package availability. Fresh extraction and execution were checked separately. The included GitHub workflows and Docker image remain unexecuted deployment conveniences until they are run by the repository owner.

For a local install, use a fresh virtual environment and `python -m pip install -r requirements.txt`. If pip reports a missing wheel on another platform, first check the Python version and architecture. The reproducibility baseline is the pinned Python 3.13.5 Linux x86-64 configuration. A failed install or output mismatch should be retained in the run log rather than worked around by silently changing numerical dependencies.

## Runtime and storage

The full experiment was measured during package validation. See `validation/VALIDATION.md` and the machine-readable reports there for timings and the observed peak memory. Three same-environment reproductions support the archived outputs; they are repetitions of fixed streams, not additional independent statistical replications.

The source/reference repository is approximately 26 MiB before ZIP compression. A full regenerated result tree has a similar footprint. Temporary synthetic arrays are generated in memory; the optional `.npy` export can increase disk use substantially. A machine with 2 GiB of available RAM is a conservative working allowance for these small benchmark simulations, although actual local peak memory is documented separately.

## Optional Docker execution

The Dockerfile provides the same Python version and numerical requirements. It uses a versioned base-image tag; the operating-system layer is not pinned to a content digest. The image was not built during local validation.

```bash
docker build -t contextual-tube-mpc .
mkdir -p runs/docker
docker run --rm -v "$PWD/runs/docker:/output" contextual-tube-mpc
```

The default container command writes a complete run beneath `/output/paper`. Keep the host output mount so that results survive container removal. The resulting `verification.json` remains the acceptance criterion.

## GitHub workflows

`tests.yml` runs the unit tests and a numerical smoke test on pushes and pull requests. It also regenerates the manuscript assets from archived results. `full-reproduction.yml` runs the full protocol only when launched manually from the Actions tab. Both workflows use read-only repository permissions and archive their validation outputs.

The workflow action versions follow the official `actions/checkout`, `actions/setup-python`, and `actions/upload-artifact` documentation checked during package preparation. The repository's numerical version pins are independent of those workflow action versions.
