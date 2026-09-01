#!/usr/bin/env python3
"""Host emulation of the verifier: real runner, real pytest, real gt.json.

Docker is not installed on the authoring host, so tools/docker_trial2.py cannot run here.
This reproduces everything the verifier does EXCEPT the container isolation: it overlays a
variant's route.py onto a pristine copy of the tree, runs tests/runner.py against it, and
grades the result with the real tests/test_outputs.py.

What it therefore does NOT prove: the privilege drop, the locked reward channel, the
root-only ground truth, and the reaping of double-forked survivors. Those need the two
real images and are listed as unrun in the handover.

Usage:
    python3 authoring/trial.py solution/ref
    python3 authoring/trial.py shipped
    python3 authoring/trial.py --all
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

import harness  # noqa: E402


def grade(variant: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        app = tmp / "app"
        harness.overlay(variant, app)
        out = tmp / "out.json"
        nonce = "hostemulation"
        subprocess.run(
            [sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
            capture_output=True, text=True,
            env={"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1",
                 "RUN_NONCE": nonce, "TMPDIR": str(tmp),
                 "SYSTEMROOT": "C:\\Windows", "PATH": "/usr/bin:/bin"},
            timeout=900)
        if not out.is_file():
            out.write_text(json.dumps({"reports": {}, "errors": {"fatal": "no output"}}))
        # The artifact directory the attestation compares against: whatever this variant
        # supplied, laid out the way the harness uploads it.
        art = tmp / "artifact"
        harness.stage(variant, art)
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             str(TASK / "tests" / "test_outputs.py")],
            capture_output=True, text=True,
            env={"RUN_OUT": str(out),
                 "RUN_NONCE": nonce,
                 "APP_DIR": str(app),
                 "PRISTINE_DIR": str(TASK / "environment" / "app_src"),
                 "ARTIFACT_DIR": str(art),
                 "PYTHONPATH": str(TASK / "tests"),
                 "PYTHONDONTWRITEBYTECODE": "1",
                 "SYSTEMROOT": "C:\\Windows", "PATH": "/usr/bin:/bin"},
            timeout=900)
        return (1 if proc.returncode == 0 else 0), proc.stdout[-1500:]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    if argv[1] == "--all":
        targets = [("oracle", "solution/ref"), ("nop", "shipped")]
        for d in sorted((TASK / "authoring" / "variants").glob("ok-*")):
            targets.append((d.name, "authoring/variants/" + d.name))
        for d in sorted((TASK / "cheat").glob("v-*")):
            targets.append((d.name, "cheat/" + d.name))
        bad = 0
        for label, path in targets:
            r, _ = grade(path)
            want = 1 if (label == "oracle" or label.startswith("ok-")) else 0
            ok = "OK " if r == want else "BAD"
            if r != want:
                bad += 1
            print("%s %-28s reward=%d (want %d)" % (ok, label, r, want))
        print("\n%d unexpected" % bad)
        return 1 if bad else 0
    r, tail = grade(argv[1])
    print(tail)
    print("reward=%d" % r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
