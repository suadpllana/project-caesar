#!/usr/bin/env python3
"""What each isolation probe actually observed, not just what it scored.

A reward of 0 is not evidence for an isolation probe either. It can mean the tamper was
refused, which is the thing being proved, or that the probe never ran, or that the submission
was too slow and the clock ended it before the tamper fired. So this runs the probes through
the two images by hand, keeps the verifier's own log, and asserts the line the probe printed:
an unprivileged uid, a PermissionError on the reward channel, a PermissionError on the sealed
directory, and the grader still writing 0 afterwards.

It needs the two images built (`python3 tools/docker_trial.py feed-lag-pare --build`).

    python3 -u authoring/feed-lag-pare/probe_layer.py
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ENV_IMG = "feed-lag-pare-env:local"
TEST_IMG = "feed-lag-pare-test:local"
PARTS = lab.PARTS

# Each probe, and the line its own output must show for the probe to have proved anything.
WANT = {
    "probe-privilege": [r"^uid 1002$", r"^reward PermissionError$"],
    "probe-answer-key": [r"^gt PermissionError$", r"^model (PermissionError|ModuleNotFoundError)$"],
    "probe-shrink-set": [r"/tests/gen\.py PermissionError", r"/tests/cases\.py PermissionError"],
}


def run(cheat):
    room = pathlib.Path(tempfile.mkdtemp(prefix="flp-probe-"))
    try:
        art = room / "art"
        art.mkdir()
        subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/out" % art,
             "-v", "%s:/agent.sh:ro" % cheat.resolve(), ENV_IMG, "bash", "-c",
             "bash /agent.sh >/tmp/a.log 2>&1 || true ; "
             "mkdir -p /out/lg ; cp /app/lg/*.py /out/lg/"],
            capture_output=True, text=True, timeout=600)
        done = subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art, TEST_IMG, "bash", "-c",
             "mkdir -p /app/lg ; cp -a /artifacts/. /app/ ; bash /tests/test.sh > /tmp/v.log 2>&1 ; "
             "echo REWARD=$(cat /logs/verifier/reward.txt) ; cat /tmp/v.log"],
            capture_output=True, text=True, timeout=900)
        return done.stdout
    finally:
        shutil.rmtree(room, ignore_errors=True)


def main():
    bad = 0
    for name, wants in sorted(WANT.items()):
        cheat = lab.TASK / "cheat" / ("cheat-%s.sh" % name)
        log = run(cheat)
        reward = re.search(r"REWARD=(\d)", log)
        got = reward.group(1) if reward else "?"
        missing = [w for w in wants if not re.search(w, log, re.M)]
        print("%-22s reward=%s  %s" % (name, got, "layer shown" if not missing
                                       else "MISSING %s" % missing))
        for line in log.splitlines():
            if re.match(r"^(uid|gt|model|reward|/tests)", line):
                print("      %s" % line)
        if got != "0" or missing:
            bad += 1
    print("\n%d probe(s) unproved" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
