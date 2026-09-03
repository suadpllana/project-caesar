"""Host emulation of the two-image trial: real runner, real grader, real gt.json.

Docker is not always available on an authoring host, so this stages the tree the way the
verifier image builds it - tests/ copied WITHOUT pristine, and the pristine tree beside it,
because the image does `mv /tests/pristine /pristine` and a case that reads tests/pristine by
path resolves here and raises there. Then it runs tests/runner.py in its own process, the way
test.sh does, and grades its JSON with the real tests/test_outputs.py under pytest.

What it does NOT cover, and the handover has to say so: the privilege drop, the root-owned
reward channel, the unreadable /tests, and the process teardown.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import stage

CHEATS = os.path.join(stage.TASK, "cheat")
VARIANTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "variants")


def lay(work, overlay):
    app = stage.tree(overlay, into=work)
    tests = os.path.join(work, "tests")
    if os.path.isdir(tests):
        shutil.rmtree(tests)
    os.makedirs(tests)
    for name in sorted(os.listdir(stage.TESTS)):
        if name in ("pristine", "__pycache__"):
            continue
        src = os.path.join(stage.TESTS, name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(tests, name))
    pristine = os.path.join(work, "pristine")
    if os.path.isdir(pristine):
        shutil.rmtree(pristine)
    shutil.copytree(os.path.join(stage.TESTS, "pristine"), pristine,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return app, tests, pristine


def play(app, script):
    out = subprocess.run(["bash", script], env=dict(os.environ, APP=app),
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("playbook %s failed rc=%d\n%s" % (script, out.returncode,
                                                             out.stderr[-2000:]))


def grade(label, overlay=None, script=None, count=60):
    work = tempfile.mkdtemp(prefix="ahc-trial-")
    try:
        app, tests, pristine = lay(work, overlay)
        if script:
            play(app, script)
        report = os.path.join(work, "out.json")
        nonce = "trial-%s" % label
        env = dict(os.environ, APPDIR=app, RUN_NONCE=nonce, RUN_COUNT=str(count),
                   PYTHONPATH=os.pathsep.join([app, tests]), PYTHONDONTWRITEBYTECODE="1")
        run = subprocess.run([sys.executable, os.path.join(tests, "runner.py"), report],
                             env=env, capture_output=True, text=True, cwd=work)
        if not os.path.exists(report):
            return 0, "the run wrote no report: %s" % run.stderr[-400:]
        env2 = dict(os.environ, RUN_OUT=report, APP_DIR=app, PRISTINE_DIR=pristine,
                    RUN_NONCE=nonce, RUN_COUNT=str(count),
                    PYTHONPATH=tests, PYTHONDONTWRITEBYTECODE="1")
        pt = subprocess.run([sys.executable, "-m", "pytest", "-q",
                             os.path.join(tests, "test_outputs.py")],
                            env=env2, capture_output=True, text=True, cwd=work)
        first = ""
        for line in pt.stdout.splitlines():
            if line.startswith(("FAILED", "E  ")) or "assert" in line[:8]:
                first = line.strip()[:150]
                break
        return (1 if pt.returncode == 0 else 0), first
    finally:
        shutil.rmtree(work, ignore_errors=True)


def check_host():
    """A harness that cannot tell "it failed" from "the grader never ran" manufactures
    evidence, so establish that pytest is here before believing a single 0."""
    out = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("pytest is not installed on this host, so every reward below would "
                         "be 0 for a reason that has nothing to do with the task:\n"
                         "  pip install pytest==9.1.1 pytest-json-ctrf==0.5.2")


def main():
    check_host()
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--cheats", action="store_true")
    ap.add_argument("--count", type=int, default=60)
    args = ap.parse_args()
    ref = [os.path.join(stage.SOLUTION, n) for n in ("hold.py", "pick.py")]
    bad = 0
    rows = []
    if args.all or not (args.variants or args.cheats):
        rows.append(("oracle", grade("oracle", ref, count=args.count), 1))
        rows.append(("nop (shipped tree)", grade("nop", None, count=args.count), 0))
    if args.all or args.variants:
        for name in sorted(os.listdir(VARIANTS)) if os.path.isdir(VARIANTS) else []:
            d = os.path.join(VARIANTS, name)
            files = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".py")]
            rows.append((name, grade(name, files, count=args.count), 1))
    if args.all or args.cheats:
        for name in sorted(os.listdir(CHEATS)) if os.path.isdir(CHEATS) else []:
            if not name.endswith(".sh"):
                continue
            rows.append((name[:-3], grade(name, None, os.path.join(CHEATS, name),
                                          count=args.count), 0))
    for name, (got, why), want in rows:
        flag = "ok " if got == want else "BAD"
        if got != want:
            bad += 1
        print("%s %-34s reward %d (want %d) %s" % (flag, name, got, want, why))
    print("%d unexpected" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
