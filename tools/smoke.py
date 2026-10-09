"""Short end-to-end exercise; it is separate from the reported experiments."""
from __future__ import annotations
from pathlib import Path
import time
from tools.common import environment, load_engine, write_json


def smoke(output: Path) -> None:
    engine = load_engine()
    core = engine.r
    start = time.perf_counter()
    reports = []
    for benchmark, offset, seed in [("A", 0, 5100), ("B", 100000, 105100)]:
        p = core.make_plant(benchmark)
        design, cal, _ = engine.datasets(p, offset, test=False)
        atlas = engine.build(p, design, cal)
        frame, summary = core.run_missions(atlas, 2, 4, .1, seed)
        if not atlas.edges.all() or summary["completed_missions"] != 2:
            raise RuntimeError(f"Smoke test failed for {benchmark}")
        if summary["max_qp_constraint_violation"] > 2e-7:
            raise RuntimeError(f"Smoke QP tolerance exceeded for {benchmark}")
        frame.to_csv(output / f"{benchmark}_missions.csv", index=False)
        write_json(output / f"{benchmark}_atlas.json", core.serialize_atlas(atlas))
        reports.append({"benchmark": benchmark, **summary})
    write_json(output / "smoke_report.json", {"ok": True, "paper_reproduction": False,
        "description": "Full 1800/50000 design/calibration sizes; two missions of four steps per plant. No paper-performance claim.",
        "elapsed_seconds": time.perf_counter()-start, "results": reports})
    write_json(output / "environment.json", environment())
    print(f"Smoke test passed for both plants. Output: {output}")
