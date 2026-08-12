#!/usr/bin/env python3
"""Alternative correct solutions must score 1.

The cheat suite proves the verifier catches wrong answers. This proves the mirror image:
that it does not fail a right one for making a different implementation choice. Each
directory under authoring/variants/ is a complete set of the editable files implementing
the same semantics a different way, and every one of them must come out clean on every
graded field.

Three of them are the readings of the resume condition the reference did not take. Those
are the ones the character window exists for, and two of them are what the ceiling is
measured from, so a change that narrows the window shows up here immediately.

If one of these fails, the verifier is grading a choice rather than the work, and the
graded set is what has to change - not the variant.

Usage:  python3 authoring/variant_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import field_report  # noqa: E402
import scen  # noqa: E402


def main() -> int:
    root = TASK / "authoring" / "variants"
    dirs = sorted(d for d in root.iterdir() if d.is_dir() and d.name.startswith("ok-"))
    if not dirs:
        print("no ok-* variants to check - run authoring/emit.py")
        return 1
    bad = 0
    for d in dirs:
        sig = field_report.signature(str(d))
        hits = {(n, f) for n, fs in sig.items() for f in fs}
        if hits:
            bad += 1
            print("FAIL %s" % d.name)
            for name, fields in sorted(sig.items()):
                if fields:
                    print("      %-13s %s" % (name, " ".join(fields)))
        else:
            print("ok   %-18s (%d scenarios clean)" % (d.name, len(scen.SCENARIOS)))
    if bad:
        print("\n%d alternative correct solution(s) fail the verifier" % bad)
        return 1
    print("\nevery alternative correct solution scores clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
