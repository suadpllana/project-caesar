import sys

from wire import plan
from wire.reg import SING, SCOPED, TRANS, load

LIFE = {"sing": SING, "scoped": SCOPED, "trans": TRANS}


def field(p, i):
    return "" if i >= len(p) or p[i] == "." else p[i]


def parse(path):
    rows = []
    ops = []
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = ln.split()
        if p[0] == "r":
            deps = [] if p[3] == "." else p[3].split(",")
            facs = [] if p[4] == "." else p[4].split(",")
            rows.append((p[1], LIFE[p[2]], deps, facs, field(p, 5), field(p, 6), field(p, 7)))
        elif p[0] == "o":
            ops.append(tuple(p[1:]))
    return load(rows), ops


def main():
    tbl, ops = parse(sys.argv[1])
    for rec in plan.run(tbl, ops):
        print(" ".join(str(x) for x in rec))


main()
