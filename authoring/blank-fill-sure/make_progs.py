"""Write the sample programs that ship in /app/progs, from fixed seeds.

tiny.txt is written by hand and carries the brief's worked example. The other three are built
here so that they have the shapes the graded population has:

  shop.txt   a medium program in which every everyday mechanism appears once or twice
  wide.txt   one program of the wide family, for timing
  flags.txt  one program of the flag family, for timing

None ships with its report. Every file is written with LF line endings and checked for CR.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tasks", "blank-fill-sure")
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen  # noqa: E402

OUT = os.path.join(TASK, "environment", "app_src", "progs")
BIG = gen.BIG


def shop(rng):
    L = ["table cust 0..%d 1..12 0..%d" % (BIG, BIG),
         "table reg 1..12 ann|bob|cyd",
         "table acct 0..%d 0..%d open|shut|held" % (BIG, BIG),
         "table hold 0..%d" % BIG,
         "table leg 0..%d 0..%d 0..%d" % (BIG, BIG, BIG),
         "table stop 0..%d" % BIG,
         "table seen 1..8"]
    lab = gen.Namer("x")
    custs = rng.sample(range(100, 999), 24)
    regions = {}
    for c in custs:
        r = lab() if rng.random() < 0.3 else str(rng.randint(1, 12))
        regions[c] = r
        s = lab() if rng.random() < 0.3 else str(rng.randint(0, 5000))
        L.append("row cust %d %s %s" % (c, r, s))
    for g in range(1, 13):
        L.append("row reg %d %s" % (g, "ann" if g % 3 else "bob"))
    L.append("row reg %d cyd" % rng.randint(1, 12))
    for c in rng.sample(custs, 5):
        if regions[c].startswith("?"):
            L.append("row seen %s" % regions[c])
    aid = 5000
    for c in custs:
        for _ in range(rng.randint(1, 3)):
            aid += 1
            st = lab() if rng.random() < 0.4 else rng.choice(["open", "shut", "held"])
            L.append("row acct %d %d %s" % (aid, c, st))
            if rng.random() < 0.25:
                L.append("row hold %d" % aid)
    for i in range(30):
        d = lab() if rng.random() < 0.3 else str(rng.randint(0, 40))
        L.append("row leg %d %d %s" % (7000 + i, rng.choice(custs), d))
    for v in (0, 5, 10):
        L.append("row stop %d" % v)
    L.append("rule boss X M :- cust(X, R, _), reg(R, M)")
    L.append("rule east X :- cust(X, R, _), reg(R, ann)")
    L.append("rule east X :- cust(X, R, _), reg(R, bob)")
    L.append("rule live C :- acct(_, C, open)")
    L.append("rule live C :- acct(A, C, S), S != open, hold(A)")
    L.append("rule gone A :- acct(A, _, shut)")
    L.append("rule go L :- leg(L, _, D), D != 0")
    L.append("rule go L :- leg(L, _, D), stop(D)")
    L.append("rule pair X Y :- cust(X, _, S), cust(Y, _, S)")
    return L


def write(name, lines):
    text = "\n".join(lines) + "\n"
    assert "\r" not in text
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("%-10s %6d lines" % (name, len(lines)))


def main():
    write("shop.txt", shop(random.Random("shop")))
    write("wide.txt", gen.wide(random.Random("sample-wide")))
    write("flags.txt", gen.flags(random.Random("sample-flags")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
