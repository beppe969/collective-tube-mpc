"""Strict file coverage, exact discrete comparisons, and tolerant floating comparisons.

Only timing fields and run-environment manifests are excluded from scientific
comparison. Missing files, changed array shapes, and altered categorical outcomes
are errors. NaN locations in CSVs must agree (e.g. unavailable corrected designs).
"""
from __future__ import annotations
import math
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from tools.common import load_json, sha256

IGNORED_FIELDS = {"solve_median_ms", "elapsed_seconds"}
DISCRETE_COLUMNS = {"mission", "k", "g", "chart", "reset_failed", "nominal_feasible",
                    "horizon_escape", "first_escape", "state_violation", "input_violation",
                    "completed", "minimum_calibration_samples", "context_0", "context_1", "context_2"}


def compare_json(a: Any, b: Any, path: str, errors: list[str], atol: float, rtol: float) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        ak, bk = set(a) - IGNORED_FIELDS, set(b) - IGNORED_FIELDS
        if ak != bk:
            errors.append(f"{path}: JSON keys differ ({sorted(ak ^ bk)})")
        for key in sorted(ak & bk):
            compare_json(a[key], b[key], f"{path}/{key}", errors, atol, rtol)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            errors.append(f"{path}: list lengths differ ({len(a)} != {len(b)})")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                compare_json(x, y, f"{path}/{i}", errors, atol, rtol)
    elif isinstance(a, bool) or isinstance(b, bool):
        if type(a) is not type(b) or a != b:
            errors.append(f"{path}: boolean differs ({a!r} != {b!r})")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, int) and isinstance(b, int):
            good = a == b
        else:
            good = math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, abs_tol=atol, rel_tol=rtol)
        if not good:
            errors.append(f"{path}: numeric difference ({a!r} != {b!r})")
    elif type(a) is not type(b) or a != b:
        errors.append(f"{path}: value differs ({a!r} != {b!r})")


def compare_csv(reference: Path, actual: Path, atol: float, rtol: float) -> tuple[list[str], float]:
    ref = pd.read_csv(reference)
    got = pd.read_csv(actual)
    errors, largest = [], 0.0
    if list(ref.columns) != list(got.columns) or ref.shape != got.shape:
        return [f"{reference.name}: CSV schema/shape differs"], largest
    for col in ref.columns:
        a, b = ref[col], got[col]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            xa, xb = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
            # Integer/discrete scientific outcomes must agree exactly.
            discrete = col in DISCRETE_COLUMNS or (pd.api.types.is_integer_dtype(a) and pd.api.types.is_integer_dtype(b))
            good = np.isclose(xa, xb, atol=0.0 if discrete else atol,
                              rtol=0.0 if discrete else rtol, equal_nan=True)
            finite = np.isfinite(xa) & np.isfinite(xb)
            if finite.any():
                largest = max(largest, float(np.max(np.abs(xa[finite] - xb[finite]))))
            if not bool(good.all()):
                bad = np.flatnonzero(~good)
                errors.append(f"{reference.name}/{col}: {len(bad)} mismatches, first row {int(bad[0])}")
        elif not a.fillna("<MISSING>").astype(str).equals(b.fillna("<MISSING>").astype(str)):
            errors.append(f"{reference.name}/{col}: categorical values or missing locations differ")
    return errors, largest


def compare_results(reference: Path, actual: Path, *, atol: float = 2e-7,
                    rtol: float = 1e-8, exact_csv: bool = False, allow_partial: bool = False) -> dict:
    reference, actual = reference.resolve(), actual.resolve()
    if not actual.is_dir():
        return {"ok": False, "errors": [f"Result directory does not exist: {actual}"]}
    select = lambda base: {p.relative_to(base).as_posix(): p for p in base.rglob("*")
        if p.suffix in (".csv", ".json") and not p.name.startswith("run_manifest_")}
    refs, outputs = select(reference), select(actual)
    missing, extra = sorted(refs.keys() - outputs.keys()), sorted(outputs.keys() - refs.keys())
    errors = []
    if missing and not allow_partial:
        errors.append(f"Missing scientific files: {missing}")
    if extra:
        errors.append(f"Unexpected scientific files: {extra}")
    if not outputs:
        errors.append("No scientific outputs found.")
    csv_exact, csv_count, json_count, max_diff = 0, 0, 0, 0.0
    differences = {}
    for name in sorted(refs.keys() & outputs.keys()):
        a, b = refs[name], outputs[name]
        if a.suffix == ".csv":
            csv_count += 1
            same = sha256(a) == sha256(b)
            csv_exact += int(same)
            if exact_csv and not same:
                errors.append(f"{name}: CSV bytes differ (--exact-csv)")
            errs, diff = compare_csv(a, b, atol, rtol)
            max_diff = max(max_diff, diff)
            if diff:
                differences[name] = diff
            errors.extend(f"{name}: {e}" for e in errs)
        else:
            json_count += 1
            compare_json(load_json(a), load_json(b), name, errors, atol, rtol)
    return {"ok": not errors, "complete_reference_coverage": not missing,
            "csv_files_compared": csv_count, "csv_files_byte_identical": csv_exact,
            "json_files_compared": json_count, "maximum_csv_absolute_difference": max_diff,
            "floating_tolerance": {"atol": atol, "rtol": rtol},
            "exact_csv_required": exact_csv, "timing_fields_excluded": sorted(IGNORED_FIELDS),
            "environment_manifests_excluded": True,
            "missing_files": missing, "extra_files": extra,
            "csv_max_differences": differences, "errors": errors}
