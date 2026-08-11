#!/usr/bin/env python3
"""Offline harness emulation for the turn-seam-alignment task.

The real platform builds two images and runs the agent and the verifier in separate
containers. Where a registry is unavailable this reproduces the same sequence on the
host, at the same absolute paths the containers use:

  1. populate /app from environment/app_src (the agent image's COPY)
  2. run an agent script (the reference solution, a cheat, or nothing at all)
  3. copy the four declared artifacts onto a pristine tree, exactly as tests/test.sh does
  4. run the engine over the scenario set, then the verifier's pytest suite
  5. print the reward the verifier would write to /logs/verifier/reward.txt

It does not reproduce the privilege drop or the reward-channel lockdown, so the
reward-tamper cheats must be checked on the real images with `harbor run`.

Usage:
    python3 tools/run_local_seam.py oracle
    python3 tools/run_local_seam.py nop
    python3 tools/run_local_seam.py cheat/cheat-full-encode.sh
    python3 tools/run_local_seam.py --all
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "tasks" / "turn-seam-alignment"
APP = Path("/app")
LOGS = Path("/logs/verifier")
EDITABLE = ["tok/inc.py", "tok/store.py", "loop/ep.py", "loop/rec.py"]


def reset_app() -> None:
    if APP.exists():
        shutil.rmtree(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP)
    LOGS.mkdir(parents=True, exist_ok=True)
    for stale in (LOGS / "reward.txt", LOGS / "ctrf.json"):
        stale.unlink(missing_ok=True)


def run_agent(script: Path | None) -> None:
    if script is None:
        return
    proc = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    if proc.returncode != 0:
        print("    agent script exited %d" % proc.returncode)
        for line in (proc.stderr or proc.stdout).strip().splitlines()[-4:]:
            print("      " + line)


def verify(work: Path) -> int:
    app = work / "app"
    shutil.copytree(TASK / "tests" / "pristine", app)
    for rel in EDITABLE:
        src = APP / rel
        if src.is_file():
            shutil.copyfile(src, app / rel)
    out = work / "out.json"
    env = dict(os.environ)
    env.update({"APPDIR": str(app), "PYTHONDONTWRITEBYTECODE": "1"})
    subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                   capture_output=True, text=True, env=env, timeout=900)
    env["RUN_OUT"] = str(out)
    env["PYTHONPATH"] = str(TASK / "tests")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q",
                           str(TASK / "tests" / "test_outputs.py")],
                          capture_output=True, text=True, env=env)
    reward = 1 if proc.returncode == 0 else 0
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").write_text("%d\n" % reward)
    summary = [ln for ln in proc.stdout.splitlines() if "passed" in ln or "failed" in ln]
    if summary:
        print("    " + summary[-1].strip())
    return reward


def trial(name: str, script: Path | None, want: int) -> bool:
    print("[%s]" % name)
    reset_app()
    run_agent(script)
    with tempfile.TemporaryDirectory() as tmp:
        reward = verify(Path(tmp))
    ok = reward == want
    print("    reward=%d expected=%d -> %s\n" % (reward, want, "PASS" if ok else "FAIL"))
    return ok


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    if argv[1] == "--all":
        results = [trial("oracle", TASK / "solution" / "solve.sh", 1),
                   trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("*.sh")):
            results.append(trial("cheat: " + cheat.name, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(results), len(results)))
        return 0 if all(results) else 1

    if argv[1] == "oracle":
        return 0 if trial("oracle", TASK / "solution" / "solve.sh", 1) else 1
    if argv[1] == "nop":
        return 0 if trial("nop", None, 0) else 1

    script = Path(argv[1]) if Path(argv[1]).is_absolute() else (ROOT / argv[1])
    if not script.is_file():
        script = TASK / argv[1]
    if not script.is_file():
        print("no such script: " + argv[1])
        return 2
    return 0 if trial(script.name, script, 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
