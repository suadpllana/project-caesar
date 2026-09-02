#!/usr/bin/env python3
"""Lay a policy over environment/app_src and run the scenario set through the real runner.

Usage:
    python3 authoring/harness.py shipped
    python3 authoring/harness.py solution
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
EDITABLE = {"prio.py": "rt/prio.py"}
SEED = "authoringseed"
DRAWN = "12"


def source(variant: str) -> Path:
    p = Path(variant)
    return p if p.is_absolute() else TASK / variant


def overlay(variant: str, dest: Path) -> None:
    shutil.copytree(TASK / "environment" / "app_src", dest,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if variant == "shipped":
        return
    for name, rel in EDITABLE.items():
        f = source(variant) / name
        if f.is_file():
            shutil.copyfile(f, dest / rel)


def stage(variant: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if variant == "shipped":
        return
    for name, rel in EDITABLE.items():
        f = source(variant) / name
        if f.is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dest / rel)


def env_for(app: Path, extra: dict) -> dict:
    base = {"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin",
            "SYSTEMROOT": "C:/Windows", "SCEN_SEED": SEED, "SCEN_DRAWN": DRAWN}
    base.update(extra)
    return base


def run(variant: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        overlay(variant, app)
        out = Path(tmp) / "out.json"
        proc = subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                              capture_output=True, text=True,
                              env=env_for(app, {"TMPDIR": tmp}), timeout=900)
        if not out.is_file():
            print(proc.stdout[-3000:], proc.stderr[-3000:], file=sys.stderr)
            return {"runs": {}, "broke": {"fatal": "no output"}}
        return json.loads(out.read_text())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = run(argv[1])
    for name, rep in sorted(data.get("runs", {}).items()):
        print("%-28s ticks=%-4d" % (name, rep.get("ticks", -1)))
    for name, err in sorted(data.get("broke", {}).items()):
        print("BROKE", name, str(err).strip().splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
