#!/usr/bin/env python3
"""Does the verifier demand evidence, or does it grade a report?

The anti-cheat gate rejected delta-view-retraction on 2026-08-13 because a submission that
did no work at all could pass. Nothing was broken out of: the run is sandboxed and the
ground truth is root-only. The hole was narrower and worse - every number the verifier
compared came out of the process that executed the agent's file, so a file that hijacked
the driver's report and returned the right answers was indistinguishable from one that
computed them. Sealing the ground truth does not help, because the adversary the gate
models has already read it.

This gate asks two mechanical questions of a task:

  1. Does cheat/ contain a probe that was generated from tests/gt.json - that is, a cheat
     that is handed every answer? A cheat suite made only of wrong implementations tests
     the problem. It does not test the verifier.
  2. Does every cheat still score 0 through the task's own emulation?

A task that passes has been shown to reject a submission holding the complete answer key.
A task with no such cheat is not proved vulnerable by this script; it is unmeasured, which
is the state delta-view-retraction was in when it was submitted.

Usage:
    python3 tools/forgecheck.py <slug>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def gt_slices(gt_text: str, n: int = 12) -> list[str]:
    """Distinctive runs of ground truth, long enough not to occur by chance."""
    data = json.loads(gt_text)
    out = []
    for chunk in json.dumps(data, sort_keys=True).replace("{", " ").replace("}", " ").split():
        if len(chunk) >= 24:
            out.append(chunk)
        if len(out) >= n:
            break
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    task = ROOT / "tasks" / argv[1]
    gt = task / "tests" / "gt.json"
    cheats = sorted((task / "cheat").glob("cheat-*.sh"))
    if not gt.is_file():
        print("no tests/gt.json under %s" % task)
        return 1
    if not cheats:
        print("no cheats under %s/cheat" % task)
        return 1

    marks = gt_slices(gt.read_text())
    carriers = []
    for sh in cheats:
        body = sh.read_text()
        if any(m in body for m in marks):
            carriers.append(sh.name)

    print("== %s" % argv[1])
    if not carriers:
        print("   FAIL no cheat is generated from tests/gt.json, so nothing here shows")
        print("        the verifier rejecting a submission that already has the answers.")
        print("        Generate a forgery family in authoring/emit.py: hijack whatever")
        print("        assembles the graded report, return the ground truth from it, and")
        print("        confirm it scores 0. If it scores 1, the verifier is grading a")
        print("        claim rather than evidence for one.")
        return 1
    print("   forgery probes carrying ground truth: %s" % ", ".join(carriers))

    reporter = task / "authoring" / "cheat_report.py"
    if not reporter.is_file():
        print("   FAIL no authoring/cheat_report.py to grade them with")
        return 1
    proc = subprocess.run([sys.executable, str(reporter)], cwd=str(task),
                          capture_output=True, text=True, timeout=3600)
    tail = proc.stdout.strip().splitlines()[-1:] or ["no output"]
    print("   %s" % tail[0].strip())
    if proc.returncode != 0:
        print(proc.stdout[-2000:])
        return 1
    print("   none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
