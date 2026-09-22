#!/usr/bin/env python3
"""A two-stage trial on this host, because no container image can be pulled here. Never ships.

`tools/docker_trial.py` is what the platform does: build both images, run the agent's script in
one, hand the declared artifacts to the other, run tests/test.sh. It cannot run in this session -
the egress policy answers 403 for Docker Hub's blob CDN - so this reproduces as much of it as one
machine allows, and says what it does not.

Reproduced, because tests/test.sh runs verbatim as root:
  * the agent stage sees only the shipped tree, and hands back only the declared artifacts;
  * the verifier stage sees those artifacts at their absolute paths over the directories the
    verifier image creates, never the agent's tree;
  * the drop to uid 1002, the session and clock around stage one, the root-owned 0700 reward
    directory and sealed side, the survivor reap, and the reward written last;
  * Python 3.12 and the pinned pytest, from a venv put first on PATH.

Not reproduced: the image builds, the platform's own artifact upload, and filesystem isolation
between the stages beyond wiping /app, /tests, /work and /logs between them. Container evidence
is container evidence; this is not it.

    python3 -u authoring/restate-hold-plan/host_trial.py oracle | nop | --cheat PATH | --dir DIR
                                                         | --all | --variants
"""
import fcntl
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "restate-hold-plan"
LOCK = Path("/tmp/rhp-host-trial.lock")
VENV = Path("/opt/rhp-venv/bin")
APP, TESTS, WORK, LOGS = Path("/app"), Path("/tests"), Path("/work"), Path("/logs")


def artifacts():
    block = (TASK / "task.toml").read_text().split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block)]


def wipe(path):
    if path.exists():
        shutil.rmtree(path)


def env():
    e = dict(os.environ)
    e["PATH"] = "%s:%s" % (VENV, e.get("PATH", ""))
    for k in [k for k in e if k.startswith("RHP_")]:
        del e[k]
    return e


def agent_stage(script):
    """The shipped tree, the agent's script run in it, and the declared artifacts taken out."""
    wipe(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP)
    if script is not None:
        # /app is the cwd, so a relative script path would silently not exist: resolve it,
        # and report a script that failed rather than scoring it as a clean run.
        done = subprocess.run(["bash", str(Path(script).resolve())], cwd=str(APP), env=env(),
                              capture_output=True, text=True, timeout=3600)
        if done.returncode != 0:
            print("    agent script exited %d: %s" % (done.returncode, done.stderr[-400:]),
                  flush=True)
    taken = Path(tempfile.mkdtemp(prefix="rhp-art-"))
    for path in artifacts():
        if Path(path).is_file():
            dst = taken / path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, dst)
    return taken


def verifier_stage(taken):
    """The verifier image's directories, the uploaded artifacts, and tests/test.sh as root."""
    for path in (APP, TESTS, WORK, LOGS):
        wipe(path)
    for path in (APP / "plan", LOGS / "verifier", WORK):
        path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TASK / "tests", TESTS, ignore=shutil.ignore_patterns("__pycache__"))
    os.chmod(TESTS / "seal", 0o700)
    for path in artifacts():
        src = taken / path.lstrip("/")
        if src.is_file():
            shutil.copy(src, path)
    done = subprocess.run(["bash", str(TESTS / "test.sh")], env=env(), capture_output=True,
                          text=True, timeout=1800)
    try:
        reward = int((LOGS / "verifier" / "reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    return reward, done


def trial(label, script, want):
    taken = agent_stage(script)
    reward, done = verifier_stage(taken)
    shutil.rmtree(taken, ignore_errors=True)
    note = WORK / "probe.log"
    if note.is_file():
        for ln in note.read_text(errors="replace").splitlines()[:6]:
            print("    probe| " + ln[:160], flush=True)
    summary = [ln.strip() for ln in done.stdout.splitlines()
               if "passed" in ln or "failed" in ln or "exited" in ln or "killed" in ln]
    ok = reward == want
    print("[%s] reward=%d expected=%d -> %s" % (label, reward, want, "PASS" if ok else "FAIL"),
          flush=True)
    for ln in summary[-4:]:
        print("    " + ln, flush=True)
    if not ok:
        print("\n".join("    | " + ln for ln in (done.stdout + done.stderr).splitlines()[-30:]),
              flush=True)
    return ok


def from_dir(d):
    """A directory of planner files, as an agent script that writes them into /app/plan."""
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for part in ("keep.py", "reach.py", "look.py", "settle.py", "order.py"):
        f = Path(d) / part
        if f.is_file():
            lines += ["cat > /app/plan/%s <<'PYEOF'" % part, f.read_text().rstrip("\n"),
                      "PYEOF", ""]
    out = Path(tempfile.mkdtemp(prefix="rhp-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


def main(argv):
    # /app, /tests, /work and /logs are fixed absolute paths: two trials at once read each
    # other's tree and report nonsense (CLAUDE.md, publish-settle-order). One at a time.
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
        return 0 if trial(Path(argv[1]).name, argv[1], 0) else 1
    if what == "--dir":
        return 0 if trial("variant " + Path(argv[1]).name, from_dir(argv[1]), 1) else 1
    if what == "--variants":
        res = [trial("variant " + d.name, from_dir(d), 1)
               for d in sorted((HERE / "variants").iterdir()) if d.is_dir()]
        print("%d of %d correct variants scored 1" % (sum(res), len(res)))
        return 0 if all(res) else 1
    if what == "--all":
        res = [trial("oracle", TASK / "solution" / "solve.sh", 1), trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("*.sh")):
            res.append(trial(cheat.name, cheat, 0))
        print("%d of %d trials came out as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
