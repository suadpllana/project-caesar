"""Two-stage trial on this host, because the container registry is not reachable here.

`tools/docker_trial.py` is the real thing and is what the platform does. It cannot run in this
session: the egress policy denies Docker Hub's blob CDN, so no base image can be pulled. This
stands in for it as closely as one machine allows, and it is honest about the difference.

What it does reproduce, because `tests/test.sh` is run verbatim as root:
  * the agent stage sees only the shipped tree and writes wherever it likes inside it;
  * the verifier stage sees only the declared artifacts, at their absolute paths, on top of the
    directories the verifier image creates - not the agent's tree;
  * the privilege drop to uid 1002, the session and wall clock around the worker, the
    root-owned `chmod 700` reward channel, the survivor reap, and the reward written last.

What it does not reproduce: image build, filesystem isolation between the two stages beyond
what the wipe gives, and the platform's own artifact upload. Container evidence is container
evidence; this is not it.

    python3 host_trial.py oracle | nop | --cheat <path> | --dir <overlay> | --all
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

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order"
LOCK = pathlib.Path("/tmp/pso-host-trial.lock")
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
    """Give the agent the shipped tree, run its script, hand back the declared artifacts."""
    wipe(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP)
    if script is not None:
        # cwd is /app, so a relative script path would silently not exist - which once made a
        # cheat look like a no-op and report a clean row. Resolve it, and check it ran.
        proc = subprocess.run(["bash", str(pathlib.Path(script).resolve())], cwd=str(APP),
                              capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            print("    agent script exited %d: %s" % (proc.returncode, proc.stderr[-300:]),
                  flush=True)
    out = pathlib.Path(tempfile.mkdtemp(prefix="pso-art-"))
    for path in artifacts():
        src = pathlib.Path(path)
        if src.is_file():
            dst = out / path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return out


def verifier_stage(art):
    """Rebuild the verifier container's view: its own dirs, plus the uploaded artifacts."""
    wipe(APP)
    wipe(TESTS)
    wipe(WORK)
    wipe(LOGS.parent)
    for d in (APP / "link", WORK, LOGS):
        d.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TASK / "tests", TESTS)
    for path in artifacts():
        src = art / path.lstrip("/")
        if src.is_file():
            dst = pathlib.Path(path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    proc = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
    reward = 0
    try:
        reward = int((LOGS / "reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    return reward, proc


def trial(name, script, want, bundle=False):
    art = agent_stage(script, bundle)
    reward, proc = verifier_stage(art)
    shutil.rmtree(art, ignore_errors=True)
    note = WORK / "probe.log"
    if note.is_file():
        for ln in note.read_text().splitlines():
            print("    probe| " + ln[:200], flush=True)
    tail = [ln for ln in proc.stdout.splitlines() if "passed" in ln or "failed" in ln or "error" in ln]
    ok = reward == want
    print("[%s] reward=%d expected=%d -> %s" % (name, reward, want, "PASS" if ok else "FAIL"), flush=True)
    if tail:
        print("    " + tail[-1].strip(), flush=True)
    if not ok:
        print("\n".join("    " + ln for ln in proc.stdout.splitlines()[-25:]), flush=True)
    return ok


def from_dir(d):
    """Turn a directory of link files into an agent script, for variant checks."""
    by_base = {pathlib.Path(a).name: a for a in artifacts()}
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for f in sorted(d.glob("*.py")):
        target = by_base.get(f.name)
        if target is None:
            continue
        lines += ["cat > %s <<'PYEOF'" % target, f.read_text().rstrip("\n"), "PYEOF", ""]
    out = pathlib.Path(tempfile.mkdtemp(prefix="pso-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    # /app, /tests, /work and /logs are fixed absolute paths, so two runs at once read each
    # other's tree and report nonsense. This was measured once; the lock stops it happening.
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
