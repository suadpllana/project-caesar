#!/usr/bin/env python3
"""Two-stage trial on this host, because no base image can be pulled here. Never ships.

`tools/docker_trial.py` is what the platform does and cannot run in this session: the egress
policy refuses Docker Hub's blob CDN, so no image builds. This stands in for it as closely as
one machine allows, and says where it differs.

Reproduced, because `tests/test.sh` runs verbatim as root on the real absolute paths:
  * the agent stage sees only the shipped tree at /app and may write anywhere in it;
  * the verifier stage sees only the declared artifacts, at their absolute paths, on top of the
    directories the verifier image creates - not the agent's tree;
  * the privilege drop to uid 1002, the session and 60 second clock around the worker, the
    root-owned 0700 reward and seal directories, the exam written by root, the survivor reap,
    the reward written last.

Not reproduced: the image build (the host runs Python 3.11, the images 3.12), filesystem
isolation beyond the wipe between stages, and the platform's artifact upload. Container
evidence is container evidence; this is not it.

    python3 -u host_trial.py oracle | nop | --cheat <script> | --dir <overlay> | --variants | --all
"""
import fcntl
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "glob-route-hide"
LOCK = pathlib.Path("/tmp/grh-host-trial.lock")
APP = pathlib.Path("/app")
TESTS = pathlib.Path("/tests")
WORK = pathlib.Path("/work")
EXAM = pathlib.Path("/exam")
LOGS = pathlib.Path("/logs/verifier")


def artifacts():
    text = (TASK / "task.toml").read_text()
    block = text.split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block)]


def wipe(path):
    if path.exists():
        shutil.rmtree(path)


def agent_stage(script):
    """Give the agent the shipped tree, run its script, hand back the declared artifacts."""
    wipe(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP)
    if script is not None:
        # cwd is /app, so a relative script path would silently not exist: resolve it, and
        # report a script that failed rather than letting it pass for a no-op.
        proc = subprocess.run(["bash", str(pathlib.Path(script).resolve())], cwd=str(APP),
                              capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0:
            print("    agent script exited %d: %s" % (proc.returncode, proc.stderr[-300:]),
                  flush=True)
    out = pathlib.Path(tempfile.mkdtemp(prefix="grh-art-"))
    for path in artifacts():
        src = pathlib.Path(path)
        if src.is_file():
            dst = out / path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return out


def verifier_stage(art):
    """Rebuild the verifier container's view: its own directories plus the artifacts."""
    for d in (APP, TESTS, WORK, EXAM, LOGS.parent):
        wipe(d)
    for d in (APP / "fe", WORK, LOGS):
        d.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TASK / "tests", TESTS, ignore=shutil.ignore_patterns("__pycache__"))
    os.chmod(TESTS / "seal", 0o700)
    for path in artifacts():
        src = art / path.lstrip("/")
        if src.is_file():
            dst = pathlib.Path(path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    t0 = time.time()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True,
                          env=env)
    took = time.time() - t0
    try:
        reward = int((LOGS / "reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    return reward, proc, took


def trial(name, script, want):
    art = agent_stage(script)
    reward, proc, took = verifier_stage(art)
    shutil.rmtree(art, ignore_errors=True)
    probe = WORK / "probe.log"
    if probe.is_file():
        for ln in probe.read_text().splitlines()[:6]:
            print("    probe| " + ln[:200], flush=True)
    worker = [ln for ln in proc.stdout.splitlines() if ln.startswith("worker exited")]
    summary = [ln for ln in proc.stdout.splitlines()
               if re.search(r"\d+ (passed|failed|error)", ln)]
    ok = reward == want
    print("[%s] reward=%d expected=%d -> %s (%.1fs; %s; %s)" % (
        name, reward, want, "PASS" if ok else "FAIL", took,
        worker[-1] if worker else "worker line missing",
        summary[-1].strip() if summary else "no pytest summary"), flush=True)
    if not ok:
        print("\n".join("    " + ln for ln in (proc.stdout + proc.stderr).splitlines()[-30:]),
              flush=True)
    return ok


def from_dir(d):
    """Turn a directory of resolution files into an agent script, for variant checks."""
    by_base = {pathlib.Path(a).name: a for a in artifacts()}
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for f in sorted(pathlib.Path(d).glob("*.py")):
        target = by_base.get(f.name)
        if target is None:
            continue
        lines += ["cat > %s <<'PYEOF'" % target, f.read_text().rstrip("\n"), "PYEOF", ""]
    out = pathlib.Path(tempfile.mkdtemp(prefix="grh-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    # Fixed absolute paths: two runs at once would read each other's trees.
    fd = os.open(str(LOCK), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit("another host_trial.py is running (%s)" % LOCK)
    what = argv[0] if argv else "--all"
    if what == "oracle":
        return 0 if trial("oracle", TASK / "solution" / "solve.sh", 1) else 1
    if what == "nop":
        return 0 if trial("nop", None, 0) else 1
    if what == "--cheat":
        return 0 if trial(pathlib.Path(argv[1]).name, pathlib.Path(argv[1]), 0) else 1
    if what == "--dir":
        return 0 if trial("variant " + pathlib.Path(argv[1]).name, from_dir(argv[1]), 1) else 1
    if what == "--variants":
        res = [trial("variant " + d.name, from_dir(d), 1)
               for d in sorted((HERE / "variants").iterdir()) if d.is_dir()]
        print("%d/%d correct variants scored 1" % (sum(res), len(res)))
        return 0 if res and all(res) else 1
    if what == "--all":
        res = [trial("oracle", TASK / "solution" / "solve.sh", 1), trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("*.sh")):
            res.append(trial(cheat.name, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
