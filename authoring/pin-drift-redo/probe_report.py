#!/usr/bin/env python3
"""What each isolation probe actually managed to do, not only what it scored.

A probe that scores 0 for its own reasons proves nothing. Each probe writes what it reached
into /work/pdr-probe.txt while the graded run is in flight; this runs them one at a time and
prints that record beside the reward, so the layer that stopped each one is named.

    python3 -u authoring/pin-drift-redo/probe_report.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import host_trial  # noqa: E402

PROBES = sorted((host_trial.TASK / "cheat").glob("cheat-probe-*.sh"))


def main():
    bad = 0
    for one in PROBES:
        got = host_trial.trial(cheat=one)
        note = Path("/work/pdr-probe.txt")
        told = note.read_text(encoding="utf-8").strip() if note.is_file() else "(nothing)"
        reward = got["reward"]
        if reward != "0":
            bad += 1
        print("%-34s reward=%s" % (one.name, reward))
        for line in told.splitlines():
            print("      %s" % line)
        out = got["out"]
        for line in out.splitlines():
            if "survivors killed" in line or "half one exited" in line:
                print("      [runner] %s" % line.strip())
        print(flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
