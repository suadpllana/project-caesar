"""Host emulation of one trial: agent phase, artifact hand-over, verifier phase.

    python trial.py oracle | nop | cheat:<path to .sh> | variant:<dir> [--keep]

Docker cannot pull base images in this session (egress policy), so this runs the real
tests/test.sh on the host, with the same absolute paths and the same two unprivileged users
the verifier image creates. It is evidence about the verifier's logic and isolation, not
about the container build; the report says which.

The agent phase acts on a fresh /app built from environment/app_src. The verifier phase
then sees only the declared artifacts, as the platform uploads them: /app is wiped and
/app/dbg holds only marks.py, frames.py and steps.py from the agent phase.
"""
import fcntl
import json
import os
import pwd
import shutil
import subprocess
import sys
import time

from lab import APP, TASK

LOCK = "/tmp/lss-trial.lock"
ARTIFACTS = ("marks.py", "frames.py", "steps.py")


def ensure_user(name, uid):
    try:
        pwd.getpwnam(name)
        return
    except KeyError:
        pass
    subprocess.run(["groupadd", "--gid", str(uid), name], check=True)
    subprocess.run(["useradd", "--uid", str(uid), "--gid", str(uid), "--no-create-home",
                    "--shell", "/usr/sbin/nologin", name], check=True)


def reset(path):
    if os.path.lexists(path):
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def agent_phase(action):
    reset("/app")
    shutil.copytree(APP, "/app")
    if action == "nop":
        return
    if action == "oracle":
        subprocess.run(["bash", os.path.join(TASK, "solution", "solve.sh")], check=True, cwd="/app")
        return
    kind, _, arg = action.partition(":")
    if kind == "cheat":
        r = subprocess.run(["bash", os.path.abspath(arg)], cwd="/app")
        if r.returncode != 0:
            raise SystemExit("cheat script failed with status %d" % r.returncode)
        return
    if kind == "variant":
        for f in ARTIFACTS:
            p = os.path.join(arg, f)
            if os.path.exists(p):
                shutil.copy(p, os.path.join("/app/dbg", f))
        return
    raise SystemExit("unknown action " + action)


def handover():
    kept = {}
    for f in ARTIFACTS:
        p = os.path.join("/app/dbg", f)
        if os.path.isfile(p):
            kept[f] = open(p, "rb").read()
    reset("/app")
    os.makedirs("/app/dbg")
    for f, b in kept.items():
        with open(os.path.join("/app/dbg", f), "wb") as fh:
            fh.write(b)
    return sorted(kept)


def verifier_phase(timeout):
    for p in ("/tests", "/work", "/logs/verifier", "/var/lib/judge"):
        reset(p)
    shutil.copytree(os.path.join(TASK, "tests"), "/tests")
    os.makedirs("/logs/verifier")
    t = time.monotonic()
    env = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root",
           "LANG": "C.UTF-8"}
    r = subprocess.run(["bash", "/tests/test.sh"], capture_output=True, text=True, timeout=timeout,
                       env=env)
    dt = time.monotonic() - t
    reward = open("/logs/verifier/reward.txt").read().strip() if os.path.exists("/logs/verifier/reward.txt") else None
    verdict = None
    if os.path.exists("/var/lib/judge/verdict.json"):
        verdict = json.load(open("/var/lib/judge/verdict.json"))
    return reward, verdict, dt, r


def main():
    action = sys.argv[1]
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        ensure_user("dbgr", 2201)
        ensure_user("tgtr", 2202)
        agent_phase(action)
        handed = handover()
        reward, verdict, dt, r = verifier_phase(timeout=3600)
        tail = [ln for ln in r.stdout.splitlines() if ln.startswith(("PASSED", "FAILED", "ERROR"))]
        out = {"action": action, "reward": reward, "handed": handed, "secs": round(dt, 1),
               "verdict": verdict, "pytest": tail}
        print(json.dumps(out, indent=1))
        if "--keep" not in sys.argv:
            for p in ("/app", "/tests", "/work"):
                reset(p)


if __name__ == "__main__":
    main()
