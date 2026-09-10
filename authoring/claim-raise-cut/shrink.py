"""Find and shrink a program that separates one reading from the model.

    python3 authoring/claim-raise-cut/shrink.py <flag> [count]

Programs come from the verifier's generator; a candidate stays well formed while it shrinks
(every drop is preceded, inside its own transaction's steps, by an unmatched take of that
item), so the difference is never a malformed step.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TESTS = HERE.parents[1] / "tasks" / "claim-raise-cut" / "tests"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import altmodel  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def well_formed(steps):
    depth = {}
    for st in steps:
        if st[0] == "take":
            depth[(st[1], st[2])] = depth.get((st[1], st[2]), 0) + 1
        elif st[0] == "drop":
            d = depth.get((st[1], st[2]), 0)
            if d <= 0:
                return False
            depth[(st[1], st[2])] = d - 1
    return True


def differs(steps, flag):
    if not steps or not well_formed(steps):
        return False
    try:
        return model.trace(steps) != altmodel.trace(steps, (flag,))
    except Exception:
        return False


def shrink(steps, flag):
    cur = list(steps)
    changed = True
    while changed:
        changed = False
        for i in range(len(cur) - 1, -1, -1):
            cand = cur[:i] + cur[i + 1:]
            if differs(cand, flag):
                cur = cand
                changed = True
                break
    return cur


def main(argv):
    flag = argv[0]
    count = int(argv[1]) if len(argv) > 1 else 3
    found = []
    for name, steps in gen.programs("shrink-seed", 40, 0):
        if differs(steps, flag):
            found.append((name, shrink(steps, flag)))
        if len(found) >= 40:
            break
    found.sort(key=lambda x: len(x[1]))
    for name, small in found[:count]:
        print("== from %s, %d lines" % (name, len(small)))
        for st in small:
            print("   " + " ".join(st))
        print("   model:   ", model.trace(small))
        print("   reading: ", altmodel.trace(small, (flag,)))


if __name__ == "__main__":
    main(sys.argv[1:])
