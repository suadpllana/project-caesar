"""Two-stage trial on this host, for when no container image can be pulled.

Emulates the platform's separate-mode run as closely as a single machine allows:

  1  agent stage: a fresh /app built from environment/app_src (what the agent image holds),
     and the agent script (solve.sh, a cheat, or nothing) run in it as root;
  2  the declared artifacts - the three files under /app/rs - are carried over, and nothing else;
  3  verifier stage: /app, /tests, /work and /logs/verifier are wiped, tests/ is copied to
     /tests, the artifacts are put back at their absolute paths, and tests/test.sh runs as root.

What it does not emulate: the two stages share one kernel and one host, so this is not evidence
about container isolation; the image build is skipped; the Python here is the host's (3.11, where
the image has 3.12); memory is capped only with --mem, and then as an address-space limit, under
which an allocation fails with MemoryError where the container's cgroup would kill the process. The
privilege drop, the locked reward directory, the sealed 0700 model and the survivor reaping are
all exercised for real, because test.sh does them itself.

It writes fixed absolute paths, so it takes a lock: two copies running at once would be one run
with the rows interleaved (CLAUDE.md, 2026-09-08).

Usage:
    python3 authoring/blank-fill-sure/host_trial.py oracle
    python3 authoring/blank-fill-sure/host_trial.py nop
    python3 authoring/blank-fill-sure/host_trial.py <path/to/agent-script.sh>
    python3 authoring/blank-fill-sure/host_trial.py --parts <dir with cmp.py join.py keep.py>
    add --mem 2048 to any of them to cap the verifier's memory as task.toml caps the container
"""
import fcntl
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "blank-fill-sure")
ARTIFACTS = ("/app/rs/cmp.py", "/app/rs/join.py", "/app/rs/keep.py")
LOCK = "/tmp/bfs-host-trial.lock"


def wipe(path):
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def agent_stage(script, parts):
    wipe("/app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), "/app")
    status = 0
    if parts:
        for a in ARTIFACTS:
            src = os.path.join(parts, os.path.basename(a))
            if os.path.isfile(src):
                shutil.copyfile(src, a)
    elif script:
        res = subprocess.run(["bash", script], cwd="/app", capture_output=True, text=True)
        status = res.returncode
        if res.returncode != 0:
            sys.stderr.write(res.stdout[-2000:] + res.stderr[-2000:])
    carried = {}
    for a in ARTIFACTS:
        if os.path.isfile(a):
            with open(a, "rb") as fh:
                carried[a] = fh.read()
    return status, carried


def verifier_stage(carried, mem_mb=None):
    for p in ("/app", "/tests", "/work", "/logs/verifier"):
        wipe(p)
    shutil.copytree(os.path.join(TASK, "tests"), "/tests",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    os.makedirs("/app/rs", exist_ok=True)
    os.makedirs("/logs/verifier", exist_ok=True)
    os.makedirs("/work", exist_ok=True)
    for a, data in carried.items():
        with open(a, "wb") as fh:
            fh.write(data)
    t0 = time.time()
    cmd = ["bash", "/tests/test.sh"]
    if mem_mb:
        # The container's memory_mb, as an address-space cap on the verifier and everything it
        # starts: this host has 16 GB and no cgroup, so without it a reading that eats memory
        # runs until the host kills something else.
        cmd = ["prlimit", "--as=%d" % (mem_mb * 1024 * 1024)] + cmd
    res = subprocess.run(cmd, capture_output=True, text=True)
    took = time.time() - t0
    try:
        with open("/logs/verifier/reward.txt", encoding="utf-8") as fh:
            reward = fh.read().strip()
    except OSError:
        reward = "missing"
    return reward, took, res


def main():
    args = sys.argv[1:]
    parts = script = None
    label = args[0] if args else "nop"
    if label == "--parts":
        parts = os.path.abspath(args[1])
        label = "parts:" + os.path.basename(parts.rstrip("/"))
    elif label == "oracle":
        script = os.path.join(TASK, "solution", "solve.sh")
    elif label != "nop":
        script = os.path.abspath(label)
        label = os.path.basename(label)
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        status, carried = agent_stage(script, parts)
        mem = int(sys.argv[sys.argv.index("--mem") + 1]) if "--mem" in sys.argv else None
        reward, took, res = verifier_stage(carried, mem)
    tail = [l for l in (res.stdout + res.stderr).splitlines() if l.strip()]
    worker = next((l for l in tail if l.startswith("worker exit status")), "worker exit status ?")
    summary = next((l for l in reversed(tail) if " passed" in l or " failed" in l or " error" in l),
                   tail[-1] if tail else "")
    print("%-34s reward %s  (%s; %s; agent script %d; %.1fs)"
          % (label, reward, worker, summary.strip(), status, took))
    if "-v" in sys.argv:
        print("\n".join(tail[-40:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
