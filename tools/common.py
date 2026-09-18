"""Paths, provenance, and subprocess helpers shared by the public commands."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_engine():
    """Load the preserved experiment driver without colliding with the root CLI."""
    path = str(ROOT / "experiments")
    if path not in sys.path:
        sys.path.insert(0, path)
    spec = importlib.util.spec_from_file_location("paper_engine", ROOT / "experiments/reproduce.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def set_threads() -> None:
    # Run before importing NumPy/SciPy. A small, fixed CPU thread count also
    # avoids oversubscription on shared machines. No random seed is changed.
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    os.environ["MPLBACKEND"] = "Agg"


def new_output(path: Path) -> Path:
    """Create a fresh output directory; never overwrite reference data or a run."""
    path = path.expanduser().resolve()
    protected = [REFERENCE.resolve(), (ROOT / "experiments").resolve()]
    if path == ROOT or any(path == p or p in path.parents for p in protected):
        raise ValueError("Output must be outside reference/ and experiments/.")
    if path.exists():
        raise FileExistsError(f"Output directory already exists: {path}. Choose a fresh --output.")
    path.mkdir(parents=True)
    return path


def stage_engine(output: Path) -> None:
    dest = output / "experiments"
    dest.mkdir(exist_ok=True)
    for script in (ROOT / "experiments").glob("*.py"):
        shutil.copyfile(script, dest / script.name)


def run_logged(command: list[str], log: Path, cwd: Path) -> None:
    """Stream a subprocess to the console and an auditable UTF-8 log."""
    log.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["MPLCONFIGDIR"] = str(cwd / ".mplconfig")
    with log.open("w", encoding="utf-8") as file:
        file.write("COMMAND: " + " ".join(command) + "\n")
        file.flush()
        process = subprocess.Popen(command, cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace")
        assert process.stdout
        for line in process.stdout:
            print(line, end="", flush=True)
            file.write(line)
            file.flush()
        code = process.wait()
    if code:
        raise RuntimeError(f"Command exited with status {code}. See {log}.")


def environment() -> dict:
    import importlib.metadata as md
    import platform
    import contextlib
    import io
    import numpy as np
    names = ("numpy", "scipy", "pandas", "matplotlib", "contourpy", "cycler",
             "fonttools", "kiwisolver", "packaging", "pillow", "pyparsing",
             "python-dateutil", "pytz", "six", "tzdata")
    versions = {name: md.version(name) for name in names}
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        np.show_config()
    return {"python": sys.version, "platform": platform.platform(),
            "machine": platform.machine(), "packages": versions,
            "numpy_configuration": stream.getvalue(),
            "thread_environment": {key: os.environ.get(key) for key in
                ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
            "engine_sha256": {p.name: sha256(p) for p in (ROOT / "experiments").glob("*.py")}}


def check_reference() -> dict:
    """Verify archived outputs and unchanged numerical-engine bytes (stdlib only)."""
    errors = []
    count = 0
    manifest = REFERENCE / "SHA256SUMS"
    if not manifest.exists():
        return {"ok": False, "errors": ["Missing reference/SHA256SUMS"]}
    listed = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed.add(name)
        path = REFERENCE / name
        if not path.is_file():
            errors.append(f"Missing reference file: {name}")
        elif sha256(path) != digest:
            errors.append(f"Reference checksum mismatch: {name}")
        count += 1
    actual = {str(p.relative_to(REFERENCE)).replace(os.sep, "/") for p in REFERENCE.rglob("*")
              if p.is_file() and p.name != "SHA256SUMS"}
    if actual != listed:
        errors.append(f"Reference file set differs: extra={sorted(actual-listed)}, missing={sorted(listed-actual)}")
    for name, digest in load_json(REFERENCE / "provenance.json")["engine_sha256"].items():
        path = ROOT / "experiments" / name
        if not path.exists() or sha256(path) != digest:
            errors.append(f"Numerical engine changed: {name}")
    return {"ok": not errors, "reference_files_checked": count,
            "engine_files_checked": 4, "errors": errors}
