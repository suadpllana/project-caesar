"""Two-stage trial at the real paths, for a machine where the images cannot be pulled.

This runs the shipped `tests/test.sh` verbatim - the privilege drop to uid 1002, the locked
root-owned reward channel, the sealed directory at mode 700, the wall clock, the reaper and the
real grader - against artifacts collected the way the platform collects them: the agent stage
gets a copy of `environment/app_src` at `/app`, the six declared files are taken out of it, and
the verifier stage sees a fresh `/app` holding nothing else.

What it does not prove: the two Dockerfiles are never executed, so it says nothing about what
the images contain (`tools/imagecheck.py` covers that), and there is no container boundary.

It writes absolute paths, so it takes a lock: two copies running beside each other are one run
with the rows interleaved.

Usage:
    host_trial.py oracle
    host_trial.py nop
    host_trial.py --dir <directory of editable files>
    host_trial.py --cheat <path/to/cheat.sh>
    host_trial.py --all
"""
import fcntl
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "blend-roll-resume"
PARTS = ("deck.py", "pick.py", "walk.py", "lay.py", "keep.py", "turn.py")
LOCK = Path("/tmp/blend-roll-resume.trial.lock")


def wipe():
    for p in ("/app", "/tests", "/work", "/logs"):
        shutil.rmtree(p, ignore_errors=True)


def agent_stage(script):
    """Give the agent a copy of the shipped tree, run its script, take the six files."""
    shutil.copytree(TASK / "environment" / "app_src", "/app")
    if script is not None:
        got = subprocess.run(["bash", str(Path(script).resolve())],
                             capture_output=True, text=True, cwd="/app")
        if got.returncode != 0:
            print("    agent script exited %d: %s" % (
                got.returncode, (got.stderr or got.stdout).strip().splitlines()[-1:]))
    held = Path("/tmp/brr-collected")
    shutil.rmtree(held, ignore_errors=True)
    (held / "mix").mkdir(parents=True)
    for part in PARTS:
        one = Path("/app/mix") / part
        if one.is_file():
            shutil.copy(one, held / "mix" / part)
    return held


def verifier_stage(held):
    """Rebuild what tests/Dockerfile builds, upload the artifacts, run test.sh."""
    shutil.copytree(TASK / "tests", "/tests",
                    ignore=shutil.ignore_patterns("__pycache__"))
    os.chmod("/tests/test.sh", 0o755)
    os.chmod("/tests/seal", 0o700)
    Path("/app/mix").mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        one = held / "mix" / part
        if one.is_file():
            shutil.copy(one, Path("/app/mix") / part)
    Path("/work").mkdir(exist_ok=True)
    Path("/logs/verifier").mkdir(parents=True, exist_ok=True)
    got = subprocess.run(["bash", "/tests/test.sh"], capture_output=True, text=True)
    tail = [ln for ln in (got.stdout + got.stderr).splitlines()
            if "passed" in ln or "failed" in ln or "error" in ln]
    if tail:
        print("    " + tail[-1].strip())
    try:
        return int(Path("/logs/verifier/reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        return 0


def caught_by(name):
    """Which graded tests the run failed, kept before /logs is wiped."""
    room = Path("/tmp/brr-reports")
    room.mkdir(exist_ok=True)
    src = Path("/logs/verifier/ctrf.json")
    if src.is_file():
        shutil.copy(src, room / (name.replace("/", "_") + ".json"))
    worker = Path("/work/worker_out.json")
    (room / (name.replace("/", "_") + ".worker")).write_text(
        "present" if worker.is_file() else "absent", encoding="utf-8")
    for note in Path("/work").glob("brr-*.txt"):
        shutil.copy(note, room / ("%s.%s" % (name.replace("/", "_"), note.name)))


def from_dir(d):
    """Turn a directory of editable files into an agent script."""
    d = Path(d)
    if not d.is_absolute():
        d = ROOT / d
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for part in PARTS:
        one = d / part
        if one.is_file():
            lines += ["cat > /app/mix/%s <<'PYEOF'" % part,
                      one.read_text(encoding="utf-8").rstrip("\n"), "PYEOF", ""]
    out = Path("/tmp/brr-variant.sh")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


def trial(name, script, want):
    print("[%s]" % name, flush=True)
    wipe()
    held = agent_stage(script)
    shutil.rmtree("/app", ignore_errors=True)
    reward = verifier_stage(held)
    caught_by(name)
    ok = reward == want
    print("    reward=%d expected=%d -> %s\n" % (reward, want, "PASS" if ok else "FAIL"),
          flush=True)
    wipe()
    return ok


def main(argv):
    with open(LOCK, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        what = argv[1] if len(argv) > 1 else ""
        if what == "oracle":
            return 0 if trial("oracle", TASK / "solution" / "solve.sh", 1) else 1
        if what == "nop":
            return 0 if trial("nop", None, 0) else 1
        if what == "--dir":
            d = Path(argv[2])
            return 0 if trial("variant: " + d.name, from_dir(d), 1) else 1
        if what == "--cheat":
            p = Path(argv[2])
            if not p.is_absolute():
                p = ROOT / p
            return 0 if trial("cheat: " + p.name, p, 0) else 1
        if what == "--all":
            res = [trial("oracle", TASK / "solution" / "solve.sh", 1), trial("nop", None, 0)]
            for cheat in sorted((TASK / "cheat").glob("*.sh")):
                res.append(trial("cheat: " + cheat.name, cheat, 0))
            print("%d/%d trials behaved as required" % (sum(res), len(res)))
            return 0 if all(res) else 1
        print(__doc__)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
