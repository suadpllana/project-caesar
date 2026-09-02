"""The reference against the sealed model, on registers nobody chose.

The enumerated set is twenty-three registers a person wrote, so agreement on it says
something about that person's imagination. This says something about the specification.
Nothing that takes its numbers from the reference is believed until this comes back clean.

Usage:
    python3 authoring/fuzz.py [rounds]
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def run(rounds):
    tree = harness.stage(harness.REF)
    seen = bad = 0
    step = 250
    done = 0
    while done < rounds:
        want = min(step, rounds - done)
        batch = gen.batch("fuzz-%d" % done, want)
        rows = harness.drive_text(tree, [t for _, t in batch])
        for (name, text), got in zip(batch, rows):
            seen += 1
            if got != oracle.determine(text):
                bad += 1
                if bad == 1:
                    print("first disagreement, register %s:\n%s" % (name, text))
        done += want
    print("reference against the sealed model: %d registers, %d disagreements" % (seen, bad))
    return bad


if __name__ == "__main__":
    sys.exit(1 if run(int(sys.argv[1]) if len(sys.argv) > 1 else 800) else 0)
