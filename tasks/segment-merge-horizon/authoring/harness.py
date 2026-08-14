#!/usr/bin/env python3
"""Overlay a variant of the editable file onto environment/app_src and run the scenarios.

Usage:
    python3 authoring/harness.py shipped
    python3 authoring/harness.py solution/ref
    python3 authoring/harness.py solution/ref -o out.json
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
EDITABLE = {
    "plan.py": "merge/plan.py",
}


def source(variant: str) -> Path:
    src = Path(variant)
    if not src.is_absolute():
        src = TASK / variant
    return src


def overlay(variant: str, dest: Path) -> None:
    shutil.copytree(TASK / "environment" / "app_src", dest,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if variant == "shipped":
        return
    src = source(variant)
    for name, rel in EDITABLE.items():
        f = src / name
        if f.is_file():
            shutil.copyfile(f, dest / rel)


def stage(variant: str, dest: Path) -> None:
    """Lay a variant's declared files out the way the harness uploads them.

    The verifier attests the tree it executed against the pristine copy plus whatever was
    uploaded at the declared paths, so the emulation has to produce that second tree too.
    """
    dest.mkdir(parents=True, exist_ok=True)
    if variant == "shipped":
        return
    src = source(variant)
    for name, rel in EDITABLE.items():
        f = src / name
        if f.is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dest / rel)


def env_for(app: Path, extra: dict) -> dict:
    base = {"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": "/usr/bin:/bin", "SYSTEMROOT": "C:\\Windows"}
    base.update(extra)
    return base


def run(variant: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        overlay(variant, app)
        out = Path(tmp) / "out.json"
        proc = subprocess.run(
            [sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
            capture_output=True, text=True,
            env=env_for(app, {"TMPDIR": tmp}), timeout=900)
        if not out.is_file():
            print(proc.stdout[-3000:], proc.stderr[-3000:], file=sys.stderr)
            return {"reports": {}, "errors": {"fatal": "no output"}}
        return json.loads(out.read_text())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = run(argv[1])
    if "-o" in argv:
        Path(argv[argv.index("-o") + 1]).write_text(
            json.dumps(data, indent=1, sort_keys=True))
    for name, rep in sorted(data.get("reports", {}).items()):
        print("%-24s reads=%-5d writes=%-5d probes=%-4d jobs=%d"
              % (name, rep["reads"], rep["writes"], rep["probes"], rep["jobs"]))
    for name, err in sorted(data.get("errors", {}).items()):
        print("ERROR", name, str(err).strip().splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
