"""Write authoring/variants: alternative correct implementations, all of which must score 1.

This is the cheat suite's mirror image and it is the gate the run audit actually applies. A
graded quantity that two correct implementations disagree on is a trap rather than a test,
and the only way to know is to write the other implementations and run them through the
real verifier.

Six readings, chosen so that between them they vary every structural decision a solver
could plausibly make differently: push against pull, recursion against a worklist, sort
against a single minimum, an offer derived on the fly against one materialised, a
reachability walk by layers against one by relaxation, and one that keeps its own index
beside the store rather than re-deriving from it.

Regenerate with:  python authoring/make_variants.py
"""

import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REF = ROOT / "solution"
SHIP = ROOT / "environment" / "app_src" / "pol"
OUT = HERE / "variants"

# ------------------------------------------------------------------ shared pieces

REF_GRAFT = """from . import spread


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)
    spread.flow(st, nid)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)
    spread.flow(st, nid)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    spread.flow(st, nid)
"""

REF_SPREAD = """from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def flow(st, nid):
    if st.stops(nid):
        return
    st.rip(nid, lambda r: r.og != nid)
    up = st.up(nid)
    if up is not None:
        for r in st.held(up):
            if r.sc == 0 or r.og == nid:
                continue
            st.put(nid, R(r.sb, r.rt, r.vd, 1, r.og, r.bn))
    for k in st.kids(nid):
        flow(st, k)
"""

REF_WEIGH = """from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid)
          if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (nb[r.sb], 0 if r.og == nid else 1, -r.bn))
    return cs[0]
"""

# ------------------------------------------------------------------ the readings

PULL_SPREAD = """from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    settle(st, st.kids(nid))


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    settle(st, st.kids(nid))


def offer(st, nid):
    return [(r.sb, r.rt, r.vd, r.og, r.bn) for r in st.held(nid) if r.sc != 0]


def settle(st, seeds):
    work = list(seeds)
    while work:
        nid = work.pop(0)
        if st.stops(nid):
            continue
        keep = [r for r in st.held(nid) if r.og == nid]
        st.rip(nid, lambda r: True)
        for r in keep:
            st.put(nid, r)
        up = st.up(nid)
        if up is not None:
            for sb, rt, vd, og, bn in offer(st, up):
                if og != nid:
                    st.put(nid, R(sb, rt, vd, 1, og, bn))
        work.extend(st.kids(nid))


def flow(st, nid):
    settle(st, [nid])
"""

MIN_WEIGH = """from . import crowd


def rank(nb, nid, r):
    return (nb[r.sb], 0 if r.og == nid else 1, -r.bn)


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    best = None
    mark = None
    for r in st.held(nid):
        if r.rt != rt or r.sc == 2 or r.sb not in nb:
            continue
        here = rank(nb, nid, r)
        if mark is None or here < mark:
            mark, best = here, r
    return best
"""

CMP_WEIGH = """import functools

from . import crowd


def pick(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid) if r.rt == rt and r.sc != 2 and r.sb in nb]
    if not cs:
        return None

    def order(a, b):
        for left, right in ((nb[a.sb], nb[b.sb]),
                            (a.og != nid, b.og != nid),
                            (b.bn, a.bn)):
            if left != right:
                return -1 if left < right else 1
        return 0

    return sorted(cs, key=functools.cmp_to_key(order))[0]
"""

DFS_CROWD = """def near(st, sb):
    out = {sb: 0}
    stack = [(sb, 0)]
    while stack:
        who, d = stack.pop()
        for g in st.crews():
            if who not in st.mems(g):
                continue
            if g in out and out[g] <= d + 1:
                continue
            out[g] = d + 1
            stack.append((g, d + 1))
    return out
"""

INDEX_SPREAD = """from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def flow(st, nid):
    if st.stops(nid):
        return
    up = st.up(nid)
    book = {}
    if up is not None:
        for r in st.held(up):
            if r.sc == 0 or r.og == nid:
                continue
            book[(r.og, r.sb, r.rt)] = (r.vd, r.bn)
    st.rip(nid, lambda r: r.og != nid)
    for og, sb, rt in sorted(book):
        vd, bn = book[(og, sb, rt)]
        st.put(nid, R(sb, rt, vd, 1, og, bn))
    for k in st.kids(nid):
        flow(st, k)
"""

BFS_SPREAD = """from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def rung(st, nid):
    seen = [nid]
    at = 0
    while at < len(seen):
        who = seen[at]
        if not st.stops(who):
            seen.extend(st.kids(who))
        at += 1
    return seen


def flow(st, nid):
    for who in rung(st, nid):
        if st.stops(who):
            continue
        st.rip(who, lambda r: r.og != who)
        up = st.up(who)
        if up is None:
            continue
        for r in st.held(up):
            if r.sc == 0 or r.og == who:
                continue
            st.put(who, R(r.sb, r.rt, r.vd, 1, r.og, r.bn))
"""

VARIANTS = {
    "ok-pull": {"spread.py": PULL_SPREAD, "graft.py": REF_GRAFT, "weigh.py": REF_WEIGH},
    "ok-minimum": {"spread.py": REF_SPREAD, "graft.py": REF_GRAFT, "weigh.py": MIN_WEIGH},
    "ok-comparator": {"spread.py": REF_SPREAD, "graft.py": REF_GRAFT, "weigh.py": CMP_WEIGH},
    "ok-crowd-dfs": {"spread.py": REF_SPREAD, "graft.py": REF_GRAFT, "weigh.py": REF_WEIGH,
                     "crowd.py": DFS_CROWD},
    "ok-index": {"spread.py": INDEX_SPREAD, "graft.py": REF_GRAFT, "weigh.py": REF_WEIGH},
    "ok-layers": {"spread.py": BFS_SPREAD, "graft.py": REF_GRAFT, "weigh.py": REF_WEIGH},
}


def main():
    if OUT.is_dir():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in sorted(VARIANTS):
        box = OUT / name
        box.mkdir()
        for fname, body in VARIANTS[name].items():
            (box / fname).write_text(body, newline="\n")
        if "crowd.py" not in VARIANTS[name]:
            shutil.copyfile(SHIP / "crowd.py", box / "crowd.py")
    print("wrote %d variants into %s" % (len(VARIANTS), OUT))


if __name__ == "__main__":
    main()
