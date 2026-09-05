"""Expected trails for the enumerated cases, derived by hand from the brief's rules before
either implementation was consulted, and re-checked row by row against both.

This is the reviewer's demand made mechanical: both implementations here have one author,
so their agreeing proves only that the author read the rules the same way twice. These
literals are the third reading. build_gt.py refuses to write a ground truth that differs
from them, and this file fails on its own if either implementation drifts.

Usage: python3 authoring/handcheck.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

EXPECT = {
    "comp-arrows-do-not-wrap": "w1 w1 w2 w3 w3 w2 w1 w1",
    "comp-back-lands-on-memory": "w1 w2 w3 w5 w3 w1 w3",
    "comp-empty-is-no-stop": "w1 w1 w3 w1 w1 w2",
    "comp-is-one-stop": "w1 w2 w3 w4 w5 w4",
    "comp-memory-from-request": "w1 w4 w5 w4 w5 w1",
    "comp-memory-gone": "w1 w2 w3 w4 w5 w5 w2 w5 w5 w3",
    "group-none-selected": "w1 w2 w4 w4 w3",
    "group-selected-is-the-stop": "w1 w3 w5 w5 w4 w1",
    "group-selected-unreachable": "w1 w2 w4 w4 w3",
    "group-unselected-holds-focus": "w1 w3 w4 w3 w2",
    "lost-container-dropped": "w1 w2 w3 none w4",
    "lost-container-dropped-then-parent": "w1 w2 none none w4",
    "lost-insert-at-the-point": "w1 w2 none none w5",
    "lost-inside-composite": "w1 w2 none w4 w3",
    "lost-moved-under-hidden": "w1 w2 none w3 w3 w2",
    "lost-point-at-the-end": "w1 w3 none w1 w2",
    "lost-point-does-not-move": "w1 w2 none none w4",
    "lost-starts-after-the-widget": "w1 w2 w3 none w4 w2 w1 none w4",
    "lost-widget-shown-again": "w1 w2 none none w3 w2 w1",
    "pick-keeps-focus": "w1 w1 w2 w3",
    "pop-out-of-order": "a1 a2 b1 b2 c1 c1 a2 a3",
    "pop-out-of-order-target-gone": "a1 a2 b1 b2 c1 c1 c1 none a3",
    "pop-out-of-order-twice": "a1 a2 b1 c1 c2 d1 d1 d1 a2",
    "pop-restores-lazily": "w1 w2 d1 d1 d1 w2 w3",
    "pop-restores-the-widget": "w1 w2 d1 d1 w2 w3",
    "pop-target-dropped": "w1 w2 d1 d1 none w3",
    "pop-target-still-unreachable": "w1 w2 d1 d1 none w3 w1 w3",
    "pop-the-last-screen": "w1 w2 none none d1 d1 none none",
    "push-lands-on-auto": "w1 d3 d4 w1",
    "push-nothing-to-take": "w1 none none none d1",
    "push-without-auto": "w1 d1",
    "reach-inherits-disabled-focused": "w1 none w2 w2 w1",
    "reach-inherits-hidden": "w1 none w2 w3 w3 w1",
    "reach-inherits-shut": "w1 w2 none w3 w3 w2",
    "want-held-beats-the-return": "w1 w2 d1 d1 w3",
    "want-held-before-the-push": "w1 w1 d3",
    "want-held-for-a-screen-below": "w1 d1 d1 d1 w3",
    "want-held-latest-wins": "w1 d1 d1 d1 w2",
    "want-held-re-enabled-before-return": "w1 d1 d1 d1 d1 w2",
    "want-held-unreachable-at-return": "w1 d1 d1 d1 none w3",
    "want-inside-composite": "w1 w3 w3 w1 w3",
    "want-unreachable-is-ignored": "w1 w1 w3 w3 w1",
    "comp-keys-leave-it": "w1 w2 w3 w1 w3 none w1 w2 none w4",
    "push-over-nothing": "w1 w2 none d1 none w3 w3 w2",
    "pop-out-of-order-with-held": "a1 b1 c1 c1 c1 c1 c1 a3 a1",
    "comp-back-from-dropped-place": "w1 w2 w3 w2 none w1 w3 none w1",
}


def main():
    import cases
    import harness
    import oracle
    names = sorted(cases.CASES)
    missing = [n for n in names if n not in EXPECT]
    extra = [n for n in EXPECT if n not in cases.CASES]
    if missing or extra:
        print("case set and hand-checked set differ: missing %s extra %s" % (missing, extra))
        return 1
    refs = harness.run_many(harness.REF, [cases.CASES[n] for n in names])
    bad = 0
    for n, r in zip(names, refs):
        want = tuple(EXPECT[n].split())
        got_ref = harness.trail(r)
        got_orc = tuple(oracle.solve(cases.CASES[n]))
        if got_ref != want or got_orc != want:
            bad += 1
            print("%-40s hand %s\n%-40s ref  %s\n%-40s orc  %s" % (
                n, " ".join(want), "", " ".join(got_ref), "", " ".join(got_orc)))
    print("%d cases, %d disagree with the hand-derived trails" % (len(names), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
