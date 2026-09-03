"""Host emulation of one trial: stage a tree, run it, grade it.

This is the fast loop. It runs the real runner and the real grader against the real
ground truth, so it answers "does this submission pass" correctly, and it is what
cheat_report.py uses to find out WHICH assertion caught a cheat.

What it does NOT cover, and the handover has to say so: the privilege drop, the root-owned
reward channel, the root-only ground truth and the process reaping. Those need the two
container images and tools/docker_trial2.py.

    python3 authoring/trial.py cheat/cheat-name.sh
    python3 authoring/trial.py --dir authoring/variants/ok-scan
    python3 authoring/trial.py            (the reference)
"""

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

TASK = pathlib.Path(__file__).resolve().parent.parent
SHIP = TASK / "environment" / "app_src"
TESTS = TASK / "tests"
FILES = ("ord.py", "wire.py", "trip.py", "same.py")


def stage(script=None, folder=None):
    work = pathlib.Path(tempfile.mkdtemp(prefix="pso-trial-"))
    app = work / "app"
    shutil.copytree(SHIP, app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if script is not None:
        env = dict(os.environ, APP=str(app))
        r = subprocess.run(["bash", str(script)], env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("the playbook failed: %s\n%s" % (script, r.stderr[-800:]))
    if folder is not None:
        for f in FILES:
            src = pathlib.Path(folder) / f
            if src.is_file():
                shutil.copy2(src, app / "pnl" / f)
    return work, app


def run(script=None, folder=None, nonce="host", count=120, quiet=True):
    work, app = stage(script, folder)
    rep = work / "out.json"
    env = dict(os.environ,
               APPDIR=str(app), PSO_NONCE=nonce, PSO_COUNT=str(count),
               OUTFD="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(TESTS))
    with open(rep, "w") as fh:
        subprocess.run([sys.executable, str(TESTS / "runner.py")],
                       env=env, stdout=fh, stderr=subprocess.DEVNULL)
    env2 = dict(os.environ,
                PSO_REPORT=str(rep), PSO_TREE=str(app),
                PSO_PRISTINE=str(TESTS / "pristine"),
                PSO_NONCE=nonce, PSO_COUNT=str(count),
                PYTHONDONTWRITEBYTECODE="1")
    out = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-rf",
                          "-p", "no:cacheprovider", str(TESTS / "test_outputs.py")],
                         env=env2, cwd=str(TESTS), capture_output=True, text=True)
    shutil.rmtree(work, ignore_errors=True)
    failed = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if line.startswith("FAILED") or line.startswith("ERROR"):
            rest = line.split("::", 1)[-1] if "::" in line else line.split(None, 1)[-1]
            failed.append(rest.split(" - ")[0].split()[0])
        elif line.startswith("____") and "test_" in line:
            for tok in line.strip("_ ").split():
                if tok.startswith("test_"):
                    failed.append(tok)
    return (out.returncode == 0), sorted(set(failed)), out.stdout


def main(argv):
    if len(argv) > 2 and argv[1] == "--dir":
        ok, failed, log = run(folder=argv[2])
    elif len(argv) > 1:
        ok, failed, log = run(script=argv[1])
    else:
        ok, failed, log = run(folder=TASK / "solution")
    print("reward", 1 if ok else 0, "failed:", failed or "none")
    if not ok and "-v" in argv:
        print(log[-3000:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
