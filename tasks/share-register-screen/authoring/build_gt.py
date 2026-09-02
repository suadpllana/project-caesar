"""Write tests/gt.json, and refuse to write one that cannot be proved.

Two proofs stand between the reference and a ground truth. Every enumerated register has
to give the same record under the reference and under tests/oracle.py, which shares no
code with it. And the two have to agree on a run of registers nobody chose, because
agreement on a hand-written set is agreement about one person's imagination.

Text is written with an explicit newline, because Path.write_text on a Windows host
translates every one and a CRLF ground truth ships a bundle the structural check rejects.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import cases  # noqa: E402
import fuzz  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402

OUT = TASK / "tests" / "gt.json"
ROUNDS = 1500


def main():
    for name, text in cases.CASES:
        if not gen.clean([ln for ln in text.splitlines() if ln.strip()]):
            print("enumerated register %s has a seat decided on a tied average" % name)
            return 1

    tree = harness.stage(harness.REF)
    rows = harness.drive_text(tree, [t for _, t in cases.CASES])
    truth = {}
    for (name, text), got in zip(cases.CASES, rows):
        want = oracle.determine(text)
        if got != want:
            print("reference and sealed model disagree on %s" % name)
            print("   reference %r" % (got,))
            print("   model     %r" % (want,))
            return 1
        truth[name] = got

    if fuzz.run(ROUNDS):
        print("refusing to write a ground truth the sealed model does not reproduce")
        return 1

    body = {
        "cases": truth,
        "rounds": ROUNDS,
        "note": "records are [company, on the list, seats the list took, seats, seat takers]",
    }
    OUT.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print("wrote %s: %d enumerated registers" % (OUT, len(truth)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
