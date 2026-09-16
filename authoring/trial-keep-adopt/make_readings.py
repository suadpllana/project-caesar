"""Every plausible wrong reading of the brief, built as a working service.

Each one is the reference with one decision taken the other way, so it is a service a competent
solver could have written and not a broken file. A rename or a patch that does not fire is the
defect this script exists to avoid, so every edit asserts that its anchor was found exactly once
(CLAUDE.md, reach-pair-sweep).

Two of them - `pre-copy` and `no-memo` - produce exactly the reference's trace on everything they
finish. They are the resource readings, and only the stated limit separates them.
"""
import pathlib
import shutil
import sys

import lab

OUT = pathlib.Path(__file__).resolve().parent / "readings"
PARTS = ("keep.py", "look.py", "make.py", "need.py", "feed.py", "hold.py")

EDITS = {
    "check-all": [("look.py", """    for dep, was in rec[1]:
        if want(f, dep, seen) != was:
            return False
    return True""", """    ok = True
    for dep, was in rec[1]:
        if want(f, dep, seen) != was:
            ok = False
    return ok""")],

    "args-record": [("make.py", """    say.ran(f, name)
    keep.put(f, name, (v, tuple(reads)))
    return v""", """    say.ran(f, name)
    shown = []
    for i, one in enumerate(a):
        if kind == "cap" and i == 1:
            continue
        shown.append((one, want(f, one, seen)))
    keep.put(f, name, (v, tuple(shown)))
    return v""")],

    "merge-reads": [("make.py", """    keep.put(f, name, (v, tuple(reads)))""", """    old = keep.get(f, name)
    if old is not None:
        for pair in old[1]:
            if pair[0] not in [r[0] for r in reads]:
                reads.append((pair[0], want(f, pair[0], seen)))
    keep.put(f, name, (v, tuple(reads)))""")],

    "both-arms": [("make.py", """    elif kind == "pick":
        v = rd(a[1]) if rd(a[0]) else rd(a[2])
    else:
        v = rd(a[1]) if rd(a[0]) else 0""", """    elif kind == "pick":
        one = rd(a[1])
        two = rd(a[2])
        v = one if rd(a[0]) else two
    else:
        arm = rd(a[1])
        v = arm if rd(a[0]) else 0""")],

    "run-first": [("make.py", """    kind = f.kind[name]
    a = f.args[name]
    reads = []""", """    kind = f.kind[name]
    a = f.args[name]
    say.ran(f, name)
    reads = []"""),
                  ("make.py", """    say.ran(f, name)
    keep.put""", """    keep.put""")],

    "reads-set": [("make.py", """    keep.put(f, name, (v, tuple(reads)))""",
                   """    keep.put(f, name, (v, tuple(dict.fromkeys(reads))))""")],

    "pre-drop": [("hold.py", """def off(f):
    f.pre.live = False""", """def off(f):
    f.pre = None""")],

    "pre-write": [("keep.py", """def put(f, name, rec):
    pre = f.pre
    if pre is not None and pre.live:
        pre.res[name] = rec
    else:
        f.keep[name] = rec""", """def put(f, name, rec):
    f.keep[name] = rec""")],

    "pre-fresh": [("need.py", """        rec = keep.get(f, name)""",
                   """        pre = f.pre
        rec = None if (pre is not None and pre.live) else keep.get(f, name)""")],

    "layer-last": [("keep.py", """def get(f, name):
    pre = f.pre
    if pre is not None and pre.live:
        rec = pre.res.get(name)
        if rec is not None:
            return rec
    return f.keep.get(name)""", """def get(f, name):
    rec = f.keep.get(name)
    if rec is not None:
        return rec
    pre = f.pre
    if pre is not None and pre.live:
        return pre.res.get(name)
    return None""")],

    "adopt-any": [("feed.py", """        if lay.val == v:
            keep.take(f, lay)
        f.pre = None""", """        keep.take(f, lay)
        f.pre = None""")],

    "adopt-blind": [("feed.py", """            keep.take(f, lay)""", """            for one in lay.res:
                lay.res[one] = (lay.res[one][0], ())
            keep.take(f, lay)""")],

    "same-set": [("feed.py", """    if f.pub[name] == v:
        return
    f.pub[name] = v""", """    f.pub[name] = v""")],

    "other-drop": [("feed.py", """    lay = f.pre
    if lay is not None and not lay.live and lay.src == name:
        if lay.val == v:
            keep.take(f, lay)
        f.pre = None""", """    lay = f.pre
    if lay is not None and not lay.live:
        if lay.src == name and lay.val == v:
            keep.take(f, lay)
        f.pre = None""")],

    "pin-check": [("need.py", """    elif keep.pinned(f, name):
        v = keep.held(f, name)
    else:
        rec = keep.get(f, name)
        if rec is not None and look.stands(f, rec, want, seen):
            v = rec[0]
        else:
            v = make.body(f, name, want, seen)""", """    else:
        rec = keep.get(f, name)
        if rec is not None and look.stands(f, rec, want, seen):
            v = keep.held(f, name) if keep.pinned(f, name) else rec[0]
        else:
            v = make.body(f, name, want, seen)""")],

    "pin-kept": [("need.py", """def pin(f, name):
    keep.hold(f, name, get(f, name))""", """def pin(f, name):
    rec = keep.get(f, name)
    keep.hold(f, name, 0 if rec is None else rec[0])""")],

    "no-memo": [("need.py", """def want(f, name, seen):
    if name in seen:
        return seen[name]""", """def want(f, name, seen):
    if False:
        return seen[name]""")],
}


def reach(_):
    """`pre-reach`: inside a block, anything that can reach the previewed source is evaluated."""
    return [("need.py", """        rec = keep.get(f, name)
        if rec is not None and look.stands(f, rec, want, seen):""", """        rec = keep.get(f, name)
        if rec is not None and not tainted(f, name) and look.stands(f, rec, want, seen):"""),
            ("need.py", """def over(f, name):""", """def tainted(f, name):
    pre = f.pre
    if pre is None or not pre.live:
        return False
    fringe = [name]
    seen = set()
    while fringe:
        one = fringe.pop()
        if one == pre.src:
            return True
        if one in seen:
            continue
        seen.add(one)
        if f.kind[one] != "raw":
            fringe.extend(x for x in f.args[one] if x in f.kind)
    return False


def over(f, name):""")]


def copyback(_):
    """`pre-copy`: the block saves the kept results and puts them back - correct, and O(all)."""
    return [("hold.py", """def on(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    lay = keep.Lay(name, v)
    lay.live = True
    f.pre = lay


def off(f):
    f.pre.live = False""", """def on(f, name, v):
    if not defs.src(f, name):
        raise ValueError("not a source: %s" % name)
    lay = keep.Lay(name, v)
    lay.live = True
    lay.was = dict(f.keep)
    f.pre = lay


def off(f):
    lay = f.pre
    lay.live = False
    for one, rec in f.keep.items():
        if lay.was.get(one) is not rec:
            lay.res[one] = rec
    f.keep = lay.was"""),
            ("keep.py", """def put(f, name, rec):
    pre = f.pre
    if pre is not None and pre.live:
        pre.res[name] = rec
    else:
        f.keep[name] = rec""", """def put(f, name, rec):
    f.keep[name] = rec"""),
            ("keep.py", """def get(f, name):
    pre = f.pre
    if pre is not None and pre.live:
        rec = pre.res.get(name)
        if rec is not None:
            return rec
    return f.keep.get(name)""", """def get(f, name):
    return f.keep.get(name)""")]


EDITS["pre-reach"] = reach(None)
EDITS["pre-copy"] = copyback(None)


def build(name, edits):
    room = OUT / name
    if room.exists():
        shutil.rmtree(room)
    room.mkdir(parents=True)
    for part in PARTS:
        shutil.copy(lab.TASK / "solution" / part, room / part)
    for part, old, new in edits:
        path = room / part
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise SystemExit("%s: anchor in %s matched %d times, not 1"
                             % (name, part, text.count(old)))
        path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


def main():
    OUT.mkdir(exist_ok=True)
    for name in sorted(EDITS):
        build(name, EDITS[name])
    print("built %d readings: %s" % (len(EDITS), " ".join(sorted(EDITS))))


if __name__ == "__main__":
    main()
