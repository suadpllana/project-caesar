"""Host emulation of the two-container trial, for a machine with no Docker.

It reproduces what test.sh does apart from the isolation: a pristine work tree with only
the declared artifacts overlaid, the real runner in a subprocess with a fresh nonce, and
the real grader under the real pytest against the real gt.json and the real sealed model.

What it does NOT cover, and the handover has to say so: the privilege drop, the root-owned
locked reward channel, the root-only ground truth, the process teardown in reap.py. Those
need the container. The isolation cheats graded here prove the grader's logic rejects
them, never that the sandbox contains them.

    python3 authoring/trial.py                  the reference solution
    python3 authoring/trial.py --nop            the shipped tree, untouched
    python3 authoring/trial.py --dir <path>     any directory of policy files
    python3 authoring/trial.py --all            reference, nop, every variant, every cheat
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TESTS = os.path.join(ROOT, "tests")
ART = ("kern/pick.py", "kern/stop.py", "kern/knot.py", "kern/wake.py")
COUNT = os.environ.get("RUN_COUNT", "300")


def stage(policy):
    tmp = tempfile.mkdtemp(prefix="gmu-trial-")
    app = os.path.join(tmp, "app")
    shutil.copytree(os.path.join(TESTS, "pristine"), app,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    drop = os.path.join(tmp, "art")
    os.makedirs(os.path.join(drop, "kern"))
    if policy:
        for rel in ART:
            src = os.path.join(policy, os.path.basename(rel))
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(drop, rel))
                shutil.copyfile(src, os.path.join(app, rel))
    return tmp, app, drop


def go(policy, label, quiet=False):
    tmp, app, drop = stage(policy)
    out = os.path.join(tmp, "out.json")
    nonce = os.urandom(16).hex()
    env = dict(os.environ)
    env.update({"APPDIR": app, "RUN_NONCE": nonce, "RUN_COUNT": COUNT,
                "PYTHONDONTWRITEBYTECODE": "1"})
    run = subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out],
                         env=env, capture_output=True, text=True, cwd=tmp)
    if run.returncode != 0 and not quiet:
        print("  runner exited %d\n%s" % (run.returncode, run.stderr[-800:]))
    if not os.path.exists(out):
        open(out, "w").close()
    env.update({"RUN_OUT": out, "APP_DIR": app,
                "PRISTINE_DIR": os.path.join(TESTS, "pristine"),
                "ARTIFACT_DIR": drop, "PYTHONPATH": TESTS})
    grade = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header",
                            os.path.join(TESTS, "test_outputs.py")],
                           env=env, capture_output=True, text=True, cwd=tmp)
    reward = 1 if grade.returncode == 0 else 0
    fired = [ln.rsplit("::", 1)[-1].split()[0]
             for ln in grade.stdout.splitlines() if ln.startswith("FAILED")]
    print("%-34s reward %d   %s" % (label, reward, " ".join(fired)))
    if not quiet and reward == 0:
        tail = [ln for ln in grade.stdout.splitlines()
                if ln.startswith(("FAILED", "E ", "assert", "tests/")) or "wrong" in ln]
        for ln in tail[:14]:
            print("    %s" % ln)
    shutil.rmtree(tmp, ignore_errors=True)
    return reward


def main(argv):
    if "--all" in argv:
        bad = 0
        bad += 0 if go(os.path.join(ROOT, "solution"), "oracle (reference)") else 1
        bad += 1 if go(None, "nop (shipped tree)", quiet=True) else 0
        vd = os.path.join(HERE, "variants")
        for name in sorted(os.listdir(vd)) if os.path.isdir(vd) else []:
            p = os.path.join(vd, name)
            if os.path.isdir(p):
                bad += 0 if go(p, "variant %s" % name) else 1
        cd = os.path.join(ROOT, "cheat")
        work = tempfile.mkdtemp(prefix="gmu-cheat-")
        for name in sorted(os.listdir(cd)):
            if not name.endswith(".sh"):
                continue
            d = os.path.join(work, name[:-3])
            os.makedirs(d)
            ce = dict(os.environ)
            ce["APP"] = os.path.join(d, "app")
            subprocess.run(["bash", os.path.join(cd, name)], cwd=d, env=ce,
                           capture_output=True, text=True)
            src = os.path.join(d, "app", "kern")
            bad += 1 if go(src if os.path.isdir(src) else d,
                           "cheat %s" % name[:-3], quiet=True) else 0
        shutil.rmtree(work, ignore_errors=True)
        print("%s" % ("ALL CLEAN" if bad == 0 else "%d TRIALS WRONG" % bad))
        return 1 if bad else 0
    if "--nop" in argv:
        return 0 if go(None, "nop (shipped tree)") == 0 else 1
    if "--dir" in argv:
        p = argv[argv.index("--dir") + 1]
        return 0 if go(p, os.path.basename(os.path.abspath(p))) else 1
    return 0 if go(os.path.join(ROOT, "solution"), "oracle (reference)") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
