"""Build one whole engine per wrong reading, from the reference, and assert every patch fired.

A reading is a complete service a solver could actually submit, not an ablation of a file no
agent would produce: it reads one rule the wrong way and is right about everything else. Each
patch is an exact string that must occur once in the reference, and a patch that matched
nothing would otherwise ship a copy of the reference and score itself as "caught by
everything", which is the quietest way for this whole measurement to be a lie.

    python authoring/bind-claim-prune/make_readings.py
"""
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE.parent.parent / "tasks" / "bind-claim-prune" / "solution"
OUT = HERE / "readings"
PARTS = ("hold.py", "want.py", "pull.py", "place.py", "prune.py", "wire.py")

PICK_OLDEST = '''
def pick(st, sc):
    for nm in sorted(st.names.want):
        row = sc.idx.get(nm)
        if not row:
            continue
        at = sc.cur.get(nm, 0)
        while at < len(row) and row[at] in sc.taken:
            at += 1
        sc.cur[nm] = at
        if at < len(row):
            return row[at]
    return None
'''

PICK_ONWARD = '''
def pick(st, sc):
    best = None
    floor = getattr(sc, "mark", 0)
    for nm in st.names.want:
        row = sc.idx.get(nm)
        if not row:
            continue
        at = sc.cur.get(nm, 0)
        while at < len(row) and (row[at] in sc.taken or row[at] < floor):
            at += 1
        sc.cur[nm] = at
        if at < len(row) and (best is None or row[at] < best):
            best = row[at]
    return best
'''

RUN_ONWARD = '''
def run(st, bundles):
    scans = [Scan(st.job, b) for b in bundles]
    for sc in scans:
        sc.mark = 0
    while True:
        moved = False
        for sc in scans:
            while True:
                pos = pick(st, sc)
                if pos is None:
                    break
                sc.taken.add(pos)
                sc.mark = pos + 1
                who = sc.mem[pos]
                if who in st.keep.loaded:
                    continue
                say.take(st.job, sc.name, who)
                st.load(who, False)
                moved = True
        if not moved:
            return
'''

WIRE_LIST = '''
def run(job, items):
    st = Link(job)
    job.link = st
    every = []
    for kind, what in items:
        if kind == "u":
            st.load(what, True)
        elif kind == "b":
            every.append(what)
            pull.run(st, (what,))
        else:
            every.extend(what)
            pull.run(st, what)
    if every:
        pull.run(st, tuple(every))
    st.set = place.run(st)
    st.live, st.lit = prune.run(st)
'''

WIRE_BACK = '''
def run(job, items):
    st = Link(job)
    job.link = st
    behind = []
    for kind, what in items:
        if kind == "u":
            before = len(st.keep.parts)
            st.load(what, True)
            if len(st.keep.parts) <= before:
                for old in behind:
                    pull.run(st, old)
        elif kind == "b":
            behind.append((what,))
            pull.run(st, (what,))
        else:
            behind.append(what)
            pull.run(st, what)
    st.set = place.run(st)
    st.live, st.lit = prune.run(st)
'''

READINGS = {
    "claim-sticks": [("hold.py", """    if direct:
        for p in u.parts:
            if p.key is None or p.key not in keep.who or p.key in keep.firm:
                continue
            out.append(keep.parts.pop(keep.who[p.key]))
            del keep.who[p.key]
""", """    if False:
        pass
""")],
    "claim-never": [("hold.py", """        if p.key is not None:
            if p.key in keep.who:
                continue
            keep.who[p.key] = (p.unit, p.idx)
""", """        if p.key is not None:
            if p.key not in keep.who:
                keep.who[p.key] = (p.unit, p.idx)
""")],
    "firm-never": [("hold.py",
                    "            if p.key is None or p.key not in keep.who or p.key in keep.firm:",
                    "            if p.key is None or p.key not in keep.who:")],
    "give-stays": [("want.py", """    for nm, strong in p.gives:
        row = names.firm.get(nm) if strong else names.soft.get(nm)
        if row:
            for i, q in enumerate(row):
                if q is p:
                    del row[i]
                    break
        touch(names, nm)
""", """    for nm, strong in p.gives:
        touch(names, nm)
""")],
    "use-stays": [("want.py", """    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) - 1
            touch(names, nm)
""", """    for nm, strong in p.uses:
        touch(names, nm)
""")],
    "one-give": [("want.py", """            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
            row.append(p)
""", """            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
            else:
                row.append(p)
""")],
    "dup-replaces": [("want.py", """            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
            row.append(p)
""", """            row = names.firm.setdefault(nm, [])
            if row:
                say.dup(job, nm, p.unit)
                del row[:]
            row.append(p)
""")],
    "weak-settles": [("want.py", """    if names.firm.get(nm):
        names.want.discard(nm)
""", """    if names.firm.get(nm) or names.soft.get(nm):
        names.want.discard(nm)
""")],
    "spare-quiet": [("want.py",
                     "    elif names.need.get(nm, 0) > 0 or nm in names.spare:",
                     "    elif names.need.get(nm, 0) > 0:")],
    "weak-wants": [("want.py", """    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) + 1
            touch(names, nm)
""", """    for nm, strong in p.uses:
        names.need[nm] = names.need.get(nm, 0) + 1
        touch(names, nm)
"""), ("want.py", """    for nm, strong in p.uses:
        if strong:
            names.need[nm] = names.need.get(nm, 0) - 1
            touch(names, nm)
""", """    for nm, strong in p.uses:
        names.need[nm] = names.need.get(nm, 0) - 1
        touch(names, nm)
""")],
    "take-oldest": [("pull.py", "@pick@", PICK_OLDEST)],
    "take-onward": [("pull.py", "@pick@", PICK_ONWARD), ("pull.py", "@run@", RUN_ONWARD)],
    "rescan-back": [("wire.py", "@run@", WIRE_BACK)],
    "list-as-group": [("wire.py", "@run@", WIRE_LIST)],
    "take-again": [("pull.py", """                who = sc.mem[pos]
                if who in st.keep.loaded:
                    continue
                say.take(st.job, sc.name, who)
""", """                who = sc.mem[pos]
                say.take(st.job, sc.name, who)
""")],
    "group-once": [("pull.py", """        if not moved:
            return
""", """        return
""")],
    "weak-reaches": [("prune.py", """        for nm, strong in p.uses:
            if strong:
                seed(st, nm, stack, live, lit)
""", """        for nm, strong in p.uses:
            seed(st, nm, stack, live, lit)
""")],
    "hold-quiet": [("prune.py", """    for spot in st.job.holds:
        if spot in st.keep.parts and spot not in live:
            live.add(spot)
            stack.append(st.keep.parts[spot])
""", """    for _spot in st.job.holds:
        pass
""")],
    "spare-first": [("place.py",
                     "            if best is None or size > best[0] or (size == best[0] and order < best[1]):",
                     "            if best is None:")],
    "spare-late": [("place.py",
                    "            if best is None or size > best[0] or (size == best[0] and order < best[1]):",
                    "            if best is None or size > best[0] or (size == best[0] and order > best[1]):")],
    "at-preprune": [("wire.py",
                     "        return spot if spot in st.live else None",
                     "        return spot")],
    "img-all-spares": [("prune.py", """    for nm in st.lit:
        total += st.set[nm][1]
    return len(st.live) + len(st.lit), total
""", """    for nm in st.set:
        total += st.set[nm][1]
    return len(st.live) + len(st.set), total
""")],
}


def swap(src, old, new, where, tag):
    """One exact replacement, or a loud failure. A patch that matched nothing ships the
    reference under a wrong reading's name and quietly reports that everything catches it."""
    if old.startswith("@") and old.endswith("@"):
        want = "\ndef %s(" % old.strip("@")
        at = src.find(want)
        if at < 0:
            raise SystemExit("%s: no def %s in %s" % (tag, old, where))
        end = src.find("\n\ndef ", at + 1)
        end = len(src) if end < 0 else end + 1
        return src[:at] + new.rstrip("\n") + "\n" + src[end:]
    n = src.count(old)
    if n != 1:
        raise SystemExit("%s: patch for %s matched %d times, wanted 1" % (tag, where, n))
    return src.replace(old, new)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for tag, patches in READINGS.items():
        room = OUT / tag
        room.mkdir(parents=True)
        for name in PARTS:
            shutil.copy(REF / name, room / name)
        for where, old, new in patches:
            path = room / where
            path.write_text(swap(path.read_text(encoding="utf-8"), old, new, where, tag),
                            encoding="utf-8", newline="\n")
        for name in PARTS:
            same = (room / name).read_text(encoding="utf-8") == \
                (REF / name).read_text(encoding="utf-8")
            if not same:
                break
        else:
            raise SystemExit("%s: every file is still the reference" % tag)
    print("built %d readings under %s" % (len(READINGS), OUT))


if __name__ == "__main__":
    main()
