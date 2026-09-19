#!/usr/bin/env python3
"""Run the real trial on this host, without a container. Never ships.

`tools/docker_trial.py` is what the platform does and is the run that counts. It cannot run in
this session: pulling `python:3.12-slim` fails because the blob host
`production.cloudfront.docker.com` is denied by this environment's egress policy, so neither
image can be built. This reproduces the same flow with the host standing in for both
containers, and it runs the shipped `tests/test.sh` itself rather than an imitation of it - so
the privilege drop, the root-owned 0700 reward channel, the sealed directory, the session, the
wall clock and the reap are all exercised exactly as written.

The flow, per trial:

  1  `/app` is staged from `environment/app_src`, and the agent script runs against it as root,
     which is what the agent container does.
  2  only the six declared artifacts cross over: `/app` is thrown away and rebuilt holding
     nothing but `/app/keep/<the six>`, which is what the platform uploads into the verifier.
  3  `/tests` is a fresh copy of the bundle's `tests/`, `/work` and `/logs` are removed, and
     `bash /tests/test.sh` runs. The reward is read from `/logs/verifier/reward.txt`.

What it still does not reproduce: the container boundary itself. Everything here shares one
kernel and one filesystem with the session, so a probe that escapes into the host is not
escaping into a neighbouring image. The isolation rules it does exercise are the ones
`docs/VERIFIER-ISOLATION.md` names.

Absolute paths again, so it takes a lock: two runs of a fixed-path harness are one run with
the rows interleaved (CLAUDE.md, publish-settle-order).

    python3 -u authoring/link-clear-round/host_trial.py oracle
    python3 -u authoring/link-clear-round/host_trial.py nop
    python3 -u authoring/link-clear-round/host_trial.py --dir <directory of the six files>
    python3 -u authoring/link-clear-round/host_trial.py --cheats
    python3 -u authoring/link-clear-round/host_trial.py --all
"""
import fcntl
import pwd
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

APP = Path("/app")
TESTS = Path("/tests")
WORK = Path("/work")
LOGS = Path("/logs")
LOCK = Path("/tmp/lcr-host-trial.lock")
PARTS = lab.PARTS


def sandbox_user():
    try:
        pwd.getpwuid(1002)
    except KeyError:
        subprocess.run(["useradd", "--uid", "1002", "--no-create-home", "sandbox"],
                       capture_output=True, text=True)


def trial(name, script, want, quiet=False):
    # -- the agent container -----------------------------------------------------------
    shutil.rmtree(APP, ignore_errors=True)
    shutil.copytree(lab.SRC, APP)
    if script is not None:
        done = subprocess.run(["bash", str(script)], cwd=str(APP),
                              capture_output=True, text=True)
        if done.returncode != 0 and not quiet:
            print("    agent script exited %d: %s"
                  % (done.returncode, done.stderr.strip()[-200:]))

    # -- only the declared artifacts cross over ----------------------------------------
    room = Path(tempfile.mkdtemp(prefix="lcr-art-"))
    for part in PARTS:
        one = APP / "keep" / part
        if one.is_file():
            shutil.copy(one, room / part)
    shutil.rmtree(APP, ignore_errors=True)
    (APP / "keep").mkdir(parents=True)
    for part in PARTS:
        if (room / part).is_file():
            shutil.copy(room / part, APP / "keep" / part)
    shutil.rmtree(room, ignore_errors=True)

    # -- the verifier container --------------------------------------------------------
    for path in (TESTS, WORK, LOGS):
        shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(lab.TASK / "tests", TESTS,
                    ignore=shutil.ignore_patterns("__pycache__"))
    (TESTS / "seal").chmod(0o700)
    (TESTS / "test.sh").chmod(0o755)
    LOGS.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
    try:
        reward = int((LOGS / "verifier" / "reward.txt").read_text().strip() or 0)
    except Exception:
        reward = 0
    ok = reward == want
    tail = [ln for ln in run.stdout.splitlines() if "passed" in ln or "failed" in ln]
    print("[%s] reward=%d expected=%d -> %s%s"
          % (name, reward, want, "PASS" if ok else "FAIL",
             "  " + tail[-1].strip() if tail and not ok else ""))
    if not ok and not quiet:
        print("    " + "\n    ".join(run.stdout.strip().splitlines()[-12:]))
    return ok


def main(argv):
    sandbox_user()
    LOCK.touch()
    with LOCK.open("w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        what = argv[1] if len(argv) > 1 else "--all"
        res = []
        if what in ("oracle", "--all"):
            res.append(trial("oracle", lab.SOL / "solve.sh", 1))
        if what in ("nop", "--all"):
            res.append(trial("nop", None, 0))
        if what == "--dir":
            here = Path(argv[2])
            script = Path(tempfile.mkdtemp()) / "v.sh"
            body = ["#!/bin/bash", "set -euo pipefail", ""]
            for part in PARTS:
                body += ["cat > /app/keep/%s <<'PYEOF'" % part,
                         (here / part).read_text(encoding="utf-8").rstrip("\n"), "PYEOF", ""]
            script.write_text("\n".join(body) + "\n", encoding="utf-8")
            res.append(trial("variant: " + here.name, script, 1))
        if what in ("--cheats", "--all"):
            for cheat in sorted((lab.TASK / "cheat").glob("*.sh")):
                res.append(trial("cheat: " + cheat.name, cheat, 0, quiet=True))
        print("\n%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
