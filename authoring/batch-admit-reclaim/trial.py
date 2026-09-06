"""Host emulation of the two-image trial: overlay, run, grade.

It does what tests/test.sh does, minus the isolation - no privilege drop, no
locked reward channel, no separate container - because those need Docker and
this is the loop used while iterating. What it does cover is the whole grading
path: the pristine overlay, runner.py over every trace, and pytest against
test_outputs.py. Anything it passes still has to pass tools/docker_trial.py.

Usage:
    python3 authoring/batch-admit-reclaim/trial.py               the reference
    python3 authoring/batch-admit-reclaim/trial.py --shipped     the tree as it ships
    python3 authoring/batch-admit-reclaim/trial.py --dir <path>  a directory of policy files
"""

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "batch-admit-reclaim")
SRC = os.path.join(TASK, "environment", "app_src")
TESTS = os.path.join(TASK, "tests")
SOL = os.path.join(TASK, "solution")
WORK = os.environ.get("WORK", "/tmp/bar-work")
BOX = os.path.join(WORK, "box")
POLICY = ("fit.py", "room.py", "back.py", "pick.py")


def lay(over):
    app = os.path.join(BOX, "app")
    if os.path.isdir(BOX):
        shutil.rmtree(BOX)
    os.makedirs(BOX)
    shutil.copytree(os.path.join(TESTS, "pristine"), app)
    if over:
        for name in POLICY:
            here = os.path.join(over, name)
            if os.path.isfile(here):
                shutil.copyfile(here, os.path.join(app, "eng", name))
    return app


def main(argv):
    over = SOL
    if "--shipped" in argv:
        over = None
    elif "--dir" in argv:
        over = argv[argv.index("--dir") + 1]
    app = lay(over)
    out = os.path.join(BOX, "out.json")
    nonce = os.urandom(16).hex() + os.urandom(16).hex()
    env = dict(os.environ)
    env.update({"APPDIR": app, "RUN_NONCE": nonce, "RUN_COUNT": "300",
                "PYTHONDONTWRITEBYTECODE": "1"})
    run = subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out],
                         env=env, capture_output=True, text=True)
    if run.returncode:
        print(run.stdout[-2000:])
        print(run.stderr[-2000:])
        return 2
    env.update({"RUN_OUT": out, "APP_DIR": app,
                "PRISTINE_DIR": os.path.join(TESTS, "pristine"),
                "PYTHONPATH": TESTS})
    grade = subprocess.run(["python3", "-m", "pytest", "-q",
                            os.path.join(TESTS, "test_outputs.py")],
                           env=env, capture_output=True, text=True)
    print(grade.stdout[-4000:])
    if grade.stderr.strip():
        print(grade.stderr[-1500:])
    print("reward", 1 if grade.returncode == 0 else 0)
    return 0 if grade.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
