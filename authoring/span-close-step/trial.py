"""Host emulation of one trial: agent script, then the sealed verifier.

Docker cannot pull a base image in this workspace, so the two-container runner is
unavailable and this stands in for it. It reproduces the *grading* faithfully -
the same worker, the same pytest module, the same nonce generation after the agent
has finished - and nothing else: it does not drop privileges, does not lock the
reward channel and does not reap survivors, so it is evidence about semantics and
never about the verifier's isolation.

    python3 authoring/span-close-step/trial.py oracle
    python3 authoring/span-close-step/trial.py nop
    python3 authoring/span-close-step/trial.py --dir authoring/span-close-step/variants/ok-flat
    python3 authoring/span-close-step/trial.py --all
"""
import contextlib
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "span-close-step"
ENV = TASK / "environment" / "app_src"
TESTS = TASK / "tests"
PARTS = ("pick.py", "fold.py", "norm.py", "turn.py", "again.py", "keep.py")


@contextlib.contextmanager
def at_app(app):
    """Publish the staged tree at /app, the absolute path the bundle really uses.

    solve.sh and every cheat address /app because that is where the image puts the
    tree; running them against a copy under another name would not be running them
    at all. A real /app that predates this run is left alone and the emulation
    refuses rather than overwriting somebody's directory.
    """
    link = pathlib.Path("/app")
    made = False
    if not link.exists():
        link.symlink_to(app)
        made = True
    elif not link.is_symlink():
        raise SystemExit("/app exists and is not this emulation's symlink")
    else:
        link.unlink()
        link.symlink_to(app)
        made = True
    try:
        yield
    finally:
        if made and link.is_symlink():
            link.unlink()


def stage_app(work):
    """The agent container's /app, before the agent has done anything."""
    app = work / "app"
    shutil.copytree(ENV, app)
    return app


def run_agent(app, kind, script=None, policy=None):
    """`oracle` runs solution/solve.sh; `nop` does nothing; a dir is dropped in."""
    if kind == "nop":
        return 0
    if kind == "oracle":
        with at_app(app):
            proc = subprocess.run(["bash", str(TASK / "solution" / "solve.sh")],
                                  capture_output=True, text=True, cwd=str(app))
        if proc.returncode != 0:
            print(proc.stderr[-1200:])
        return proc.returncode
    if kind == "dir":
        for name in PARTS:
            one = pathlib.Path(policy) / name
            if one.is_file():
                shutil.copy(one, app / "train" / name)
        return 0
    if kind == "sh":
        with at_app(app):
            proc = subprocess.run(["bash", str(script)], capture_output=True, text=True,
                                  cwd=str(app))
        return proc.returncode
    raise ValueError(kind)


def verify(work, app):
    logs = work / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "reward.txt").write_text("0\n", encoding="utf-8", newline="\n")
    nonce = os.urandom(16).hex()
    (logs / "nonce").write_text(nonce + "\n", encoding="utf-8", newline="\n")
    (logs / "per").write_text("55\n", encoding="utf-8", newline="\n")
    wk = work / "work"
    wk.mkdir(parents=True, exist_ok=True)
    shutil.copy(logs / "nonce", wk / "nonce")
    shutil.copy(logs / "per", wk / "per")

    env = dict(os.environ)
    env.update({"SCS_TESTS": str(TESTS), "SCS_WORK": str(wk), "SCS_LOGS": str(logs),
                "SCS_SUB": str(app / "train"), "PYTHONDONTWRITEBYTECODE": "1"})
    planned = subprocess.run([sys.executable, str(TESTS / "seal" / "plan.py"),
                              "--out", str(wk / "scripts.json"), "--logs", str(logs)],
                             capture_output=True, text=True, env=env)
    if planned.returncode != 0:
        raise SystemExit(planned.stderr[-2000:])
    worker = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                             "--scripts", str(wk / "scripts.json"),
                             "--out", str(wk / "worker_out.json")],
                            capture_output=True, text=True, env=env)
    graded = subprocess.run([sys.executable, "-m", "pytest",
                             str(TESTS / "seal" / "test_outputs.py"),
                             "-p", "no:cacheprovider", "-q", "-rEf"],
                            capture_output=True, text=True, env=env,
                            cwd=str(TESTS / "seal"))
    ok = worker.returncode == 0 and graded.returncode == 0
    return (1 if ok else 0), worker, graded


def detail(kind, script=None, policy=None):
    """Run one trial and report the reward plus why it came out that way."""
    work = pathlib.Path(tempfile.mkdtemp(prefix="scs-trial-"))
    try:
        app = stage_app(work)
        agent = run_agent(app, kind, script, policy)
        reward, worker, graded = verify(work, app)
        failed = []
        for line in graded.stdout.splitlines():
            if line.startswith("FAILED ") or line.startswith("ERROR "):
                head = line.split()[0].lower()
                failed.append("%s:%s" % (head, line.split()[1].split("::", 1)[-1]))
        return {"reward": reward, "agent": agent, "worker": worker.returncode,
                "failed": failed, "out": graded.stdout, "err": worker.stderr}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def one(kind, script=None, policy=None, show=False):
    got = detail(kind, script, policy)
    if show and got["reward"] == 0:
        print(got["err"][-1500:])
        print(got["out"][-2500:])
    return got["reward"]


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--dir":
        print("dir %s -> %d" % (args[1], one("dir", policy=args[1], show=True)))
        return 0
    if args[0] == "--sh":
        print("sh %s -> %d" % (args[1], one("sh", script=args[1], show=True)))
        return 0
    if args[0] == "--all":
        rc = 0
        for kind, want in (("oracle", 1), ("nop", 0)):
            got = one(kind, show=(kind == "oracle"))
            print("%-8s reward %d (want %d) %s" % (kind, got, want,
                                                   "ok" if got == want else "FAIL"))
            rc |= 0 if got == want else 1
        return rc
    print("%s -> %d" % (args[0], one(args[0], show=True)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
