#!/usr/bin/env python3
"""Which verifier test each cheat fails, on the host.

Companion to field_report.py: that one reports which graded field diverges, this one
reports which named test catches it, so a cheat that fails for an accidental reason is
visible. The authoritative run is tools/docker_trial2.py, which exercises the isolation
this cannot.

One thing about the host run is worth knowing before reading its output.
cheat-side-channel-file has nothing to fail on here, which is the point of it: the host
emulation has a writable /tmp and no privileged supervisor, so only the container run
stops that one. The three checks that are properties of the verifier image rather than of
the submission - the privilege drop, the disk survey and the reward channel - skip
themselves off the image and are silent here for the same reason.

Usage:  python3 authoring/cheat_report.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

import field_report  # noqa: E402
import harness  # noqa: E402


def grade(variant: str, tmp: Path) -> list[str]:
    data = harness.run(variant)
    out = tmp / "out.json"
    out.write_text(json.dumps(data))
    env = dict(os.environ)
    env["RUN_OUT"] = str(out)
    env["CONF_JSON"] = str(TASK / "tests" / "train.json")
    env["PYTHONPATH"] = str(TASK / "tests")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rf", "--tb=no", "--no-header",
         str(TASK / "tests" / "test_outputs.py")],
        capture_output=True, text=True, env=env)
    return [ln.split(" ")[1] for ln in proc.stdout.splitlines() if ln.startswith("FAILED ")]


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    try:
        for sh in sorted((TASK / "cheat").glob("*.sh")):
            d = tmp / sh.stem
            field_report.from_script(sh, d)
            fails = grade(str(d), tmp)
            names = sorted({f.split("::")[1].split("[")[0] for f in fails if "::" in f})
            print("%-30s %d failing assertions: %s"
                  % (sh.stem, len(fails), ", ".join(names) or "NONE"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
