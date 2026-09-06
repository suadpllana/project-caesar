"""Does the specification pick out one timeline, or a family of them?

The graded artifact is compared exactly, so a rule that leaves an internal
ordering free would fail correct submissions. Each permutation below is a
behaviour-preserving rewrite of one reference file - a different iteration
order, a different loop, a different route to the same set - and every one of
them has to produce a byte-identical timeline on every trace. A single
disagreement means the rule that allowed it is underdetermined and belongs in
the instruction or out of the graded set.

Usage: python3 authoring/batch-admit-reclaim/orderfuzz.py [count]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "batch-admit-reclaim", "tests"))

import gen
import play

WORK = os.environ.get("WORK", "/tmp/bar-work")


def edit(name, *swaps):
    with open(os.path.join(play.SOL, name)) as fh:
        text = fh.read()
    for old, new in swaps:
        if old not in text:
            raise SystemExit("stale permutation in %s: %r" % (name, old[:50]))
        text = text.replace(old, new, 1)
    return text


PERMUTED = [
    ("the pool is scanned in the opposite order", "room.py",
     lambda: edit("room.py", ("    for k in pool.blk:", "    for k in sorted(pool.blk, reverse=True):"))),
    ("the losing block is found by sorting rather than by scanning", "room.py",
     lambda: """def pick(pool):
    loose = [k for k in pool.blk if pool.blk[k].refs == 0]
    if not loose:
        return None
    loose.sort(key=lambda k: (pool.blk[k].touch, pool.blk[k].born))
    return loose[0]
"""),
    ("the shadow pool is filled in the opposite order", "fit.py",
     lambda: edit("fit.py", ("    for k in pool.blk:", "    for k in sorted(pool.blk, reverse=True):"))),
    ("the kept prefix is counted by index rather than by walking", "back.py",
     lambda: """from eng.pool import keys


def at(pool, span, r):
    tgt = r.plen if r.have == 0 else r.have
    ks = keys(r.toks, span, tgt)
    n = len(ks)
    for i in range(len(ks)):
        if not pool.has(ks[i]):
            n = i
            break
    return n * span
"""),
    ("the queue is ordered by a reversed sort", "pick.py",
     lambda: edit("pick.py", ("    return sorted(q, key=lambda r: r.idx)",
                              "    return sorted(q, key=lambda r: -r.idx, reverse=True)"))),
]


def swap(target, source):
    files = {}
    for name in play.POLICY:
        with open(os.path.join(play.SOL, name)) as fh:
            files[name] = fh.read()
    files[target] = source
    return files


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 300
    jobs = gen.batch("orderfuzz", count)
    ref = play.reference(os.path.join(WORK, "ref"))
    base = dict((name, play.safe(ref, text)) for name, text in jobs)
    bad = 0
    width = max(len(label) for label, _, _ in PERMUTED)
    for label, target, make in PERMUTED:
        tree = play.build(os.path.join(WORK, "perm"), swap(target, make()))
        off = [name for name, text in jobs if play.safe(tree, text) != base[name]]
        bad += len(off)
        print("  %-*s  %s" % (width, label,
                              "same" if not off else "DIFFERS on %d (%s)" % (len(off), off[0])))
    print("%d traces, %d disagreements" % (len(jobs), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
