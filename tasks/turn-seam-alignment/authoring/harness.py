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
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import audit  # noqa: E402
import scen  # noqa: E402

EDITABLE = {
    "inc.py": "tok/inc.py",
    "store.py": "tok/store.py",
    "ep.py": "loop/ep.py",
    "rec.py": "loop/rec.py",
}


def overlay(variant: str, dest: Path) -> None:
    shutil.copytree(TASK / "environment" / "app_src", dest,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if variant == "shipped":
        return
    src = Path(variant)
    if not src.is_absolute():
        src = TASK / variant
    for name, rel in EDITABLE.items():
        f = src / name
        if f.is_file():
            shutil.copyfile(f, dest / rel)


SOCK = "/meter/sock"


def meter(tape: Path):
    """Bring the sealed meter up the way tests/test.sh does, or report that we cannot.

    The emulation is worthless without it. Every graded figure now comes off the meter's
    tape, so a local trial that ran the loop with no meter behind it would be scoring the
    run's own account of itself - which is the thing that got the earlier build passed by
    a probe. When the meter cannot be started here, run() falls back to synthesising the
    tape from the run's record and says so, and the docker trials remain the real gate.
    """
    try:
        os.makedirs("/meter", exist_ok=True)
        if os.path.exists(SOCK):
            os.unlink(SOCK)
    except OSError:
        return None
    env = dict(os.environ)
    env["PYTHONPATH"] = str(TASK / "tests")
    proc = subprocess.Popen(
        [sys.executable, str(TASK / "tests" / "meter.py"), SOCK, str(tape)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(200):
        if os.path.exists(SOCK):
            return proc
        if proc.poll() is not None:
            return None
        time.sleep(0.05)
    proc.kill()
    return None


def read_tape(path: Path) -> list:
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run(variant: str, tape_path: str | None = None) -> dict:
    """Drive one set of editable files through every scenario, behind the meter.

    The report comes back with the meter's tape attached, because that is what the
    verifier grades. Nothing here reads the run's own counters.
    """
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / "app"
        overlay(variant, app)
        out = Path(tmp) / "out.json"
        tape = Path(tape_path) if tape_path else Path(tmp) / "tape.jsonl"
        if tape.exists():
            tape.unlink()
        served = meter(tape)
        env = {"APPDIR": str(app), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            proc = subprocess.run(
                [sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                capture_output=True, text=True, env=env, timeout=900)
        finally:
            if served is not None:
                served.terminate()
                served.wait(timeout=10)
        if proc.returncode != 0:
            print(proc.stdout[-2000:], proc.stderr[-2000:], file=sys.stderr)
        data = json.loads(out.read_text())
        rows = read_tape(tape)
        if served is None:
            # No fallback when the meter did run: an empty tape is a finding, not a gap.
            print("harness: no meter on this host, synthesising the tape from the run's "
                  "own record", file=sys.stderr)
            rows = audit.synth([s["name"] for s in scen.SCENARIOS], data.get("reports"))
        data["tape"] = rows
        return data


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    data = run(argv[1])
    if "-o" in argv:
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(data, indent=1, sort_keys=True))
    for name, rep in data["reports"].items():
        print("%-16s chars=%-6d calls=%-4d fwd=%-6d spans=%s" % (
            name, rep["enc_chars"], rep["enc_calls"], rep["fwd"],
            {k: v for k, v in rep["spans"].items()}))
    for name, err in data.get("errors", {}).items():
        print("ERROR", name, err.splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
