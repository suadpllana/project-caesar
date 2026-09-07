"""Host emulation of one trial, for fast iteration.

Builds the work tree the way tests/test.sh does, overlays one policy directory onto it,
runs tests/runner.py against it, then runs the grader. Everything lands in a temp
directory outside the bundle, because authoring scratch left inside the task folder ships.

This does not exercise the container isolation - the privilege drop, the locked reward
channel, the root-only ground truth. tools/docker_trial.py does that.

Usage:
    python3 trial.py <policy-dir> [--small N] [--deep N]
    python3 trial.py --shipped
    python3 trial.py --reference
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "slice-trip-fill"))
TESTS = os.path.join(TASK, "tests")
PRISTINE = os.path.join(TESTS, "pristine")
ARTIFACTS = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")


def run(policy, small, deep, nonce, keep=False):
    root = tempfile.mkdtemp(prefix="stf-trial-")
    app = os.path.join(root, "app")
    shutil.copytree(PRISTINE, app)
    if policy is not None:
        # A variant changes one decision and leaves the rest of the reference alone, so
        # anything it does not carry comes from solution/. Copying only what is present
        # leaves the shipped broken files standing and reports a correct variant as a
        # failure.
        ref = os.path.join(TASK, "solution")
        for fn in ARTIFACTS:
            for src in (os.path.join(ref, fn), os.path.join(policy, fn)):
                if os.path.isfile(src):
                    shutil.copyfile(src, os.path.join(app, "eng", fn))
    out = os.path.join(root, "out.json")
    env = dict(os.environ)
    env.update(APPDIR=app, RUN_NONCE=nonce, RUN_SMALL=str(small),
               RUN_DEEP=str(deep), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out],
                       env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        return 2, root
    env.update(RUN_OUT=out, APP_DIR=app, PRISTINE_DIR=PRISTINE,
               PYTHONPATH=TESTS)
    g = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        os.path.join(TESTS, "test_outputs.py"), "-rf"],
                       env=env, capture_output=True, text=True)
    print(g.stdout[-6000:])
    if g.stderr.strip():
        print(g.stderr[-2000:])
    if not keep:
        shutil.rmtree(root, ignore_errors=True)
    return (0 if g.returncode == 0 else 1), root


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("policy", nargs="?")
    ap.add_argument("--shipped", action="store_true")
    ap.add_argument("--reference", action="store_true")
    ap.add_argument("--small", type=int, default=60)
    ap.add_argument("--deep", type=int, default=1)
    ap.add_argument("--nonce", default="host-trial")
    a = ap.parse_args(argv[1:])
    policy = None
    if a.reference:
        policy = os.path.join(TASK, "solution")
    elif a.policy:
        policy = a.policy
    label = "shipped tree" if policy is None else policy
    code, _ = run(policy, a.small, a.deep, a.nonce)
    print("%s -> reward %d" % (label, 1 if code == 0 else 0))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
