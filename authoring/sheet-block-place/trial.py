"""Host emulation of the verifier: overlay, run, grade, read the reward.

This is not the container gate. It does not drop privileges, does not lock the reward
channel and does not build either image, so it proves nothing about isolation; what it
does prove is that the grader accepts the reference, rejects an untouched tree, and
rejects each cheat for the reason the cheat was written to test. Container evidence needs
tools/docker_trial.py, which needs image pulls.

    python authoring/sheet-block-place/trial.py oracle
    python authoring/sheet-block-place/trial.py nop
    python authoring/sheet-block-place/trial.py --dir <policy dir>
    python authoring/sheet-block-place/trial.py --cheats
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "sheet-block-place"
APP = TASK / "environment" / "app_src"
TESTS = TASK / "tests"
POLICY = ("val.py", "see.py", "lay.py", "memo.py")


def stage(overlay, count):
    home = pathlib.Path(tempfile.mkdtemp(prefix="sbp-trial-"))
    work = home / "app"
    shutil.copytree(TESTS / "pristine", work,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if overlay:
        for name in POLICY:
            src = pathlib.Path(overlay) / name
            if src.exists():
                shutil.copyfile(src, work / "sheet" / name)
    (home / "logs").mkdir()
    (home / "logs" / "reward.txt").write_text("0\n")
    return home, work


def run(overlay, count=40, note=""):
    home, work = stage(overlay, count)
    out = home / "out.json"
    nonce = "hostemulation%d" % os.getpid()
    env = dict(os.environ, APPDIR=str(work), RUN_NONCE=nonce, RUN_COUNT=str(count),
               PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(TESTS))
    worker = subprocess.run([sys.executable, str(TESTS / "runner.py"), str(out)],
                            capture_output=True, text=True, env=env, timeout=1800)
    if worker.returncode != 0:
        shutil.rmtree(home, ignore_errors=True)
        return 0, "worker exited %d: %s" % (worker.returncode, worker.stderr[-400:])
    graded = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(TESTS / "test_outputs.py")],
        capture_output=True, text=True, timeout=1800,
        env=dict(env, RUN_OUT=str(out), APP_DIR=str(work),
                 PRISTINE_DIR=str(TESTS / "pristine")))
    reward = 1 if graded.returncode == 0 else 0
    tail = graded.stdout.strip().split("\n")[-1] if graded.stdout else graded.stderr[-300:]
    shutil.rmtree(home, ignore_errors=True)
    return reward, tail


def main(argv):
    count = int(os.environ.get("TRIAL_COUNT", "40"))
    if not argv or argv[0] == "oracle":
        r, why = run(str(TASK / "solution"), count)
        print("oracle  reward=%d  %s" % (r, why))
        return 0 if r == 1 else 1
    if argv[0] == "nop":
        r, why = run(None, count)
        print("nop     reward=%d  %s" % (r, why))
        return 0 if r == 0 else 1
    if argv[0] == "--dir":
        r, why = run(argv[1], count)
        print("%-28s reward=%d  %s" % (pathlib.Path(argv[1]).name, r, why))
        return 0
    if argv[0] == "--cheats":
        bad = 0
        root = TASK / "cheat"
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            r, why = run(str(d), count)
            flag = "" if r == 0 else "   <-- SCORED 1"
            if r:
                bad += 1
            print("%-32s reward=%d%s" % (d.name, r, flag))
        return 1 if bad else 0
    if argv[0] == "--variants":
        bad = 0
        root = HERE / "variants"
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            r, why = run(str(d), count)
            flag = "" if r == 1 else "   <-- SCORED 0: %s" % why
            if r != 1:
                bad += 1
            print("%-32s reward=%d%s" % (d.name, r, flag))
        return 1 if bad else 0
    raise SystemExit("unknown mode %s" % argv[0])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
