"""Host emulation of tests/test.sh, and what it cannot cover.

Overlays a solution - the reference, nothing, a variant directory, or a cheat script run
with APP pointed at a scratch tree - onto the shipped engine, runs the real `runner.py`
over the real plan under the real 300-second limit, grades the report with the real
`test_outputs.py` and `test_lifecycle.py`, and derives the reward the way `test.sh` does:
0 unless the worker exited 0, the reaper would have found nothing, and every test passed.

WHAT THIS DOES NOT COVER, and only a container can: the privilege drop to uid 1002, the
root-owned 700 reward channel, /proc survivor reaping and the process-group kill. The
isolation probes aimed at those are reported as not covered rather than as passes.

    python authoring/repair-orderbook-engine/trial.py oracle
    python authoring/repair-orderbook-engine/trial.py nop
    python authoring/repair-orderbook-engine/trial.py variant:journal
    python authoring/repair-orderbook-engine/trial.py cheat:fired-vanish
    python authoring/repair-orderbook-engine/trial.py --all
"""
import argparse
import json
import os
import pathlib
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
TESTS = TASK / "tests"
HERE = ROOT / "authoring" / "repair-orderbook-engine"

WORKER_LIMIT = 300
NOT_COVERED = ("reward-daemon", "probe-privileges", "kill-monitor")

PARTS = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")


def stage(app, source):
    """Put a solution into a scratch engine tree. `source` is a directory of modules,
    a cheat script, or None for the shipped tree."""
    if source is None:
        return
    src = pathlib.Path(source)
    if src.is_dir():
        for p in PARTS:
            if (src / p).is_file():
                shutil.copy(src / p, app / "eng" / p)
        return
    env = dict(os.environ, APP=str(app))
    subprocess.run(["bash", str(src)], env=env, check=True, capture_output=True,
                   timeout=120)


def run(source, small=300, deep=4, nonce=None, keep=False):
    """Run one submission through the worker and the grader. Returns a dict with the
    reward, the worker exit status, the failed test names, and the report."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="trial-"))
    try:
        app = tmp / "app"
        shutil.copytree(TASK / "environment" / "app_src", app,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        stage(app, source)
        out = tmp / "out.json"
        out.write_text("")
        nonce = nonce or secrets.token_hex(16)
        env = dict(os.environ, APPDIR=str(app), RUN_NONCE=nonce, RUN_SMALL=str(small),
                   RUN_DEEP=str(deep), PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(tmp))
        t0 = time.time()
        try:
            w = subprocess.run([sys.executable, str(TESTS / "runner.py"), str(out)],
                               env=env, capture_output=True, text=True, timeout=WORKER_LIMIT)
            worker = w.returncode
        except subprocess.TimeoutExpired:
            worker = 124
        took = time.time() - t0
        env2 = dict(os.environ, RUN_OUT=str(out), APP_DIR=str(app),
                    PRISTINE_DIR=str(TESTS / "pristine"), WORKER_EXIT=str(worker),
                    REAPER_EXIT="0", RUN_NONCE=nonce, RUN_SMALL=str(small),
                    RUN_DEEP=str(deep), PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(TESTS))
        g = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider",
                            str(TESTS / "test_outputs.py"), str(TESTS / "test_lifecycle.py")],
                           env=env2, capture_output=True, text=True, cwd=str(tmp), timeout=900)
        failed = sorted(set(re.findall(r"^FAILED .*?::(\w+)", g.stdout, re.M)))
        try:
            report = json.loads(out.read_text() or "{}")
        except ValueError:
            report = {}
        reward = 1 if (worker == 0 and g.returncode == 0) else 0
        return {"reward": reward, "worker": worker, "failed": failed, "report": report,
                "seconds": round(took, 1), "nonce": nonce, "tail": g.stdout[-1500:]}
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)


def submissions():
    out = {"oracle": (TASK / "solution", 1), "nop": (None, 0)}
    for p in sorted(x for x in (HERE / "variants").iterdir() if x.is_dir()):
        out["variant:" + p.name] = (p, 1)
    for p in sorted((TASK / "cheat").glob("cheat-*.sh")):
        out["cheat:" + p.name[len("cheat-"):-3]] = (p, 0)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--small", type=int, default=300)
    ap.add_argument("--deep", type=int, default=4)
    args = ap.parse_args(argv[1:])
    subs = submissions()
    names = list(subs) if args.all else [args.which]
    bad = 0
    for name in names:
        source, want = subs[name]
        r = run(source, args.small, args.deep)
        flag = "ok " if r["reward"] == want else "BAD"
        if name.startswith("cheat:") and name[6:] in NOT_COVERED and r["reward"] == 0:
            flag = "n/c"
        if flag == "BAD":
            bad += 1
        print("%s %-40s reward %d (want %d)  worker %s  %5.1fs  %s"
              % (flag, name, r["reward"], want, r["worker"], r["seconds"],
                 ",".join(r["failed"])[:110]))
        if flag == "BAD" and not args.all:
            print(r["tail"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
