#!/usr/bin/env python3
"""What the isolation probes were actually told, not just what they scored.

A probe that scores 0 proves nothing on its own: it could have scored 0 because its own work
was wrong. These three write down what the container answered them - the uid they ran as, and
whether the sealed answers and the root-owned reward channel were readable - and this prints
that note back out of the verifier container.

    python3 -u authoring/rekey-copy-replay/probe_notes.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/user/project-caesar")
sys.path.insert(0, str(ROOT / "tools"))
import docker_trial  # noqa: E402

PROBES = ("cheat-probe-privilege.sh", "cheat-probe-answer-key.sh", "cheat-probe-shrink-set.sh")


def main():
    t = docker_trial.Trial("rekey-copy-replay")
    parents = sorted({str(Path("/app") / a).rsplit("/", 1)[0] for a in t.arts})
    bad = 0
    for name in PROBES:
        tmp = Path(tempfile.mkdtemp())
        try:
            t.agent_run(t.task / "cheat" / name, tmp / "art", False)
            cmd = (
                "mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
                "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
                "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
                "echo NOTE ; cat /work/probe-*.txt 2>/dev/null || echo '(no note written)' ; "
                "echo PER=$(cat /logs/verifier/per)"
            ) % " ".join(parents)
            got = subprocess.run(
                ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % (tmp / "art").resolve(),
                 t.test_img, "bash", "-c", cmd],
                capture_output=True, text=True)
            print("== %s" % name)
            for line in got.stdout.splitlines():
                print("   %s" % line)
            if "REWARD=0" not in got.stdout:
                print("   FINDING: the probe did not score 0")
                bad += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
