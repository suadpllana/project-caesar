#!/usr/bin/env python3
"""The two-stage trial, emulated on this host. Never ships.

`tools/docker_trial.py` is the real thing and needs two images; this session cannot build them,
because the egress policy denies the registry's blob host. So this stages the same three
directories the platform does - the agent's `/app`, the verifier's `/tests` and the sandbox's
`/work` - runs the same `tests/test.sh` with the same privilege drop, and reads the same
`/logs/verifier/reward.txt`. What it does NOT prove is the image build, so the Dockerfiles are
checked separately by `tools/imagecheck.py`.

It writes absolute paths, so it takes a lock: two copies of a fixed-path harness are one run
with the rows interleaved (CLAUDE.md, publish-settle-order).

    python3 -u authoring/lock-cover-wake/host_trial.py oracle
    python3 -u authoring/lock-cover-wake/host_trial.py nop
    python3 -u authoring/lock-cover-wake/host_trial.py --cheats
    python3 -u authoring/lock-cover-wake/host_trial.py --dir authoring/lock-cover-wake/variants/ok-flat
"""
import fcntl
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ARTS = ["lk/%s" % p for p in lab.PARTS]
LOCK = Path("/tmp/lock-cover-wake-host.lock")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def stage_agent():
    shutil.rmtree("/app", ignore_errors=True)
    shutil.copytree(lab.SRC, "/app", ignore=shutil.ignore_patterns("__pycache__"))


def stage_verifier(collected):
    shutil.rmtree("/app", ignore_errors=True)
    os.makedirs("/app/lk", exist_ok=True)
    for rel, text in collected.items():
        dest = Path("/app") / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(text)
    shutil.rmtree("/tests", ignore_errors=True)
    shutil.copytree(lab.TASK / "tests", "/tests", ignore=shutil.ignore_patterns("__pycache__"))
    os.chmod("/tests/seal", 0o700)
    os.chmod("/tests/test.sh", 0o755)
    shutil.rmtree("/work", ignore_errors=True)
    shutil.rmtree("/logs", ignore_errors=True)
    os.makedirs("/logs/verifier", exist_ok=True)


def collect():
    out = {}
    for rel in ARTS:
        p = Path("/app") / rel
        if p.is_file():
            out[rel] = p.read_bytes()
    return out


def trial(name, script, want, bundle=False, timeout=1800):
    stage_agent()
    agent_log = ""
    if script is not None:
        if bundle:
            room = Path(tempfile.mkdtemp(prefix="lcw-sol-"))
            shutil.copytree(script.parent, room / "solution")
            cmd = ["bash", str(room / "solution" / script.name)]
        else:
            cmd = ["bash", str(script.resolve())]
        done = sh(cmd, cwd="/app", timeout=timeout)
        agent_log = (done.stdout + done.stderr)[-300:]
        if done.returncode != 0:
            print("    agent script exited %d: %s" % (done.returncode, agent_log.strip()[-200:]))
    collected = collect()
    stage_verifier(collected)
    done = sh(["bash", "/tests/test.sh"], timeout=timeout)
    reward = 0
    p = Path("/logs/verifier/reward.txt")
    if p.is_file():
        try:
            reward = int(p.read_text().strip() or 0)
        except ValueError:
            reward = 0
    tail = [ln for ln in (done.stdout + done.stderr).splitlines()
            if " passed" in ln or " failed" in ln or "error" in ln.lower()]
    ok = reward == want
    print("[%-34s] reward=%d expected=%d %s   %s"
          % (name, reward, want, "PASS" if ok else "FAIL", tail[-1].strip() if tail else ""))
    return ok


def main():
    argv = sys.argv[1:]
    lock = open(LOCK, "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    res = []
    if not argv or argv[0] == "--all":
        argv = ["oracle", "nop", "--cheats"]
    i = 0
    while i < len(argv):
        what = argv[i]
        if what == "oracle":
            res.append(trial("oracle", lab.TASK / "solution" / "solve.sh", 1, bundle=True))
        elif what == "nop":
            res.append(trial("nop", None, 0))
        elif what == "--cheats":
            for cheat in sorted((lab.TASK / "cheat").glob("*.sh")):
                res.append(trial("cheat: " + cheat.stem, cheat, 0))
        elif what == "--dir":
            i += 1
            d = Path(argv[i])
            room = Path(tempfile.mkdtemp(prefix="lcw-var-"))
            out = room / "v.sh"
            body = ["#!/bin/bash", "set -euo pipefail", ""]
            for part in lab.PARTS:
                body += ["cat > /app/lk/%s <<'PYEOF'" % part,
                         (d / part).read_text().rstrip("\n"), "PYEOF", ""]
            out.write_text("\n".join(body) + "\n")
            res.append(trial("variant: " + d.name, out, 1))
        else:
            res.append(trial(what, Path(what), 0))
        i += 1
    print("\n%d/%d trials behaved as required" % (sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
