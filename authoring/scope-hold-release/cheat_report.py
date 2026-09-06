"""Run every cheat in the real two-image verifier and report its rejecting assertion."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "scope-hold-release"
sys.path.insert(0, str(ROOT / "tools"))

import docker_trial as dt  # noqa: E402

WANTED = re.compile(r"^(?:FAILED|ERROR) tests/test_outputs\.py::(\S+)", re.M)
ATTEST = {
    "cheat-probe-patch-seal.sh": "test_the_sealed_modules_were_the_ones_we_shipped",
    "cheat-probe-rewrite-frozen.sh": "test_the_executed_tree_was_the_one_we_shipped",
}


def main(argv):
    fragment = argv[1] if len(argv) > 1 else ""
    trial = dt.Trial("scope-hold-release")
    if trial.build() != 0:
        return 1
    rows = []
    for script in sorted((TASK / "cheat").glob("cheat-*.sh")):
        if fragment and fragment not in script.name:
            continue
        temp = Path(tempfile.mkdtemp(prefix="shr-cheat-"))
        try:
            trial.agent_run(script, temp / "art")
            parents = sorted({str(Path("/app") / a).rsplit("/", 1)[0] for a in trial.arts})
            command = (
                "mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; "
                "mkdir -p /logs/verifier ; bash /tests/test.sh > /tmp/v.log 2>&1 ; "
                "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
                "grep -E '^(FAILED|ERROR) ' /tmp/v.log"
            ) % " ".join(parents)
            proc = subprocess.run(
                ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % (temp / "art").resolve(),
                 trial.test_img, "bash", "-c", command],
                capture_output=True,
                text=True,
            )
        finally:
            shutil.rmtree(temp, ignore_errors=True)
        reward = 0
        for line in proc.stdout.splitlines():
            if line.startswith("REWARD="):
                reward = int((line.split("=", 1)[1] or "0").strip() or 0)
        fired = WANTED.findall(proc.stdout)
        rows.append((script.name, reward, fired))
        print("%-42s reward=%d  %s" %
              (script.name, reward, ", ".join(fired) or "nothing fired"))

    bad = [name for name, reward, _fired in rows if reward != 0]
    hollow = []
    for name, reward, fired in rows:
        expected = ATTEST.get(name)
        if reward == 0 and ((expected and expected not in fired) or (not expected and not fired)):
            hollow.append(name)
    if bad:
        print("%d cheat(s) scored 1: %s" % (len(bad), ", ".join(bad)))
    if hollow:
        print("%d cheat(s) were rejected by no aimed assertion: %s" %
              (len(hollow), ", ".join(hollow)))
    if not bad and not hollow:
        print("%d cheats all scored 0 and reached their intended checks" % len(rows))
    return 1 if bad or hollow else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
