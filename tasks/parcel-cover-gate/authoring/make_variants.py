"""Generate authoring/variants/ from the reference plus one declared change each.

A variant is the reference with one decision made differently and correctly. Kept
by hand, the copies drift the moment the reference changes, and the symptom is
every correct reading disagreeing at once, which reads like a broken reference
and is not. So they are generated, and the generator is the only place a variant
is written down.

Each variant exists to answer one run-audit question: does the verifier grade the
behaviour or the way the reference happens to be written? A variant that scores
anything but 1 is either a real disagreement about the rules - in which case some
sentence of the brief was never decided - or a bug in the variant. Ask which
sentence separates it before touching the variant.
"""

import pathlib
import sys

import lab

OUT = lab.ROOT / "authoring" / "variants"

WHY = {
    "ok-earliest-scan":
        "The pass finds the earliest ready parcel by scanning the bag for an\n"
        "index and then starts over, where the reference walks the bag and breaks\n"
        "out of the walk. Same rule, said with a different loop. It is here\n"
        "because the reverse of it is not a variant at all: which of two ready\n"
        "parcels goes up decides what the worker can ever show, and walking the\n"
        "bag newest first ships as a cheat.",
    "ok-reach-set":
        "Standing-after is answered out of a memoised reachable set per version\n"
        "rather than by walking the graph for each question. Same relation, a\n"
        "different data structure, and the graded rows must not notice.",
    "ok-cover-first":
        "Coverage looks at what the parcel carries before it looks at what the\n"
        "worker shows, where the reference asks in the other order. Either answer\n"
        "is the same answer, and a graded row that noticed would be grading the\n"
        "shape of an if.",
    "ok-fold-apply":
        "The gate works out everything a parcel moves before it moves any of it,\n"
        "rather than writing into the shown map as it goes. A parcel goes up\n"
        "whole, so the two cannot come apart.",
    "ok-number-apply":
        "Applying an entry is decided by which version number is higher, where\n"
        "the reference asks whether the entry stands after what the worker shows.\n"
        "The two cannot come apart: a parcel only reaches this point once nothing\n"
        "in it is off to one side, and of two versions of one setting on one line\n"
        "of descent the later one is the one with the higher number. It ships as a\n"
        "variant because it was written as a cheat and scored 1, which is the\n"
        "playbook working: a cheat that passes is a correct implementation or a\n"
        "hole in the case set, and this one is provably the first.",
    "ok-worklist":
        "The pass is a worklist that stops when a full round adds nothing, rather\n"
        "than a loop with a flag. The same standstill, reached by a different\n"
        "route.",
}


def _sub(text, old, new, tag):
    if old not in text:
        raise SystemExit("anchor missing for %s" % tag)
    return text.replace(old, new, 1)


def build():
    ref = lab.reference()
    out = {}

    out["ok-earliest-scan"] = {"gate.py": """from base import tape, wire

from bay import desc, stand


def given(st, w, no):
    wire.held(st, w).append(no)


def gate(st, w):
    view = tape.seat(st, w)
    bag = wire.held(st, w)
    got = set()
    while True:
        pick = -1
        for at in range(len(bag)):
            if stand.ripe(st, st.parc[bag[at] - 1], view):
                pick = at
                break
        if pick < 0:
            return got
        p = st.parc[bag.pop(pick) - 1]
        for s in p:
            v = p[s]
            cur = view.get(s, -1)
            if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                view[s] = v
                got.add(s)
"""}

    out["ok-reach-set"] = {"desc.py": '''REACH = {}


def _over(st, i):
    got = REACH.get((id(st), i))
    if got is None:
        got = set([i])
        for j in st.vers[i].base:
            got |= _over(st, j)
        REACH[(id(st), i)] = got
    return got


def runs(st, a, b):
    return b in _over(st, a)
'''}

    out["ok-cover-first"] = {"cov.py": _sub(
        ref["cov.py"],
        """        if s in view and desc.runs(st, view[s], v):
            continue
        if s in ent and desc.runs(st, ent[s], v):
            continue""",
        """        if s in ent and desc.runs(st, ent[s], v):
            continue
        if s in view and desc.runs(st, view[s], v):
            continue""", "ok-cover-first")}

    out["ok-fold-apply"] = {"gate.py": _sub(
        ref["gate.py"],
        """            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                    view[s] = v
                    got.add(s)""",
        """            step = {}
            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                    step[s] = v
            view.update(step)
            got.update(step)""", "ok-fold-apply")}

    out["ok-number-apply"] = {"gate.py": _sub(
        ref["gate.py"],
        "                if cur != v and (cur == -1 or desc.runs(st, v, cur)):",
        "                if cur < v:", "ok-number-apply")}

    out["ok-worklist"] = {"gate.py": _sub(
        ref["gate.py"],
        """    got = set()
    moving = True
    while moving:
        moving = False
        for no in list(bag):
            p = st.parc[no - 1]
            if not stand.ripe(st, p, view):
                continue
            bag.remove(no)
            for s in p:
                v = p[s]
                cur = view.get(s, -1)
                if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                    view[s] = v
                    got.add(s)
            moving = True
            break
    return got""",
        """    got = set()
    queue = list(bag)
    while queue:
        no = queue.pop(0)
        p = st.parc[no - 1]
        if not stand.ripe(st, p, view):
            continue
        bag.remove(no)
        for s in p:
            v = p[s]
            cur = view.get(s, -1)
            if cur != v and (cur == -1 or desc.runs(st, v, cur)):
                view[s] = v
                got.add(s)
        queue = list(bag)
    return got""", "ok-worklist")}

    return out


def main():
    ref = lab.reference()
    made = build()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in sorted(made):
        where = OUT / name
        where.mkdir(exist_ok=True)
        for fn in lab.OPEN:
            body = made[name].get(fn, ref[fn])
            with open(where / fn, "w", newline="\n") as fh:
                fh.write(body)
        with open(where / "README", "w", newline="\n") as fh:
            fh.write(WHY[name].rstrip() + "\n")
        print("%-16s %s" % (name, ", ".join(sorted(made[name]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
