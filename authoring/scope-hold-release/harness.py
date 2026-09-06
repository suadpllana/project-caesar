"""Host-side staging and semantic replay for scope-hold-release."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "scope-hold-release"
SRC = TASK / "environment" / "app_src"
REF = TASK / "solution"
ARTIFACTS = ("hold.py", "own.py", "pin.py", "tear.py")

PROBE = r"""
import json, pathlib, sys
tree = pathlib.Path(sys.argv[1])
tests = pathlib.Path(sys.argv[2])
rounds = int(sys.argv[3])
sys.path[:0] = [str(tree), str(tests)]
import cases, gen, oracle
from wire import plan, reg
def normalize(records):
    return [[str(x) for x in rec] for rec in records]
def matches(rows, ops):
    try:
        got = normalize(plan.run(reg.load(rows), ops))
    except Exception:
        return False
    return got == normalize(oracle.play(rows, ops))
bad_fixed = []
for name, rows, ops in cases.FIXED:
    if not matches(rows, ops):
        bad_fixed.append(name)
bad_generated = 0
for i in range(rounds):
    rows, ops = gen.stream("variant-%d" % i, i % 2 == 0)
    if not matches(rows, ops):
        bad_generated += 1
print(json.dumps({"fixed": bad_fixed, "generated": bad_generated}))
"""


def stage(policy: Path | None) -> Path:
    work = Path(tempfile.mkdtemp(prefix="shr-")) / "app"
    shutil.copytree(SRC, work)
    if policy is not None:
        for name in ARTIFACTS:
            candidate = policy / name
            if candidate.is_file():
                shutil.copyfile(candidate, work / "wire" / name)
    return work


def check(policy: Path | None, rounds: int = 600) -> dict:
    tree = stage(policy)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", PROBE, str(tree), str(TASK / "tests"), str(rounds)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-2000:] or "replay exited %d" % proc.returncode)
        return json.loads(proc.stdout)
    finally:
        shutil.rmtree(tree.parent, ignore_errors=True)
