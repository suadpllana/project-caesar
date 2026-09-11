"""Run every cheat and say WHICH test caught it, not only that the reward was 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on an unrelated typo, or because the harness ran the wrong tree. This runs
each cheat's six files through the real worker and the real grader and prints the first graded
case that failed, so a cheat and the reading it stands for cannot drift apart.

The nine `probe-` cheats are container-only: their attack is on the uid, on /logs/verifier and
on /tests, none of which exist here in the shape the verifier gives them. They are listed as
skipped and are run by tools/docker_trial.py instead.

Usage: cheat_report.py [--only NAME] [--per N] [--scale N]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")
BLOCK = re.compile(r"cat > /app/cfg/([a-z]+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)


def unpack(script, into):
    text = script.read_text(encoding="utf-8")
    found = dict(BLOCK.findall(text))
    assert set(found) == set(PARTS), "%s wrote %s" % (script.name, sorted(found))
    for name, body in found.items():
        (into / name).write_text(body + "\n", encoding="utf-8", newline="\n")
    first = [l for l in text.split("\n") if l.startswith("# ")]
    return first[0][2:] if first else ""


def trial(sub, per, scale, wall=60):
    box = Path(tempfile.mkdtemp(prefix="lgacheat-"))
    work, logs = box / "work", box / "logs"
    work.mkdir(parents=True)
    logs.mkdir(parents=True)
    for name, value in (("nonce", "cheatreport"), ("per", per), ("scale", scale)):
        for target in (work, logs):
            (target / name).write_text("%s\n" % value, encoding="utf-8", newline="\n")
    env = dict(os.environ)
    env.update({"LGA_TESTS": str(TASK / "tests"), "LGA_WORK": str(work), "LGA_SUB": str(sub),
                "LGA_SEAL": str(TASK / "tests" / "seal"), "LGA_LOGS": str(logs),
                "PYTHONDONTWRITEBYTECODE": "1"})
    start = time.time()
    try:
        ran = subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"),
                              "--out", str(work / "worker_out.json")],
                             capture_output=True, text=True, env=env, timeout=wall)
        code = ran.returncode
    except subprocess.TimeoutExpired:
        code = 124
    took = time.time() - start
    graded = subprocess.run([sys.executable, "-m", "pytest",
                             str(TASK / "tests" / "test_outputs.py"),
                             "-p", "no:cacheprovider", "-q", "--no-header", "-x"],
                            capture_output=True, text=True, env=env, cwd=str(TASK / "tests"))
    shutil.rmtree(box, ignore_errors=True)
    caught = ""
    for line in graded.stdout.split("\n"):
        if line.startswith(("FAILED", "ERROR")):
            caught = line.split(" - ")[0].replace("test_outputs.py::", "")
            break
    if code == 124:
        caught = "killed at the %d second wall clock" % wall
    return code, graded.returncode, caught, took


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--per", type=int, default=40)
    ap.add_argument("--scale", type=int, default=3)
    args = ap.parse_args(argv[1:])

    scripts = sorted((TASK / "cheat").glob("cheat-*.sh"))
    if args.only:
        scripts = [s for s in scripts if args.only in s.name]
    bad = []
    for script in scripts:
        name = script.stem[len("cheat-"):]
        if name.startswith("probe-"):
            print("%-26s SKIPPED   container only" % name, flush=True)
            continue
        box = Path(tempfile.mkdtemp(prefix="lgasub-"))
        comment = unpack(script, box)
        ran, graded, caught, took = trial(box, args.per, args.scale)
        shutil.rmtree(box, ignore_errors=True)
        reward = 1 if (ran == 0 and graded == 0) else 0
        if reward:
            bad.append(name)
        print("%-26s reward %d  %6.1fs  %-44s  %s"
              % (name, reward, took, caught or "NOTHING FAILED", comment), flush=True)
    if bad:
        print("\n%d cheats scored 1: %s" % (len(bad), ", ".join(bad)), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
