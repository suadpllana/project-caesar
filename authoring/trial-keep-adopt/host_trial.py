"""Two-stage trial on this host, because the container registry is not reachable here.

`tools/docker_trial.py` is the real thing and is what the platform does; it cannot run in this
session because the egress policy denies Docker Hub's blob CDN, so no base image can be pulled.
This stands in as closely as one machine allows, running `tests/test.sh` verbatim as root.

What it reproduces: the agent stage sees only the shipped tree and writes where it likes inside
it; the verifier stage sees only the declared artifacts at their absolute paths on top of the
directories the verifier image creates; the privilege drop to uid 1002, the session and wall
clock around the worker, the root-owned chmod 700 reward channel, the survivor reap, and the
reward written last. What it does not: the image build, filesystem isolation between the stages
beyond the wipe, and the platform's own artifact upload. Container evidence is container
evidence; this is not it.

    sudo python3 host_trial.py oracle | nop | --cheat <path> | --dir <d> | --variants | --all
"""
from __future__ import annotations

import fcntl
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "trial-keep-adopt"
LOCK = pathlib.Path("/tmp/tka-host-trial.lock")
APP = pathlib.Path("/app")
TESTS = pathlib.Path("/tests")
WORK = pathlib.Path("/work")
LOGS = pathlib.Path("/logs/verifier")


def artifacts():
    text = (TASK / "task.toml").read_text()
    block = text.split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block)]


def wipe(path):
    if path.exists():
        shutil.rmtree(path)


def agent_stage(script, bundle):
    wipe(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP)
    if script is not None:
        proc = subprocess.run(["bash", str(pathlib.Path(script).resolve())], cwd=str(APP),
                              capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            print("    agent script exited %d: %s" % (proc.returncode, proc.stderr[-300:]),
                  flush=True)
    out = pathlib.Path(tempfile.mkdtemp(prefix="tka-art-"))
    for path in artifacts():
        src = pathlib.Path(path)
        if src.is_file():
            dst = out / path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return out


def verifier_stage(art):
    wipe(APP)
    wipe(TESTS)
    wipe(WORK)
    wipe(LOGS.parent)
    for d in (APP / "fld", WORK, LOGS):
        d.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TASK / "tests", TESTS)
    subprocess.run(["chmod", "700", str(TESTS / "seal")], check=False)
    for path in artifacts():
        src = art / path.lstrip("/")
        if src.is_file():
            dst = pathlib.Path(path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    proc = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
    try:
        reward = int((LOGS / "reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    return reward, proc


def trial(name, script, want, bundle=False):
    art = agent_stage(script, bundle)
    reward, proc = verifier_stage(art)
    shutil.rmtree(art, ignore_errors=True)
    err = [ln for ln in proc.stderr.splitlines()
           if any(k in ln for k in ("uid ", "answer key", "planted", "shrank", "WRITTEN",
                                    "reaped", "worker exit"))]
    for ln in err[:6]:
        print("    log| " + ln[:200], flush=True)
    tail = [ln for ln in proc.stdout.splitlines()
            if "passed" in ln or "failed" in ln or "error" in ln]
    ok = reward == want
    print("[%s] reward=%d expected=%d -> %s" % (name, reward, want, "PASS" if ok else "FAIL"),
          flush=True)
    if tail:
        print("    " + tail[-1].strip(), flush=True)
    if not ok:
        print("\n".join("    " + ln for ln in proc.stdout.splitlines()[-20:]), flush=True)
    return ok


def from_dir(d):
    by_base = {pathlib.Path(a).name: a for a in artifacts()}
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for f in sorted(d.glob("*.py")):
        target = by_base.get(f.name)
        if target is None:
            continue
        lines += ["cat > %s <<'PYEOF'" % target, f.read_text().rstrip("\n"), "PYEOF", ""]
    out = pathlib.Path(tempfile.mkdtemp(prefix="tka-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    fd = os.open(str(LOCK), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit("another host_trial.py is running (%s)" % LOCK)
    what = argv[0] if argv else "--all"
    if what == "oracle":
        return 0 if trial("oracle", TASK / "solution" / "solve.sh", 1, bundle=True) else 1
    if what == "nop":
        return 0 if trial("nop", None, 0) else 1
    if what == "--cheat":
        return 0 if trial(pathlib.Path(argv[1]).name, pathlib.Path(argv[1]), 0) else 1
    if what == "--dir":
        d = pathlib.Path(argv[1])
        return 0 if trial("variant: " + d.name, from_dir(d), 1) else 1
    if what == "--variants":
        res = []
        for d in sorted((pathlib.Path(__file__).resolve().parent / "variants").iterdir()):
            if d.is_dir():
                res.append(trial("variant: " + d.name, from_dir(d), 1))
        print("%d/%d correct variants scored 1" % (sum(res), len(res)))
        return 0 if all(res) else 1
    if what == "--all":
        res = [trial("oracle", TASK / "solution" / "solve.sh", 1, bundle=True),
               trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("*.sh")):
            res.append(trial(cheat.name, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
