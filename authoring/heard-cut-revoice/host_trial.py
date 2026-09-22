"""Host emulation of tests/test.sh: worker, then grader, without Docker or a privilege drop.

Authoring only. It proves the grading logic and measures the worker's wall clock against the
limit; it proves nothing about isolation, which only tools/docker_trial.py exercises. Every
path it writes is under a fresh tempfile.mkdtemp, never inside tasks/.

    python authoring/heard-cut-revoice/host_trial.py <reader-dir-or-ref-or-ship> [--seed S]
"""
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "heard-cut-revoice")
TESTS = os.path.join(TASK, "tests")
PARTS = ("look.py", "know.py", "watch.py", "unit.py", "line.py", "voice.py")


def main(argv):
    who = argv[1]
    seed = argv[argv.index("--seed") + 1] if "--seed" in argv else secrets.token_hex(16)
    src = {"ref": os.path.join(TASK, "solution"),
           "ship": os.path.join(TASK, "environment", "app_src", "sr")}.get(who, who)
    room = tempfile.mkdtemp(prefix="hcr-host-")
    try:
        sub = os.path.join(room, "sub")
        work = os.path.join(room, "work")
        logs = os.path.join(room, "logs")
        tests = os.path.join(room, "tests")
        for d in (sub, work, logs):
            os.makedirs(d)
        shutil.copytree(TESTS, tests, ignore=shutil.ignore_patterns("__pycache__"))
        for p in PARTS:
            if os.path.isfile(os.path.join(src, p)):
                shutil.copy(os.path.join(src, p), os.path.join(sub, p))
        for d in (work, logs):
            with open(os.path.join(d, "nonce"), "w") as fh:
                fh.write(seed + "\n")
            with open(os.path.join(d, "per"), "w") as fh:
                fh.write("30\n")
        env = dict(os.environ, HCR_TESTS=tests, HCR_WORK=work, HCR_SUB=sub,
                   HCR_SEAL=os.path.join(tests, "seal"), HCR_LOGS=logs,
                   PYTHONDONTWRITEBYTECODE="1")
        t0 = time.perf_counter()
        w = subprocess.run([sys.executable, os.path.join(tests, "worker.py"), "--out",
                            os.path.join(work, "worker_out.json")], env=env,
                           capture_output=True, text=True)
        took = time.perf_counter() - t0
        print("worker exit %d in %.2fs %s" % (w.returncode, took, w.stderr[-300:]))
        g = subprocess.run([sys.executable, "-m", "pytest", os.path.join(tests, "test_outputs.py"),
                            "-p", "no:cacheprovider", "-q", "-x"], env=env, cwd=tests,
                           capture_output=True, text=True)
        tail = [ln for ln in g.stdout.splitlines() if ln.strip()][-3:]
        print("grader exit %d: %s" % (g.returncode, " | ".join(tail)))
        if g.returncode != 0 and "-v" in argv:
            print(g.stdout[-4000:], g.stderr[-2000:])
        reward = 1 if (w.returncode == 0 and g.returncode == 0) else 0
        print("REWARD=%d" % reward)
        return 0
    finally:
        shutil.rmtree(room, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
