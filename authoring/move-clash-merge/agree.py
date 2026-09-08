"""Do the two implementations agree, does the reference converge, and what is exercised?

Three questions in one pass over a generated population:

  agreement   the reference under tasks/<slug>/solution and the sealed model produce the
              same trace, line for line
  convergence after each round both sides equal the record - the property the whole task
              is about, and the one no printed line states directly
  coverage    how many scenarios reach each graded rule, so a rule that never fires in the
              generated space can be given a shaped family or a literal case

Scratch trees are made under tempfile, never inside the bundle.
"""
import collections
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "move-clash-merge"))
sys.path.insert(0, str(ROOT / "tasks" / "move-clash-merge" / "tests"))

import emit as E  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def shape(t):
    return dict((model.pth(t, k), (t[k][0], t[k][3])) for k in t if k != model.ROOT)


def checked(text, tally):
    """model.replay with the convergence invariant asserted after every round."""
    base, nxt, rounds = model.parse(text.split("\n"))
    rec = dict(base)
    lo, ro = dict(base), dict(base)
    made = [0]

    def fresh():
        made[0] += 1
        return "w%d" % made[0]

    faults = []
    for i, (lops, rops) in enumerate(rounds, 1):
        for op in lops:
            model.do(lo, op, False, fresh)
        for op in rops:
            model.do(ro, op, True, fresh)
        before = dict(rec)
        tgt, nxt, ml, mr = model.merge(rec, nxt, lo, ro)
        count(before, lo, ro, tgt, ml, mr, tally)
        for cur, m, fold in ((lo, ml, False), (ro, mr, True)):
            for op in model.emit(cur, tgt, m, fold):
                if op[0] == "mv" and "/~t" in op[2]:
                    tally["pushed aside"] += 1
                model.do(cur, op, fold, fresh)
        if shape(lo) != shape(tgt):
            faults.append("round %d: workstation did not reach the record" % i)
        if shape(ro) != shape(tgt):
            faults.append("round %d: server did not reach the record" % i)
        lo = model.rekey(lo, tgt, fresh)
        ro = model.rekey(ro, tgt, fresh)
        rec = tgt
    return faults


def count(rec, lo, ro, tgt, ml, mr, tally):
    raw = model.where(rec, lo, ro)
    alive = model.survive(rec, lo, ro, raw)
    place = model.settle(rec, alive, raw)
    for key in alive:
        if key in rec and (key not in lo or key not in ro):
            tally["revived"] += 1
    for key in place:
        if key in raw and raw[key][0] != place[key][0]:
            tally["walked up"] += 1
        if key.startswith("C:"):
            tally["second node"] += 1
    for key in place:
        if key in rec and key in lo and key in ro:
            lp = model.tag(rec, "L", lo[key][1])
            rp = model.tag(rec, "R", ro[key][1])
            if lp != rp and rec[key][1] not in (lp, rp):
                tally["both moved"] += 1
            if lo[key][2] != ro[key][2] and rec[key][2] not in (lo[key][2], ro[key][2]):
                tally["both renamed"] += 1
            if lo[key][1] != ro[key][1] and lo[key][2] != ro[key][2] \
                    and (lp == rec[key][1] or rp == rec[key][1]):
                tally["axes split"] += 1
    seen = collections.Counter()
    for key in place:
        seen[(place[key][0], place[key][1].lower())] += 1
    for spot, n in seen.items():
        if n > 1:
            tally["contest"] += 1
    for k in tgt:
        if k != model.ROOT and "~" in tgt[k][2]:
            tally["marked"] += 1


def main(argv):
    count_per = int(argv[1]) if len(argv) > 1 else 60
    ref, _ = E.runner(str(ROOT / "tasks" / "move-clash-merge" / "solution"))
    tally = collections.Counter()
    batch = gen.batch(argv[2] if len(argv) > 2 else "agree-v1", count_per)
    off, broken = [], []
    for name, text in batch:
        if ref(text) != model.replay(text):
            off.append(name)
        bad = checked(text, tally)
        if bad:
            broken.append((name, bad[0]))
    print("scenarios          %d" % len(batch))
    print("reference != model %d %s" % (len(off), off[:3]))
    print("did not converge   %d %s" % (len(broken), broken[:2]))
    for key in sorted(tally):
        print("  %-14s %d" % (key, tally[key]))
    return 1 if off or broken else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
