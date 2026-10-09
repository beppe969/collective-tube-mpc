# Data dictionary and random streams

## Result archive

`reference/results/` contains 36 mission CSV files. There is one corresponding atlas JSON and summary JSON for each mission file. Five further CSVs contain the feasible-state grid masks, and one CSV contains the shift sweep. This gives 42 CSV files in total.

The 79 JSON files include 72 atlas/summary records and six scientific manifests or aggregate calculations. The remaining file, `run_manifest_all.json`, records the original execution environment and timing.

### Mission CSV columns

All step and context indices are zero-based. Missing values are intentional on rows where a quantity is unavailable, such as a preflight rejection or a horizon test after recovery entry.

| Column | Meaning |
|---|---|
| `method` | Construction or diagnostic name |
| `mission`, `k`, `g` | Mission number, applied step, and current exogenous context |
| `chart` | Index into the accompanying atlas's chart list |
| `mode` | `certified_reset`, `recovery`, `budget_rejection`, `budget_exhaustion`, or `initial_state_rejection` |
| `reset_failed` | Measured-state MPC initialization failed at this step |
| `nominal_feasible` | A feasible nominal optimization was accepted for this applied step |
| `budget_before`, `budget_after` | Risk account before and after the current charge |
| `risk` | Charged chart probability; zero after recovery entry |
| `reserve` | Continuation-reserve value for the selected chart and remaining mission length |
| `horizon_escape` | Escape of the selected ancillary residual continuation from its complete tube; missing in recovery |
| `first_escape` | The realized first disturbance lies outside the selected first cross-section |
| `state_violation` | The next physical state exceeds a bound, using tolerance `1e-7` |
| `input_violation` | The applied input exceeds its bound, using tolerance `1e-7` |
| `x0`, `x1` | Current physical state coordinates |
| `next_x0`, `next_x1` | Physical state after applying the input and disturbance |
| `nominal_x0`, `nominal_x1` | Current nominal state used by the optimizer |
| `u` | Applied input, including projection in recovery |
| `stage_cost` | Realized `x'Qx + R u²` |
| `state_tightening` | Selected-chart normalized mean state tightening, expressed as a fraction |
| `input_tightening` | Selected-chart normalized mean input tightening, expressed as a fraction |

The common `mode` names describe simulator behavior. For the no-edge and uninflated shifted-law diagnostics, `certified_reset` must be interpreted together with the diagnostic's failed geometric or statistical conditions. Physical violation flags refer to the next state and the applied input.

### Atlas JSON

`charts` contains each chart's context and box sections. `S` has shape `(H+1,2)` and begins with the zero section. `certified_risk` is the charge used by the simulation. `used_calibration_samples` and `discard_count` record the sample/rank choices. The `radius` field is `null` for coordinatewise constructions without a common scalar radius.

The `raw` field has construction-dependent meaning. For calibrate-then-close it records the pre-closure calibrated sections. In the compatibility-first builder it duplicates the final calibrated sections. The design-stage compatible templates for that builder are stored separately in `audit.template_sections`.

`terminal_F` and `terminal_b` define the common terminal parallelogram. `edges` is a Boolean transition matrix stored as zeros and ones. `audit` records inclusion residuals and terminal slacks. In the compatible builder it also records the individual context thresholds and the final common scale.

`reserve` stores the finite-mission reserve recursion by remaining-step count and current chart. It can be `null` when that recursion contains infinite values, as in the no-edge diagnostic. Its absence does not mean a zero reserve is certified.

### Summary JSON

Summary files aggregate their mission logs. `cost_mean` is the mean realized mission sum; `state_tightening_pct` and `input_tightening_pct` express fractions as percentages. `horizon_escape_pct` ignores the missing recovery entries. `test_rates` are fractions from the separate conditional tests; `worst_context_test_pct` is 100 times their maximum.

`risk_spent_min` and `risk_spent_max` are mission-level accumulated charges. `budget_final_min` is the initial budget minus the largest mission expenditure. Optimizer diagnostics include accepted status counts and the largest accepted primal residual. Median solve time depends on the host and is excluded from scientific reference comparison.

The preflight-rejection summary has no cost or tightening fields because it applies no inputs. Corrected sample-rejected designs in Benchmark B have no mission summary at all; their rejection is represented in the sweep table.

### Grid and shift-sweep CSVs

Each grid file has `position`, `velocity`, and `context_0` through `context_2` columns. Context columns are zero/one feasibility masks. `feasible_grid/summary.json` records the per-context and stationary-weighted feasible percentages.

`B/shift_sweep.csv` includes the trajectory bound `Gamma`, the one-step ratio, and the maximum heavy-mixture probability. `minimum_calibration_samples` gives the scalar sample requirement per context. The uncorrected columns describe the diagnostic; the corrected columns are absent for rejected designs. `risk_spent` and `completed` refer to the corrected missions. The `reason` column records each rejection.

## Random-stream map

All pseudo-random draws use `numpy.random.default_rng(seed)` in the preserved engine. Reproduction uses the same call order and complete sample count as the archive. A shorter sample generated with the same seed need not be a prefix of the full sample because the vectorized draw sequence changes.

| Stream | Seed or rule |
|---|---|
| A design, context `g` | `offset + 1100 + g` |
| A calibration, context `g` | `offset + 2100 + g` |
| A independent conditional test, context `g` | `offset + 3100 + g` |
| A main mission primitive stream | `offset + 5100` |
| A offsets | `0`, `30000`, `40000`, `50000` |
| B design, context `g` | `101100 + g` |
| B calibration, context `g` | `102100 + g` |
| B conditional test primitive stream, context `g` | `104100 + g` |
| B conditional test initial states | `104200` |
| B mission primitive stream | `105100` |
| Initial physical states for a mission stream | `mission_seed + 777` |
| Pooled-mixture design and calibration | `7100` and `7200` |
| Contextual-budget missions | `9100` |
| Greedy and preflight diagnostics | `10100` |
| Recovery stress test | `11100` |

Within a comparison the same primitive stream is paired across controllers. In Benchmark B, the same mixture uniform may yield different component selections as the controlled state/input paths change. Future contexts continue evolving under the exogenous transition matrix.

## Raw array export

`python reproduce.py export-data ...` materializes arrays in `.npy` format with pickling disabled. Design/calibration/test residual arrays have shape `(sample_count,H,2)` and `float64` dtype. Mission primitive exports include the context path and Gaussian innovations. The mixture uniforms and initial physical states are also included when requested.

The export manifest distinguishes a file SHA-256 from the hash of the raw C-order array bytes. The original manifests record the latter. Benchmark A exports validate all requested split hashes; Benchmark B validates its design and calibration split hashes. Its feedback-tail test arrays are regenerated from the explicit controlled kernel, and their original summarized escape rates can be recomputed against the archived atlases.

An A design/calibration/test export contains about 48 MiB of residual-array payload per offset, before optional mission primitives. The basic B design/calibration export contains about 16 MiB. Optional B test primitives add further storage. These arrays are generated locally and are excluded from Git tracking.

No empirical plant measurements are required for these numerical examples. Reproducing a new real-data application would require its own data-generation assumptions and a separate calibration assessment.
