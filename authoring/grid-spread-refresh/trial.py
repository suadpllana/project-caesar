"""Host emulation of the verifier: assemble, run, grade.

This is the fast loop, not the gate. It does what tests/test.sh does minus the parts that
need a container - the privilege drop, the root-owned reward, the survivor sweep - so the
isolation is exercised only by tools/docker_trial.py. Everything is assembled in a fresh
temporary directory outside the bundle.

    python3 authoring/grid-spread-refresh/trial.py [--count N] [--dir <policy dir>]
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "grid-spread-refresh")
TESTS = os.path.join(TASK, "tests")
POLICY = ("dep.py", "lay.py", "upd.py", "flow.py")


def main(argv):
    count = "12"
    src = os.path.join(TASK, "solution")
    i = 1
    while i < len(argv):
        if argv[i] == "--count":
            count = argv[i + 1]
            i += 2
        elif argv[i] == "--dir":
            src = argv[i + 1] if os.path.isabs(argv[i + 1]) \
                else os.path.join(ROOT, argv[i + 1])
            i += 2
        else:
            raise SystemExit("unknown argument %s" % argv[i])

    work = tempfile.mkdtemp(prefix="gsr-trial-")
    app = os.path.join(work, "app")
    shutil.copytree(os.path.join(TESTS, "pristine"), app,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for fn in POLICY:
        p = os.path.join(src, fn)
        if os.path.isfile(p):
            shutil.copyfile(p, os.path.join(app, "sheet", fn))
    out = os.path.join(work, "out.json")

    env = dict(os.environ)
    env.update({"APPDIR": app, "RUN_NONCE": "hostemulation", "RUN_COUNT": count,
                "PYTHONPATH": TESTS, "PYTHONDONTWRITEBYTECODE": "1"})
    run = subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out], env=env)
    if run.returncode != 0:
        print("runner exited %d" % run.returncode)
        return 1

    env.update({"RUN_OUT": out, "APP_DIR": app,
                "PRISTINE_DIR": os.path.join(TESTS, "pristine")})
    grade = subprocess.run([sys.executable, "-m", "pytest", "-q",
                            os.path.join(TESTS, "test_outputs.py")], env=env)
    print("reward %d   (work tree %s)" % (1 if grade.returncode == 0 else 0, work))
    return 0 if grade.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
