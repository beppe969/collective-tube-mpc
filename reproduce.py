#!/usr/bin/env python3
"""Reproduce the manuscript numerical protocol without modifying archived results.

Run `python reproduce.py --help` for the repository interface. The four scripts
in experiments/ are preserved byte-for-byte from the current manuscript package.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
import time
from tools.common import (ROOT, REFERENCE, check_reference, environment, load_json,
    new_output, run_logged, set_threads, sha256, stage_engine, write_json)


def validate(results: Path, report: Path, *, exact_csv: bool = False,
             allow_partial: bool = False) -> dict:
    from tools.audit import audit_results
    from tools.compare import compare_results
    comparison = compare_results(REFERENCE / "results", results,
        exact_csv=exact_csv, allow_partial=allow_partial)
    audit = audit_results(results)
    integrity = check_reference()
    answer = {"ok": comparison["ok"] and audit["ok"] and integrity["ok"],
              "reference_integrity": integrity, "comparison": comparison,
              "independent_audit": audit}
    tables = results.parents[1] / "tables"
    if not allow_partial and tables.is_dir():
        matches = {p.name: (tables / p.name).is_file() and sha256(p) == sha256(tables / p.name)
                   for p in (REFERENCE / "tables").glob("*.tex")}
        answer["latex_tables_byte_identical"] = matches
        answer["ok"] = answer["ok"] and all(matches.values())
    write_json(report, answer)
    print(f"Verification: {'PASS' if answer['ok'] else 'FAIL'}; "
          f"{comparison.get('csv_files_compared', 0)} CSV files, "
          f"{comparison.get('json_files_compared', 0)} JSON files, "
          f"{audit['checks']} independent checks. Report: {report}")
    for section in (comparison, audit, integrity):
        for message in section.get("errors", [])[:10]:
            print("  " + message, file=sys.stderr)
    return answer


def run_study(args) -> None:
    integrity = check_reference()
    if not integrity["ok"]:
        raise ValueError("Reference integrity failed: " + "; ".join(integrity["errors"]))
    output = new_output(args.output)
    stage_engine(output)
    write_json(output / "environment.json", environment())
    results = output / "experiments/results"
    if args.study == "grid":
        # A grid-only invocation uses an explicitly recorded input atlas set.
        source = args.input_results.resolve() if args.input_results else REFERENCE / "results"
        inputs = source / "A/seed_0"
        if not inputs.is_dir():
            raise ValueError("Grid study requires A/seed_0 atlases; supply --input-results.")
        for apath in inputs.glob("*_atlas.json"):
            dest = results / "A/seed_0" / apath.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Also copy logs/summaries to keep partial-run audit well-defined.
            for path in (apath, apath.with_name(apath.name.replace("_atlas", "_summary")),
                         apath.with_name(apath.name.replace("_atlas.json", "_missions.csv"))):
                shutil.copyfile(path, dest.parent / path.name)
        write_json(output / "grid_input_provenance.json", {
            "source": "archived reference" if args.input_results is None else "user-specified result directory",
            "atlas_sha256": {p.name: sha256(p) for p in inputs.glob("*_atlas.json")}})
    start = time.perf_counter()
    try:
        run_logged([sys.executable, "experiments/reproduce.py", "--study", args.study],
                   output / "experiment.log", output)
        if args.study == "all":
            run_logged([sys.executable, "experiments/make_paper_assets.py"], output / "assets.log", output)
            answer = validate(results, output / "verification.json", exact_csv=args.exact_csv)
            if not answer["ok"]:
                raise RuntimeError("Numerical output differs from the paper reference; see verification.json.")
        write_json(output / "run_status.json", {"ok": True, "study": args.study,
            "elapsed_seconds": time.perf_counter()-start, "paper_parameters_unchanged": True,
            "full_reference_verification": args.study == "all"})
    except BaseException as exc:
        write_json(output / "run_status.json", {"ok": False, "study": args.study,
            "elapsed_seconds": time.perf_counter()-start, "error": str(exc)})
        raise
    print(f"Results written to {output}")


def make_assets(args) -> None:
    output = new_output(args.output)
    stage_engine(output)
    source = args.results.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Results directory not found: {source}")
    shutil.copytree(source, output / "experiments/results")
    run_logged([sys.executable, "experiments/make_paper_assets.py"], output / "assets.log", output)
    matches = {p.name: sha256(p) == sha256(output / "tables" / p.name)
               for p in (REFERENCE / "tables").glob("*.tex")}
    write_json(output / "asset_verification.json", {
        "tables_byte_identical_to_paper": matches,
        "input_result_sha256": {p.relative_to(source).as_posix(): sha256(p)
            for p in sorted(source.rglob("*")) if p.is_file()},
        "figure_comparison": "Plotting inputs and unchanged plotting script are recorded; PDF timestamps can differ."})
    if not all(matches.values()):
        raise RuntimeError("Generated tables differ from the manuscript; see asset_verification.json.")
    print(f"Generated three LaTeX tables and two PDF figures in {output}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check-reference", help="Check archived result and original-engine SHA-256 hashes; no dependencies needed")
    p.add_argument("--report", type=Path)
    p = sub.add_parser("run", help="Run the unchanged full paper protocol, or one study")
    p.add_argument("--study", choices=["all", "A", "B", "budget", "recovery", "grid", "mixture"], default="all")
    p.add_argument("--output", type=Path, default=Path("runs/paper"))
    p.add_argument("--input-results", type=Path, help="Grid-only input results; defaults to the archived A atlases")
    p.add_argument("--exact-csv", action="store_true", help="Additionally require byte-identical CSV outputs")
    p = sub.add_parser("verify", help="Compare numerical outputs with the archive and recompute certificate/log checks")
    p.add_argument("--results", type=Path, default=REFERENCE / "results")
    p.add_argument("--report", type=Path, default=Path("runs/verification.json"))
    p.add_argument("--exact-csv", action="store_true")
    p.add_argument("--allow-partial", action="store_true", help="Explicitly permit missing studies; no full-reproduction claim")
    p = sub.add_parser("assets", help="Regenerate the paper's three tables and two figures without rerunning simulations")
    p.add_argument("--results", type=Path, default=REFERENCE / "results")
    p.add_argument("--output", type=Path, default=Path("runs/assets"))
    p = sub.add_parser("smoke", help="Exercise both plants with full calibration and two short missions each")
    p.add_argument("--output", type=Path, default=Path("runs/smoke"))
    p = sub.add_parser("export-data", help="Materialize synthetic design/calibration data and optional test/mission streams")
    p.add_argument("--benchmark", choices=["A", "B"], required=True)
    p.add_argument("--seed-offset", type=int, help="A: 0, 30000, 40000, or 50000; B: 100000")
    p.add_argument("--gamma", type=float, default=3.0, help="Benchmark B shift factor (default: 3)")
    p.add_argument("--include-test", action="store_true")
    p.add_argument("--include-mission-primitives", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "check-reference":
            report = check_reference()
            if args.report:
                write_json(args.report, report)
            import json
            print(json.dumps(report, indent=2))
            return 0 if report["ok"] else 1
        set_threads()
        if args.command == "run":
            run_study(args)
        elif args.command == "assets":
            make_assets(args)
        elif args.command == "verify":
            answer = validate(args.results.resolve(), args.report.resolve(),
                exact_csv=args.exact_csv, allow_partial=args.allow_partial)
            return 0 if answer["ok"] else 1
        elif args.command == "smoke":
            from tools.smoke import smoke
            smoke(new_output(args.output))
        elif args.command == "export-data":
            from tools.export_data import export_data
            export_data(args, new_output(args.output))
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted. The output directory retains partial logs.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
