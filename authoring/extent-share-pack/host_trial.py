"""Run the whole verifier flow on this host, with no container.

Stages a work directory, drops a chosen set of six files in as the submission, runs the worker the
way test.sh does and then the grader, and reports the reward. It proves the grading logic and the
timings; it proves nothing about the isolation, which needs the two-image run in
tools/docker_trial.py. A lock file keeps two copies from sharing the fixed paths.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "extent-share-pack"
PARTS = ("ext.py", "pt.py", "pk.py", "step.py", "tot.py", "own.py")
WALL = 60


def main():
    over = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else TASK / "solution"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    room = pathlib.Path(tempfile.mkdtemp(prefix="esp-trial-"))
    work, logs, sub = room / "work", room / "logs", room / "app" / "st"
    for d in (work, logs, sub):
        d.mkdir(parents=True)
    for part in PARTS:
        one = over / part
        if one.is_file():
            shutil.copy(one, sub / part)
        else:
            shutil.copy(TASK / "environment" / "app_src" / "st" / part, sub / part)
    (logs / "nonce").write_text("hosttrial%d\n" % int(time.time()), encoding="utf-8")
    (logs / "per").write_text("%d\n" % per, encoding="utf-8")
    shutil.copy(logs / "nonce", work / "nonce")
    shutil.copy(logs / "per", work / "per")

    env = dict(os.environ)
    env.update({"ESP_TESTS": str(TASK / "tests"), "ESP_WORK": str(work),
                "ESP_SUB": str(sub), "ESP_SEAL": str(TASK / "tests" / "seal"),
                "ESP_LOGS": str(logs), "PYTHONDONTWRITEBYTECODE": "1"})
    t0 = time.time()
    try:
        code = subprocess.run([sys.executable, str(TASK / "tests" / "worker.py"),
                               "--out", str(work / "worker_out.json")],
                              env=env, timeout=WALL).returncode
    except subprocess.TimeoutExpired:
        code = 124
    t1 = time.time()
    print("worker exit %d in %.1f s (limit %d)" % (code, t1 - t0, WALL))
    graded = subprocess.run([sys.executable, "-m", "pytest",
                             str(TASK / "tests" / "test_outputs.py"),
                             "-p", "no:cacheprovider", "-q", "--no-header"],
                            env=env, cwd=str(TASK / "tests"))
    t2 = time.time()
    reward = 1 if (code == 0 and graded.returncode == 0) else 0
    print("grader %.1f s   reward=%d" % (t2 - t1, reward))
    shutil.rmtree(room, ignore_errors=True)
    return 0 if reward else 1


if __name__ == "__main__":
    sys.exit(main())
