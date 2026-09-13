"""Differential fuzz: the reference against the sealed model on shaped random tie plans.

    python3 fuzz.py [count] [seed]

Prints every disagreement with the plan, shrunk by dropping lines while it still disagrees.
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

TESTS = lab.TASK / "tests"
sys.path.insert(0, str(TESTS / "seal"))
import model  # noqa: E402

import os
ROOTS = os.environ.get("FUZZ_ROOTS", "abcdefgh")
DEPTH = int(os.environ.get("FUZZ_DEPTH", "3"))
LEAVES = ("k", "v", "x", "y", "z")


def _p(rnd, depth_max=None):
    depth_max = DEPTH if depth_max is None else depth_max
    segs = [rnd.choice(ROOTS)]
    for _ in range(rnd.randint(0, depth_max - 1)):
        segs.append(rnd.choice(LEAVES))
    return ".".join(segs)


def _expr(rnd, deep=2):
    r = rnd.random()
    if deep <= 0 or r < 0.3:
        return "lit %d" % rnd.randint(-5, 9)
    if r < 0.55:
        return "now %s" % _p(rnd)
    if r < 0.7:
        return "old %s" % _p(rnd)
    if r < 0.8:
        return "pick %s %s %s" % (_p(rnd), _expr(rnd, deep - 1), _expr(rnd, deep - 1))
    return "%s %s %s" % (rnd.choice(("sum", "top")), _expr(rnd, deep - 1), _expr(rnd, deep - 1))


def _overlap(a, b):
    a, b = a.split("."), b.split(".")
    return a[:len(b)] == b or b[:len(a)] == a


def plan(rnd):
    lines = []
    layers = rnd.randint(1, 5)
    for _ in range(layers):
        lines.append("lay")
        for _ in range(rnd.randint(1, 7)):
            r = rnd.random()
            g = ""
            if rnd.random() < 0.15:
                g = " if %s %d" % (_p(rnd), rnd.randint(-2, 5)) if rnd.random() < 0.5 else " un %s" % _p(rnd)
            if r < 0.45:
                lines.append("put %s %s%s" % (_p(rnd), _expr(rnd), g))
            elif r < 0.58:
                lines.append("cut %s%s" % (_p(rnd), g))
            elif r < 0.8:
                a, b = _p(rnd, 2), _p(rnd, 2)
                while _overlap(a, b):
                    b = _p(rnd, 2)
                lines.append("tie %s %s%s" % (a, b, g))
            elif r < 0.9:
                lines.append("mix %s %s%s" % (_p(rnd, 2), _p(rnd, 2), g))
            else:
                lines.append("map %s %s%s" % (_p(rnd, 2), _p(rnd, 2), g))
    n = layers
    for _ in range(rnd.randint(4, 10)):
        stop = "" if rnd.random() < 0.5 else " %d" % rnd.randint(0, n)
        if rnd.random() < 0.6:
            lines.append("ask %s%s" % (_p(rnd), stop))
        else:
            lines.append("tot %s%s" % (_p(rnd, 2), stop))
    return "\n".join(lines) + "\n"


def both(lb, text):
    try:
        ref = lb.run(text)
    except RecursionError as exc:
        ref = ["REF RecursionError"]
    mod = model.trace(text)
    return ref, mod


def shrink(lb, text):
    lines = text.rstrip("\n").split("\n")
    changed = True
    while changed:
        changed = False
        for i in range(len(lines)):
            trial = lines[:i] + lines[i + 1:]
            t = "\n".join(trial) + "\n"
            try:
                r, m = both(lb, t)
            except Exception:
                continue
            if r != m:
                lines = trial
                changed = True
                break
    return "\n".join(lines) + "\n"


def main(argv):
    count = int(argv[0]) if argv else 500
    seed = argv[1] if len(argv) > 1 else "flc"
    lb = lab.Lab(lab.TASK / "solution")
    bad = 0
    for i in range(count):
        rnd = random.Random("%s/%d" % (seed, i))
        text = plan(rnd)
        try:
            ref, mod = both(lb, text)
        except ValueError:
            continue
        if ref != mod:
            bad += 1
            small = shrink(lb, text)
            r, m = both(lb, small)
            print("=== disagreement %d (plan %d)\n%s--- ref %s\n--- mod %s" % (bad, i, small, r, m))
            if bad >= 5:
                break
    lb.close()
    print("%d plans, %d disagreements" % (count, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
