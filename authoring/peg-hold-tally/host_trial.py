"""Host emulation of the verifier: worker then grader, no containers.

Not a substitute for tools/docker_trial.py - it does not exercise the privilege drop, the locked
reward channel or the image build. It exists to catch bugs in the worker and the grader in seconds
instead of minutes, and to time the graded set.
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
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
PARTS = ("live.py", "cover.py", "edge.py", "gone.py", "sole.py")


def main():
    over = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    per = sys.argv[2] if len(sys.argv) > 2 else "75"
    room = pathlib.Path(tempfile.mkdtemp(prefix="pht-trial-"))
    app = room / "app"
    logs = room / "logs"
    work = room / "work"
    for d in (logs, work):
        d.mkdir(parents=True)
    shutil.copytree(TASK / "environment" / "app_src", app, ignore=shutil.ignore_patterns("progs"))
    if over:
        for part in PARTS:
            src = pathlib.Path(over) / part
            if src.is_file():
                shutil.copy(src, app / "keep" / part)
    (logs / "nonce").write_text("d41d8cd98f00b204e9800998ecf8427e", encoding="utf-8")
    (logs / "per").write_text(per, encoding="utf-8")
    for name in ("nonce", "per"):
        shutil.copy(logs / name, work / name)

    env = dict(os.environ)
    env.update({"PHT_TESTS": str(TASK / "tests"), "PHT_WORK": str(work),
                "PHT_SUB": str(app / "keep"), "PHT_SEAL": str(TASK / "tests" / "seal"),
                "PHT_LOGS": str(logs), "PYTHONDONTWRITEBYTECODE": "1"})
    t0 = time.time()
    r = subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"),
                        "--out", str(work / "worker_out.json")],
                       capture_output=True, text=True, env=env)
    took = time.time() - t0
    print("worker exit %d in %.1fs %s" % (r.returncode, took, r.stderr.strip()[-400:]))
    if r.returncode:
        return 1
    t1 = time.time()
    g = subprocess.run([sys.executable, "-m", "pytest", str(TASK / "tests" / "test_outputs.py"),
                        "-p", "no:cacheprovider", "-q", "--no-header"],
                       capture_output=True, text=True, env=env, cwd=str(TASK / "tests"))
    print("grader exit %d in %.1fs" % (g.returncode, time.time() - t1))
    print(g.stdout[-3000:])
    print(g.stderr[-1500:])
    print("REWARD", 1 if (r.returncode == 0 and g.returncode == 0) else 0)
    if "--keep" not in sys.argv:
        shutil.rmtree(room, ignore_errors=True)
    else:
        print("room", room)
    return 0


sys.exit(main())
