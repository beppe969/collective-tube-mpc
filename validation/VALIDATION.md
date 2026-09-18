# Local validation record

## Baseline and scope

Validation was performed on 2026-09-18 against the numerical files in the latest 34-page, language-edited manuscript package. The four original experiment scripts and archived numerical outputs are preserved exactly; `reference/provenance.json` and `reference/SHA256SUMS` record their fingerprints. The full manuscript and editorial correspondence are excluded from this repository.

## Completed checks

Three complete fixed-stream reruns reproduced all 42 CSV files byte-for-byte. All 78 scientific JSON files matched after excluding the named timing fields and environment manifests. All executions used the prescribed sample sizes and mission counts. The final public-CLI run passed 11,677 independent audit checks across 36 atlas/log pairs and 71,305 logged rows. The 22 unit tests and the two-plant smoke simulation also passed.

All three regenerated LaTeX tables matched the manuscript assets byte-for-byte. Both regenerated PDF figures matched the archived figures pixel-for-pixel when rendered locally; PDF metadata and timestamps can differ. The figure check uses a renderer that is separate from the experiment dependencies.

The synthetic-array exporter was exercised for Benchmark A and for Benchmark B with shift factor 3. Its design/calibration hashes matched the archived manifests. The Benchmark A test-array hashes also matched. The Benchmark B exported test arrays reproduced the nominal and corrected empirical test rates exactly.

## Measured execution

The public CLI completed a full run, including asset generation and independent verification, in 125.36 seconds wall time according to `/usr/bin/time`. Its maximum resident set size was 328,520 KiB (approximately 321 MiB). The numerical driver itself reported 115.85 seconds. A preceding complete driver execution reported 123.24 seconds. These measurements describe this host and are not portable performance guarantees.

The tested environment was CPython 3.13.5 on Linux x86-64. Full numerical package versions and NumPy build information are retained in `full_run_environment.json`. The CLI requested one thread for the standard numerical backends.

## Installation and remote-execution limits

The runs used the existing environment with the exact versions pinned in `requirements.txt`. An installation into an empty virtual environment was attempted, but the validation host could not resolve the package-index address. Consequently, a fresh network installation has not been verified. The included GitHub Actions workflows and Dockerfile have not been executed. Their installation checks should be run after upload.

The repeated runs use the same prescribed random streams. They verify computational repeatability; the four independent Benchmark A replications remain the four replications already reported in the paper.

## Evidence files

`full_run_verification.json` contains the complete reference-comparison and audit results. `full_run_console.log` retains the execution log and measured resources. `first_run_verification.json` records the preceding run, while `unit_tests.log` records the automated tests. The smoke result and synthetic-export manifests are saved separately. `figure_render_comparison.json` records the image comparisons, and `structural_checks.json` records source syntax and metadata checks.

## Fresh-extraction test

The repository was compressed to ZIP, extracted into a separate directory, and tested from that new location. Reference integrity and all 22 unit tests passed. The extracted repository then executed the complete public command with `--exact-csv`; all 42 CSVs were identical, all 78 scientific JSONs matched, and the 11,677 consistency checks passed. All three table files were identical, and both PDF figures matched when rendered at twice their nominal pixel dimensions.

The fresh-extraction full command took 2:05.79 wall time and its maximum resident set size was 329,068 KiB. A separate mixture-only run passed explicit partial-result verification while retaining `complete_reference_coverage: false`. This confirms that a partial study is distinguished from a full reproduction.

The final package uses the same code bytes tested in that extracted directory; `validated_source_sha256.json` records the comparison. `fresh_checkout_verification.json` and the corresponding console/test logs retain the evidence. The post-test additions are documentation and validation records. This test uses the same installed dependency environment; it does not establish that a fresh network installation succeeds.

`validation_summary.json` provides the machine-readable summary of these checks and their limitations.
