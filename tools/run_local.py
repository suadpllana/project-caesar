#!/usr/bin/env python3
"""Offline harness emulation for the reaction-network task.

The real platform builds two images and runs the agent and the verifier in separate
containers. Where a container registry is unavailable this script reproduces the same
sequence on the host, at the same absolute paths the containers use:

  1. populate /app from environment/app_src (the agent image's COPY)
  2. run an agent script (the reference solution, a cheat, or nothing at all)
  3. run the verifier's pytest suite against /app/network.json
  4. print the reward the verifier would write to /logs/verifier/reward.txt

Usage:
    python3 tools/run_local.py oracle
    python3 tools/run_local.py nop
    python3 tools/run_local.py cheat/cheat-empty-network.sh
    python3 tools/run_local.py --all
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "tasks" / "reaction-network-reconstruction"
APP = Path("/app")
LOGS = Path("/logs/verifier")


def reset_app() -> None:
    """Recreate /app exactly as environment/Dockerfile leaves it."""
    if APP.exists():
        shutil.rmtree(APP)
    shutil.copytree(TASK / "environment" / "app_src", APP)
    LOGS.mkdir(parents=True, exist_ok=True)
    for stale in (LOGS / "reward.txt", LOGS / "ctrf.json"):
        stale.unlink(missing_ok=True)


def run_agent(script: Path | None) -> int:
    if script is None:
        return 0
    proc = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"    agent script exited {proc.returncode}")
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-4:]
        for line in tail:
            print(f"      {line}")
    return proc.returncode


def run_verifier() -> int:
    """Run the verifier suite the way tests/test.sh does, and return the reward."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(TASK / "tests" / "test_outputs.py")],
        capture_output=True, text=True)
    reward = 1 if proc.returncode == 0 else 0
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").write_text(f"{reward}\n")
    summary = [ln for ln in proc.stdout.splitlines() if "passed" in ln or "failed" in ln]
    if summary:
        print(f"    {summary[-1].strip()}")
    return reward


def trial(name: str, script: Path | None, expected: int) -> bool:
    print(f"[{name}]")
    reset_app()
    run_agent(script)
    reward = run_verifier()
    ok = reward == expected
    print(f"    reward={reward} expected={expected} -> {'PASS' if ok else 'FAIL'}\n")
    return ok


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    if argv[1] == "--all":
        results = [trial("oracle", TASK / "solution" / "solve.sh", 1),
                   trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("*.sh")):
            results.append(trial(f"cheat: {cheat.name}", cheat, 0))
        print(f"{sum(results)}/{len(results)} trials behaved as required")
        return 0 if all(results) else 1

    if argv[1] == "oracle":
        return 0 if trial("oracle", TASK / "solution" / "solve.sh", 1) else 1
    if argv[1] == "nop":
        return 0 if trial("nop", None, 0) else 1

    script = (ROOT / argv[1]) if not Path(argv[1]).is_absolute() else Path(argv[1])
    if not script.is_file():
        script = TASK / argv[1]
    if not script.is_file():
        print(f"no such script: {argv[1]}")
        return 2
    return 0 if trial(script.name, script, 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
