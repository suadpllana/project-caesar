"""The graded decisions as rows of features the shipped tree actually exposes.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features offered
are the raw ones a solver can read at that moment from the tree as it ships - a part's key and
index, whether that key is already held, how many parts and keys are in, how many names are
wanted, how many gives and uses a name has collected. Nothing that only the repaired engine
knows is offered, because knowing it is the task: the shipped store records who holds a key but
not whether that holder came off the input list, and it records the gives of a name but not the
order they arrived in.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
whether a part is kept, because it turns on where the current holder of its key came from, and
whether a part is in the image, because reachability is a property of the whole graph rather
than of the part.

    python3 authoring/bind-claim-prune/decisions.py
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lab  # noqa: E402

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402

APP = lab.tree("ref")
sys.path.insert(0, str(APP))

import ops  # noqa: E402
from bind import book, hold, prune, pull, want, wire  # noqa: E402

KEPT = []
TAKEN = []
LIVE = []
STANDS = []


def watch():
    """Record each decision as the reference makes it, with what was visible just before."""
    real_load = hold.load
    real_pick = pull.pick
    real_prune = prune.run

    def load(keep, u, direct):
        seen = []
        for p in u.parts:
            seen.append((p, {
                "has_key": int(p.key is not None),
                "key_held": int(p.key is not None and p.key in keep.who),
                "part_index": p.idx,
                "unit_parts": len(u.parts),
                "parts_in": min(len(keep.parts), 3),
                "keys_held": min(len(keep.who), 3),
                "direct": int(bool(direct)),
                "gives": min(len(p.gives), 3),
                "uses": min(len(p.uses), 3),
            }))
        ins, out = real_load(keep, u, direct)
        got = {(p.unit, p.idx) for p in ins}
        for p, row in seen:
            KEPT.append((row, int((p.unit, p.idx) in got)))
        return ins, out

    def pick(st, sc):
        pos = real_pick(st, sc)
        if pos is not None:
            free = [i for i in range(len(sc.mem)) if i not in sc.taken]
            gives = []
            for i in free:
                u = st.job.units.get(sc.mem[i])
                hit = 0
                if u is not None:
                    for p in u.parts:
                        for nm, strong in p.gives:
                            if strong and nm in st.names.want:
                                hit = 1
                if hit:
                    gives.append(i)
            TAKEN.append(({
                "wanted": min(len(st.names.want), 3),
                "free_members": min(len(free), 3),
                "first_free": free[0] if free else -1,
                "first_giving": gives[0] if gives else -1,
                "last_giving": gives[-1] if gives else -1,
                "taken_so_far": min(len(sc.taken), 3),
            }, pos))
        return pos

    def sweep(st):
        live, lit = real_prune(st)
        for spot, p in st.keep.parts.items():
            LIVE.append(({
                "strong_uses": min(sum(1 for _n, s in p.uses if s), 3),
                "weak_uses": min(sum(1 for _n, s in p.uses if not s), 3),
                "gives": min(len(p.gives), 3),
                "part_index": p.idx,
                "is_root_name": int(any(nm in st.job.roots for nm, _s in p.gives)),
                "is_held": int(spot in st.job.holds),
                "kept_parts": min(len(st.keep.parts), 3),
            }, int(spot in live)))
        for nm in list(st.names.firm) + list(st.names.soft):
            s_firm = len(st.names.firm.get(nm, ()))
            s_soft = len(st.names.soft.get(nm, ()))
            STANDS.append(({
                "firm_gives": min(s_firm, 3),
                "soft_gives": min(s_soft, 3),
                "strong_need": min(st.names.need.get(nm, 0), 3),
                "spared": min(len(st.names.spare.get(nm, ())), 3),
                "wanted": int(nm in st.names.want),
            }, 1 if s_firm else (2 if s_soft else 0)))
        return live, lit

    hold.load = load
    pull.pick = pick
    prune.run = sweep
    wire.hold = hold
    wire.prune = prune
    pull.pick = pick


def samples():
    watch()
    for fam, _name, lines in gen.programs("decisions", 8):
        if fam in ("wide", "deep"):
            continue
        job = book.Job()
        for line in lines:
            word = line.split()
            if word:
                ops.ex(job, tuple(word))
    return {"part_kept": KEPT, "member_taken": TAKEN, "part_in_image": LIVE,
            "name_stands_on": STANDS}


if __name__ == "__main__":
    got = samples()
    for k, v in sorted(got.items()):
        print("%-16s %6d rows, %d distinct labels" % (k, len(v), len({y for _, y in v})))
    shutil.rmtree(APP.parent, ignore_errors=True)
