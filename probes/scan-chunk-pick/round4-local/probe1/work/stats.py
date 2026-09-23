"""Count how often interesting branches fire on random files."""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "app"))

import gen  # noqa: E402
import run_scan  # noqa: E402
from scn import proj, step  # noqa: E402

C = Counter()

orig_need = proj._need


def need(mem, pids, sup, dsingle):
    res = orig_need(mem, pids, sup, dsingle)
    blocked = False
    for pid in pids:
        pg = mem.pobj[pid]
        if mem.read[pid] or sup.get(pid) or pg.nulls >= pg.n or mem.plo[pid] == mem.phi[pid] or (dsingle and mem.pis[pid]):
            continue
        blocked = True
    for pid in pids:
        s = sup.get(pid)
        if not s or mem.read[pid]:
            continue
        pg = mem.pobj[pid]
        full = s == pg.n
        single = mem.plo[pid] == mem.phi[pid] or (dsingle and mem.pis[pid])
        if pg.nulls >= pg.n:
            C["skip-allnull"] += 1
        elif single:
            C["single-" + ("skip" if (full or pg.nulls == 0) else "read") + ("-dict" if (dsingle and mem.pis[pid]) else "-bounds")] += 1
        else:
            C["general-" + ("full" if full else "part") + ("-blocked" if blocked else "-free")] += 1
    return res


proj._need = need

orig_consult = step.consult


def consult(st, g, out):
    C["pick-consult"] += 1
    n0 = len(out.lines)
    orig_consult(st, g, out)
    return None


step.consult = consult


def main():
    a, b = int(sys.argv[1]), int(sys.argv[2])
    big = len(sys.argv) > 3
    for seed in range(a, b):
        lines = run_scan.run(gen.make(seed, big))
        # report-side rd: an rd line after a sel line within the same query
        after = False
        for ln in lines:
            if ln.startswith("qry"):
                after = False
            elif ln.startswith("sel"):
                after = True
            elif ln.startswith("rd") and after:
                C["proj-rd"] += 1
            elif ln.startswith("dc") and after:
                C["proj-dc"] += 1
            elif ln.startswith("dc"):
                C["pick-dc"] += 1
    for k, v in sorted(C.items()):
        print(k, v)


if __name__ == "__main__":
    main()
