"""No seat in any shipped register may be taken on a tied average.

This exists because of a measured failure, not a worry. `ok-latekey` is the reference with
one letter changed: the combined hand is called "~~" instead of "+". It disagreed with the
reference on three of the six registers first written by hand, because a tied average is
settled by whichever name sorts first, and the name a submission gives to a hand of
several holders is its own business. That is a run-audit rejection in waiting: two correct
submissions, different answers.

tests/gen.py guarantees tie freedom for generated registers by construction. This checks
the ones written by hand, which nothing else covers.

Usage:
    python3 authoring/tiecheck.py
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402


def files():
    out = sorted((TASK / "environment" / "app_src" / "regs").glob("*.txt"))
    cases = TASK / "tests" / "cases.py"
    if cases.is_file():
        sys.path.insert(0, str(TASK / "tests"))
        import cases as mod
        return [(name, text) for name, text in mod.CASES] + \
               [(p.name, p.read_text(encoding="utf-8")) for p in out]
    return [(p.name, p.read_text(encoding="utf-8")) for p in out]


def main():
    bad = 0
    for name, text in files():
        ok = gen.clean([ln for ln in text.splitlines() if ln.strip()])
        if not ok:
            bad += 1
        print("   %-28s %s" % (name, "clean" if ok else "TIED - a seat here is decided by "
                                                       "the name of a hand"))
    print()
    print("   %d register(s) carry a tied seat" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
