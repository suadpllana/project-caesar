"""Which assertion catches each cheat, and does every cheat still score 0.

A cheat that dies on an ImportError has been rejected by nothing. Two whole rounds of this
suite scored 0 while never having been applied at all, because their payload sat in a file
the artifact list does not carry, so the verifier graded the shipped policy instead. The
only way to know the difference is to read WHICH test fired, so that is what this prints.

It drives the real two-image trial, so it needs docker. Usage:

    python3 authoring/cheat_report.py [name-fragment]
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
REPO = TASK.parent.parent
sys.path.insert(0, str(REPO / "tools"))

import docker_trial2 as dt  # noqa: E402

WANTED = re.compile(r"^(?:FAILED|ERROR) tests/test_outputs\.py::(\S+)", re.M)


# Two probes are the reference with every answer correct and one attestation interfered
# with. They are SUPPOSED to be caught by that attestation and by nothing else: a probe
# that fails on its own answers can never tell you whether the layer it was aimed at
# fires. Everything else has to be caught by a test that reads the determination.
ATTEST = {
    "cheat-patch-elect.sh": "test_the_frozen_entry_points_were_the_ones_we_shipped",
    "cheat-kill-monitor.sh": "test_the_interpreter_saw_the_work_happen",
}


def caught(name, fired):
    want = ATTEST.get(name)
    if want:
        return want in fired
    return any("register" in n or "raised" in n or "ground_truth" in n for n in fired)


def main(argv):
    pick = argv[1] if len(argv) > 1 else ""
    trial = dt.Trial("share-register-screen")
    if trial.build() != 0:
        return 1
    rows = []
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        if pick and pick not in sh.name:
            continue
        tmp = Path(tempfile.mkdtemp())
        try:
            trial.agent_run(sh, tmp / "art")
            parents = sorted({str(Path("/app") / a).rsplit("/", 1)[0] for a in trial.arts})
            cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; "
                   "mkdir -p /logs/verifier ; bash /tests/test.sh > /tmp/v.log 2>&1 ; "
                   "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
                   "grep -E '^(FAILED|ERROR) ' /tmp/v.log"
                   ) % " ".join(parents)
            proc = subprocess.run(
                ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % (tmp / "art").resolve(),
                 trial.test_img, "bash", "-c", cmd],
                capture_output=True, text=True)
        finally:
            pass
        reward = 0
        for line in proc.stdout.splitlines():
            if line.startswith("REWARD="):
                reward = int((line.split("=", 1)[1] or "0").strip() or 0)
        fired = WANTED.findall(proc.stdout)
        rows.append((sh.name, reward, fired))
        print("%-38s reward=%d  %s" % (sh.name, reward, ", ".join(fired) or "nothing fired"))

    bad = [n for n, r, _ in rows if r != 0]
    hollow = [n for n, r, f in rows if r == 0 and not caught(n, f)]
    print()
    if bad:
        print("   %d cheat(s) scored 1: %s" % (len(bad), ", ".join(bad)))
    if hollow:
        print("   %d cheat(s) were rejected by nothing that was aimed at them: %s"
              % (len(hollow), ", ".join(hollow)))
        print("   Check the payload actually reached the executed tree.")
    if not bad and not hollow:
        print("   %d cheats, all 0, every one caught by the layer it was aimed at"
              % len(rows))
    return 1 if (bad or hollow) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
