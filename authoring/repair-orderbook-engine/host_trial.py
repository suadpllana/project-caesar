"""tests/test.sh verbatim on this host, as root, because Docker's daemon is not reachable here.

`tools/docker_trial.py` is the real thing and is what the platform does. This stands in for it
as closely as one machine allows, and is honest about the difference.

What it reproduces, because `tests/test.sh` is run unchanged as root: the agent stage sees
only the shipped tree; the verifier stage sees only the declared artifacts at their absolute
paths on top of the directories the verifier image creates; the privilege drop to uid 1002,
the session and wall clock around the worker, the root-owned `chmod 700` reward channel, the
/proc survivor reap, and the reward written last. The verifier image's own preparation is
mirrored by hand: /pristine moved out of /tests, the sealed files 0600, the readable ones
0644, PYTHONPATH=/tests, and `python`/`pytest` resolving to a 3.12 interpreter carrying
pytest==9.1.1 and pytest-json-ctrf==0.5.2 (the venv at /opt/py312, or $PY312).

What it does not reproduce: the image build and filesystem isolation between the two stages
beyond what the wipe gives. Container evidence is container evidence; this is not it.

    python3 host_trial.py oracle | nop | --cheat <name> | --dir <overlay> | --all
"""
from __future__ import annotations

import fcntl
import os
import pathlib
import pwd
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
HERE = ROOT / "authoring" / "repair-orderbook-engine"
LOCK = pathlib.Path("/tmp/roe-host-trial.lock")
APP = pathlib.Path("/app")
TESTS = pathlib.Path("/tests")
PRISTINE = pathlib.Path("/pristine")
WORK = pathlib.Path("/work")
LOGS = pathlib.Path("/logs/verifier")
PY312 = pathlib.Path(os.environ.get("PY312", "/opt/py312/bin"))
SEALED = ("gt.json", "oracle.py", "test_outputs.py", "test_lifecycle.py")
READABLE = ("runner.py", "gen.py", "cases.py", "reap.py")


def artifacts():
    text = (TASK / "task.toml").read_text()
    block = text.split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', block)]


def wipe(path):
    if path.exists():
        shutil.rmtree(path)


def ensure_sandbox():
    try:
        pwd.getpwuid(1002)
    except KeyError:
        subprocess.run(["useradd", "--uid", "1002", "--create-home", "--shell",
                        "/usr/sbin/nologin", "sandbox"], check=True)


def agent_stage(script):
    """Give the agent the shipped tree, run its script, hand back the declared artifacts."""
    wipe(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if script is not None:
        proc = subprocess.run(["bash", str(pathlib.Path(script).resolve())], cwd=str(APP),
                              capture_output=True, text=True, timeout=1800,
                              env=dict(os.environ, APP=str(APP)))
        if proc.returncode != 0:
            print("    agent script exited %d: %s" % (proc.returncode, proc.stderr[-300:]),
                  flush=True)
    out = pathlib.Path(tempfile.mkdtemp(prefix="roe-art-"))
    for path in artifacts():
        src = pathlib.Path(path)
        if src.is_file():
            dst = out / path.lstrip("/")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    return out


def verifier_stage(art):
    """Rebuild the verifier container's view, then run tests/test.sh unchanged."""
    ensure_sandbox()
    for d in (APP, TESTS, PRISTINE, WORK, LOGS.parent):
        wipe(d)
    shutil.copytree(TASK / "tests", TESTS, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.move(str(TESTS / "pristine"), str(PRISTINE))
    (APP / "eng").mkdir(parents=True)
    LOGS.mkdir(parents=True)
    os.chmod(TESTS, 0o755)
    for fn in SEALED:
        os.chmod(TESTS / fn, 0o600)
    for fn in READABLE:
        os.chmod(TESTS / fn, 0o644)
    for path in artifacts():
        src = art / path.lstrip("/")
        if src.is_file():
            dst = pathlib.Path(path)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    env = dict(os.environ, PATH="%s:%s" % (PY312, os.environ.get("PATH", "")),
               PYTHONPATH=str(TESTS), PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(["bash", str(TESTS / "test.sh")], capture_output=True, text=True,
                          env=env, cwd="/")
    reward = 0
    try:
        reward = int((LOGS / "reward.txt").read_text().strip() or 0)
    except (OSError, ValueError):
        reward = 0
    return reward, proc


def trial(name, script, want):
    art = agent_stage(script)
    reward, proc = verifier_stage(art)
    shutil.rmtree(art, ignore_errors=True)
    tail = [ln for ln in proc.stdout.splitlines() if "passed" in ln or "failed" in ln]
    failed = sorted(set(re.findall(r"^FAILED .*?::(\w+)", proc.stdout, re.M)))
    ok = reward == want
    print("[%s] reward=%d expected=%d -> %s   %s" % (
        name, reward, want, "PASS" if ok else "FAIL", ",".join(failed)[:110]), flush=True)
    if tail:
        print("    " + tail[-1].strip(), flush=True)
    if not ok:
        print("\n".join("    " + ln for ln in (proc.stdout + proc.stderr).splitlines()[-25:]),
              flush=True)
    return ok


def from_dir(d):
    by_base = {pathlib.Path(a).name: a for a in artifacts()}
    lines = ["#!/bin/bash", "set -euo pipefail", ""]
    for f in sorted(pathlib.Path(d).glob("*.py")):
        target = by_base.get(f.name)
        if target is None:
            continue
        lines += ["cat > %s <<'PYEOF'" % target, f.read_text().rstrip("\n"), "PYEOF", ""]
    out = pathlib.Path(tempfile.mkdtemp(prefix="roe-var-")) / "variant.sh"
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv):
    if os.geteuid() != 0:
        raise SystemExit("test.sh drops privileges with setpriv; run this as root")
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
        p = TASK / "cheat" / ("cheat-%s.sh" % argv[1])
        return 0 if trial(p.stem, p, 0) else 1
    if what == "--dir":
        d = pathlib.Path(argv[1])
        return 0 if trial("variant: " + d.name, from_dir(d), 1) else 1
    if what == "--variants":
        res = [trial("variant: " + d.name, from_dir(d), 1)
               for d in sorted((HERE / "variants").iterdir()) if d.is_dir()]
        print("%d/%d correct variants scored 1" % (sum(res), len(res)))
        return 0 if all(res) else 1
    if what == "--all":
        res = [trial("oracle", TASK / "solution" / "solve.sh", 1), trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("cheat-*.sh")):
            res.append(trial(cheat.stem, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
