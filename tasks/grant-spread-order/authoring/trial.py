"""Host emulation of the two-image trial: real runner, real grader, real ground truth.

Docker is not installed on the authoring host this task was built on, so the two-image
trial cannot run here. This reproduces everything the trial grades that is not a property
of the container: the pristine overlay, the runner, the nonce, the sealed model and the
whole of test_outputs.py under real pytest.

What it does NOT cover, and what therefore has to be said plainly in any handover: the
privilege drop to the sandbox uid, the root-owned reward channel, the root-only ground
truth and grader, the inherited descriptor, the wall clock timeout and the reaping of
double-forked survivors. The isolation probes graded here prove the grader's logic rejects
them; they do not prove the sandbox contains them.

    python authoring/trial.py --all
    python authoring/trial.py --oracle --count 300
    python authoring/trial.py --cheat cheat-deny-wins
"""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "environment" / "app_src"
TESTS = ROOT / "tests"
PARTS = ("spread.py", "weigh.py", "graft.py", "crowd.py")


def stage(overlay):
    box = pathlib.Path(tempfile.mkdtemp(prefix="gso-trial-"))
    shutil.copytree(SRC, box / "pristine")
    shutil.copytree(SRC, box / "app")
    if overlay is not None:
        for name in PARTS:
            cand = pathlib.Path(overlay) / name
            if cand.is_file():
                shutil.copyfile(cand, box / "app" / "pol" / name)
    for junk in list((box / "app").rglob("__pycache__")):
        shutil.rmtree(junk, ignore_errors=True)
    (box / "run").mkdir()
    return box


def shell():
    """Find a bash that can actually run a cheat playbook.

    On Windows, subprocess resolves a bare "bash" to C:\\Windows\\System32\\bash.exe, which
    is the WSL launcher. With no distribution installed it exits 1 having done nothing, and
    a harness that shrugs that off grades the SHIPPED tree while reporting that it graded a
    cheat - so every cheat scores 0 and the suite proves nothing. That happened here, which
    is why this function exists and why playbook() raises instead of warning.
    """
    named = os.environ.get("GSO_BASH")
    if named and os.path.isfile(named):
        return named
    for guess in (r"C:\Program Files\Git\bin\bash.exe",
                  r"C:\Program Files\Git\usr\bin\bash.exe",
                  r"C:\Program Files (x86)\Git\bin\bash.exe",
                  "/bin/bash", "/usr/bin/bash"):
        if os.path.isfile(guess):
            return guess
    found = shutil.which("bash")
    if found and "System32" not in found and "system32" not in found:
        return found
    raise SystemExit("trial: no usable bash found. Set GSO_BASH to one - a bare 'bash' on "
                     "Windows is the WSL launcher and will silently run nothing.")


BASH = shell()


def playbook(box, script):
    """Run a cheat's shell script against the staged tree, the way solve.sh would."""
    env = dict(os.environ, APP=str(box / "app"), APP_DIR=str(box / "app"))
    proc = subprocess.run([BASH, str(script)], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("trial: %s exited %d - the tree was never modified, so grading it "
                         "would measure the shipped policy and report it as a cheat:\n%s"
                         % (script, proc.returncode, (proc.stdout + proc.stderr)[-800:]))
    return proc.returncode, (proc.stdout + proc.stderr)[-800:]


def go(name, overlay=None, script=None, count=60, nonce="trial-nonce", quiet=True):
    box = stage(overlay)
    note = ""
    try:
        if script is not None:
            code, note = playbook(box, script)
            if code != 0 and not quiet:
                print("   playbook exit %d: %s" % (code, note.strip()[:200]))
        out = box / "run" / "out.json"
        env = dict(os.environ)
        env.update(APPDIR=str(box / "app"), RUN_NONCE=nonce, RUN_COUNT=str(count),
                   PYTHONDONTWRITEBYTECODE="1")
        run = subprocess.run([sys.executable, str(TESTS / "runner.py"), str(out)],
                             env=env, capture_output=True, text=True, timeout=900)
        if not out.is_file():
            return name, 0, "the run wrote no report (exit %d)\n%s" % (
                run.returncode, run.stderr[-600:])
        env.update(RUN_OUT=str(out), APP_DIR=str(box / "app"),
                   PRISTINE_DIR=str(box / "pristine"), PYTHONPATH=str(TESTS))
        grade = subprocess.run(
            [sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"), "-q", "-rf",
             "--no-header", "-p", "no:cacheprovider"],
            env=env, capture_output=True, text=True, timeout=1800, cwd=str(TESTS))
        reward = 1 if grade.returncode == 0 else 0
        return name, reward, grade.stdout[-2500:]
    finally:
        shutil.rmtree(box, ignore_errors=True)


def first_failure(text):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("FAILED ") or (s.startswith("E ") and len(s) > 6):
            return s[:150]
    for line in text.splitlines():
        if "test_" in line and "assert" not in line:
            return line.strip()[:150]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--nop", action="store_true")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--cheats", action="store_true")
    ap.add_argument("--cheat", default=None)
    ap.add_argument("--count", type=int, default=60)
    ap.add_argument("--nonce", default="trial-nonce")
    args = ap.parse_args()

    jobs = []
    if args.all or args.oracle:
        jobs.append(("oracle", ROOT / "solution", None, 1))
    if args.all or args.nop:
        jobs.append(("nop", None, None, 0))
    if args.all or args.variants:
        for d in sorted((HERE / "variants").glob("ok-*")):
            jobs.append(("variant:" + d.name, d, None, 1))
    if args.cheat:
        jobs.append(("cheat:" + args.cheat, None, ROOT / "cheat" / (args.cheat + ".sh"), 0))
    elif args.all or args.cheats:
        for s in sorted((ROOT / "cheat").glob("*.sh")):
            jobs.append(("cheat:" + s.stem, None, s, 0))
    if not jobs:
        ap.error("nothing to do; try --all")

    bad = 0
    for name, overlay, script, expect in jobs:
        got, reward, text = go(name, overlay, script, args.count, args.nonce)
        ok = reward == expect
        bad += 0 if ok else 1
        flag = "ok " if ok else "BAD"
        extra = "" if ok else "   <- " + (first_failure(text) or "no reason parsed")
        print("%s %-42s reward %d (wanted %d)%s" % (flag, name, reward, expect, extra))
    print("\n%d of %d trials as expected" % (len(jobs) - bad, len(jobs)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
