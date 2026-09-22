#!/usr/bin/env python3
"""Two-stage trial on this host, because the container registry is not reachable here.

tools/docker_trial.py is the real thing and is what the platform does. It cannot run in this
session: the egress policy denies Docker Hub's blob CDN, so no base image can be pulled. This
stands in for it as closely as one machine allows, and it is honest about the difference.

What it reproduces, because tests/test.sh is run verbatim as root:
  * the agent stage sees only the shipped tree and may write anywhere inside it;
  * the verifier stage sees only the declared artifacts at their absolute paths, on top of the
    directories tests/Dockerfile creates - never the agent's tree;
  * the privilege drop to uid 2201, the wall clock on stage one, the root-owned chmod 700 reward
    directory and sealed model, the reaper, and the reward written last.

What it does not reproduce: the image builds, filesystem isolation beyond the wipe between the
two stages, and the platform's own artifact upload. Container evidence is container evidence;
this is not it.

    python3 host_trial.py oracle | nop | --cheat <path> | --dir <overlay> | --all | --variants
"""
from __future__ import annotations

import fcntl
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "owed-check-rewind"
LOCK = Path(tempfile.gettempdir()) / "ocr-host-trial.lock"
APP, TESTS, SCRATCH, LOGS = Path("/app"), Path("/tests"), Path("/scratch"), Path("/logs")


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
        script = Path(script).resolve()
        if bundle:
            room = Path(tempfile.mkdtemp(prefix="ocr-sol-"))
            shutil.copytree(script.parent, room / "solution")
            script = room / "solution" / script.name
        # cwd is /app, so a relative path would silently not exist; it was resolved above,
        # and the exit status is reported rather than ignored.
        proc = subprocess.run(["bash", str(script)], cwd=str(APP), capture_output=True,
                              text=True, timeout=3600)
        if proc.returncode != 0:
            print("    agent script exited %d: %s" % (proc.returncode, proc.stderr[-300:]),
                  flush=True)
    out = Path(tempfile.mkdtemp(prefix="ocr-art-"))
    for path in artifacts():
        src = Path(path)
        if src.is_file():
            dst = out / path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return out


def verifier_stage(art):
    """Rebuild the verifier container's view: its own directories, plus the uploaded artifacts."""
    for d in (APP, TESTS, SCRATCH, LOGS):
        wipe(d)
    for d in (APP / "tx", LOGS / "verifier", SCRATCH):
        d.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TASK / "tests", TESTS)
    for p in TESTS.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    os.chmod(TESTS / "seal", 0o700)
    os.chmod(TESTS / "test.sh", 0o755)
    for path in artifacts():
        src = art / path.lstrip("/")
        if src.is_file():
            shutil.copy(src, Path(path))
            os.chmod(path, 0o644)
    started = time.time()
    proc = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True)
    spent = time.time() - started
    try:
        reward = int((LOGS / "verifier" / "reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    return reward, proc, spent


def trial(name, script, want, bundle=False):
    art = agent_stage(script, bundle)
    reward, proc, spent = verifier_stage(art)
    shutil.rmtree(art, ignore_errors=True)
    tail = [ln for ln in proc.stdout.splitlines()
            if "passed" in ln or "failed" in ln or "stage one" in ln or "error" in ln]
    ok = reward == want
    print("[%s] reward=%d expected=%d -> %s (%.1fs)" % (name, reward, want,
                                                      "PASS" if ok else "FAIL", spent), flush=True)
    for ln in tail[-3:]:
        print("    " + ln.strip()[:220], flush=True)
    # A probe's reward says nothing about which layer stopped it (CLAUDE.md, token-seam-emit):
    # print what the probe itself saw from inside the run, and which tests failed.
    log = SCRATCH / "probe.log"
    if log.is_file():
        for ln in log.read_text(errors="replace").splitlines()[:12]:
            print("    probe: " + ln[:200], flush=True)
        failed = [ln.split(" - ")[0] for ln in proc.stdout.splitlines()
                  if ln.startswith(("FAILED", "ERROR"))]
        print("    failing: %d, first %s" % (len(failed), failed[:2]), flush=True)
    if not ok:
        print("\n".join("    | " + ln[:220] for ln in proc.stdout.splitlines()[-30:]), flush=True)
        print("\n".join("    ! " + ln[:220] for ln in proc.stderr.splitlines()[-10:]), flush=True)
    return ok


def from_dir(d):
    """Turn a directory of tx files into an agent script, for variant checks."""
    by_base = {Path(a).name: a for a in artifacts()}
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for f in sorted(Path(d).glob("*.py")):
        target = by_base.get(f.name)
        if target is None:
            continue
        lines += ["cat > %s <<'PYEOF'" % target, f.read_text().rstrip("\n"), "PYEOF", ""]
    out = Path(tempfile.mkdtemp(prefix="ocr-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    # /app, /tests, /scratch and /logs are fixed absolute paths, so two runs at once read each
    # other's trees and report nonsense (CLAUDE.md, publish-settle-order). The lock stops that.
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
        return 0 if trial(Path(argv[1]).name, Path(argv[1]), 0) else 1
    if what == "--dir":
        return 0 if trial("variant: " + Path(argv[1]).name, from_dir(argv[1]), 1) else 1
    if what == "--variants":
        res = [trial("variant: " + d.name, from_dir(d), 1)
               for d in sorted((HERE / "variants").iterdir()) if d.is_dir()]
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
