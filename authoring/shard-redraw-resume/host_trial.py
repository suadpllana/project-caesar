"""Run the verifier's two stages on the host, outside the bundle, with one submission laid over.

Not a container run: no privilege drop, no locked reward channel, no root-owned seal. What it
does give is the worker and the grader exactly as they ship, over the real graded set, which is
what sizes the execution limit and what says whether a submission's answers are right.

    python3 -u authoring/shard-redraw-resume/host_trial.py            the reference
    python3 -u authoring/shard-redraw-resume/host_trial.py --dir D    a directory of six files
    python3 -u authoring/shard-redraw-resume/host_trial.py --cheat C  a cheat script
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "shard-redraw-resume"
PARTS = ("draw.py", "cut.py", "scal.py", "turn.py", "keep.py", "lead.py")
LIMIT = 60   # tests/test.sh EXEC_LIMIT: the wall the submitted driver gets
LOCK = pathlib.Path(tempfile.gettempdir()) / "srr-host-trial.lock"


def app_tree(room):
    """The agent container's /app, with whatever the submission did to it."""
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    return app


def main():
    per = int(sys.argv[sys.argv.index("--per") + 1]) if "--per" in sys.argv else 45
    room = pathlib.Path(tempfile.mkdtemp(prefix="srr-trial-"))
    app = app_tree(room)

    if "--cheat" in sys.argv:
        script = pathlib.Path(sys.argv[sys.argv.index("--cheat") + 1]).resolve()
        body = script.read_text(encoding="utf-8").replace("/app/rig/", str(app / "rig") + "/")
        shim = room / "cheat.sh"
        shim.write_text(body, encoding="utf-8", newline="\n")
        done = subprocess.run(["bash", str(shim)], capture_output=True, text=True, cwd=str(app))
        if done.returncode != 0:
            print("cheat script failed: %s" % done.stderr.strip()[-800:])
            return 3
    else:
        src = pathlib.Path(sys.argv[sys.argv.index("--dir") + 1]) if "--dir" in sys.argv \
            else TASK / "solution"
        for part in PARTS:
            shutil.copy(src / part, app / "rig" / part)

    work = room / "work"
    work.mkdir()
    (work / "nonce").write_text("host-%d\n" % os.getpid(), encoding="utf-8", newline="\n")
    (work / "per").write_text("%d\n" % per, encoding="utf-8", newline="\n")
    env = dict(os.environ,
               SRR_TESTS=str(TASK / "tests"), SRR_WORK=str(work),
               SRR_SUB=str(app / "rig"), SRR_SEAL=str(TASK / "tests" / "seal"),
               SRR_PRISTINE=str(TASK / "tests" / "pristine"), SRR_LOGS=str(work),
               PYTHONDONTWRITEBYTECODE="1")
    start = time.time()
    wall = int(sys.argv[sys.argv.index("--wall") + 1]) if "--wall" in sys.argv else LIMIT
    try:
        ran = subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"),
                              "--out", str(work / "worker_out.json")],
                             capture_output=True, text=True, env=env,
                             cwd=str(room), timeout=wall)
        code, err = ran.returncode, ran.stderr
    except subprocess.TimeoutExpired:
        code, err = 124, "killed at the %ds execution limit" % wall
    spent = time.time() - start
    print("worker exit %d in %.1fs" % (code, spent))
    if code != 0:
        print((err or "").strip()[-1200:])

    graded = subprocess.run([sys.executable, "-m", "pytest", str(TASK / "tests" / "test_outputs.py"),
                             "-p", "no:cacheprovider", "-q", "--no-header", "-x"],
                            capture_output=True, text=True, env=env, cwd=str(TASK / "tests"))
    keep = int(sys.argv[sys.argv.index("--tail") + 1]) if "--tail" in sys.argv else 6
    tail = [l for l in graded.stdout.splitlines() if l.strip()][-keep:]
    print("\n".join(tail))
    if graded.returncode and not tail:
        print(graded.stderr.strip()[-2000:])
    reward = 1 if code == 0 and graded.returncode == 0 else 0
    print("reward %d" % reward)
    return 0 if reward else 1


if __name__ == "__main__":
    sys.exit(main())
