#!/usr/bin/env python3
"""Build an overlay tree from environment/app_src plus a variant of the editable files,
run the scenario set against it, and print or save the reports.

Usage:
    python3 authoring/harness.py shipped
    python3 authoring/harness.py solution/ref
    python3 authoring/harness.py solution/ref -o /tmp/ref.json
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
    "pstore.py": "model/pstore.py",
    "pfx.py": "runtime/pfx.py",
    "sch.py": "runtime/sch.py",
    "pool.py": "mem/pool.py",
}


def overlay(variant: str, dest: Path) -> None:
    shutil.copytree(TASK / "environment" / "app_src", dest)
    if variant == "shipped":
        return
    src = Path(variant)
    if not src.is_absolute():
        src = TASK / variant
    for name, rel in EDITABLE.items():
        f = src / name
        if f.is_file():
            shutil.copyfile(f, dest / rel)


def run(variant: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        overlay(variant, app)
        out = Path(tmp) / "out.json"
        env = {"APPDIR": str(app), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
        proc = subprocess.run(
            [sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
            capture_output=True, text=True, env=env, timeout=900)
        if proc.returncode != 0:
            print(proc.stdout[-2000:], proc.stderr[-2000:], file=sys.stderr)
        return json.loads(out.read_text())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = run(argv[1])
    if "-o" in argv:
        Path(argv[argv.index("-o") + 1]).write_text(
            json.dumps(data, indent=1, sort_keys=True), newline="\n")
    for name, rep in data["reports"].items():
        print("%-22s computed=%-5d reused=%-5d restart=%-3d preempt=%-3d evict=%-3d" % (
            name, rep["computed"], rep["reused"], rep["restart"], rep["preempt"], rep["evict"]))
    for name, err in data.get("errors", {}).items():
        print("ERROR", name, err.splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
