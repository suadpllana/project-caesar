#!/usr/bin/env python3
"""Hold the hand-written corners to what they claim to be.

A worked example that does not exercise the tier it was written for is a false
affordance: it reads as a pin and pins nothing. Every pair in the merge block
of casegen.FIXED has to be one that a rule counting runs of moves answers
differently, and the block as a whole has to straddle the boundary in both
directions -- pairs that move when the width is read as one fewer, and pairs
that move when it is read as one more -- or the brief's number is not pinned
by anything the grader runs.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "earliest-change-script"
sys.path.insert(0, str(TASK / "tests"))

import altrules
import casegen
import oracle

MERGE_BLOCK = 16            # the last N entries of FIXED are the merge corners


def main():
    block = casegen.FIXED[-MERGE_BLOCK:]
    narrower = altrules.context(oracle.CONTEXT - 1)
    wider = altrules.context(oracle.CONTEXT + 1)

    same_as_runs = []
    moves_narrow = moves_wide = 0
    for before, after in block:
        want = [tuple(op) for op in oracle.script(before, after)]
        if [tuple(op) for op in altrules.runs(before, after)] == want:
            same_as_runs.append((before, after))
        if [tuple(op) for op in narrower(before, after)] != want:
            moves_narrow += 1
        if [tuple(op) for op in wider(before, after)] != want:
            moves_wide += 1

    bad = []
    if same_as_runs:
        bad.append("%d of the %d merge corners are answered the same way by a "
                   "rule that counts runs of moves: %s"
                   % (len(same_as_runs), len(block), same_as_runs[:4]))
    if moves_narrow == 0:
        bad.append("no corner separates the width from one fewer")
    if moves_wide == 0:
        bad.append("no corner separates the width from one more")

    print("merge corners: %d" % len(block))
    print("  answered differently by a runs-of-moves rule: %d of %d"
          % (len(block) - len(same_as_runs), len(block)))
    print("  separating width %d from %d: %d"
          % (oracle.CONTEXT, oracle.CONTEXT - 1, moves_narrow))
    print("  separating width %d from %d: %d"
          % (oracle.CONTEXT, oracle.CONTEXT + 1, moves_wide))
    if bad:
        print("FAIL")
        for line in bad:
            print("  " + line)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
