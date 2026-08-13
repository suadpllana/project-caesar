#!/usr/bin/env python3
"""Every alternative correct implementation must score 1 through the real verifier.

This is the cheat suite's mirror image and it is the gate the run audit actually applies.
A graded quantity that two correct implementations disagree on is a trap: an agent that
has solved the problem can only close the gap by tuning an internal detail against a
hidden constant, and the audit calls that reward hacking whatever the author intended.

The variants deliberately differ in the things that must NOT matter:

  ok-store-scan      derives the accountable live set from the row store group listing
                     instead of walking the cell's dependency map.
  ok-early-exit      one pass with a list and no set comprehension; same predicate.
  ok-implied-check   drops the explicit membership branch, which the accountable count
                     already implies once the retracted values are seeded into it.
  ok-no-group-filter omits the r.g == g filter, which the dependency map already implies.

If any of these fails, fix the ENVIRONMENT or the contract so the two readings agree.
Never loosen the verifier to make one pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

import trial  # noqa: E402


def main() -> int:
    vs = sorted((TASK / "authoring" / "variants").glob("ok-*"))
    if not vs:
        print("no variants found")
        return 1
    bad = 0
    for d in vs:
        r, tail = trial.grade("authoring/variants/" + d.name)
        if r != 1:
            bad += 1
            print("BAD %-20s reward=%d" % (d.name, r))
            print(tail)
        else:
            print("OK  %-20s reward=1" % d.name)
    print("\n%d variants, %d failed" % (len(vs), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
