"""Build one whole service per wrong reading, by patching the reference.

Each reading is a service an agent could actually produce: the reference with one decision
read the other way. Ablating a module the agent never writes would measure nothing, so every
variant here is a complete, runnable six-file tree.

Every substitution asserts that it fired. A patch that silently matches nothing ships the
reference under another name and scores 1 for the wrong reason.
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOL = ROOT / "tasks" / "claim-line-stall" / "solution"
OUT = HERE / "readings"
PARTS = ("book.py", "line.py", "lift.py", "knot.py", "turn.py", "act.py")

# name -> (file, old, new); "name#2" adds a second patch to the same reading
READINGS = {

    "no-ahead": ("line.py", """def grantable(h, req):
    if book.anyclash(h, req[1], req[2], req[3]):
        return False
    return not ahead(h, req)""", """def grantable(h, req):
    return not book.anyclash(h, req[1], req[2], req[3])"""),

    "stamp-rank": ("line.py", """def rankof(h, req):
    return (0 if book.holds_over(h, req[1], req[2]) else 1, req[0])""",
                   """def rankof(h, req):
    if len(req) < 5:
        req.append(0 if book.holds_over(h, req[1], req[2]) else 1)
    return (req[4], req[0])"""),

    "stamp-rank#2": ("line.py", """def give(h, req):
    fid, job, scope, mode = req""", """def give(h, req):
    fid, job, scope, mode = req[0], req[1], req[2], req[3]"""),

    "hold-only": ("knot.py", """    out = book.whoclash(h, job, req[2], req[3])
    mine = line.rankof(h, req)""", """    out = book.whoclash(h, job, req[2], req[3])
    return out
    mine = line.rankof(h, req)"""),

    "ahead-all": ("knot.py", """        if not book.overlap(req[2], other[2]) or not book.clash(req[3], other[3]):
            continue
        if line.rankof(h, other) < mine:""", """        if line.rankof(h, other) < mine:"""),

    "pick-young": ("knot.py", """def pick(h, jobs):
    return min(jobs, key=lambda j: (len(h.held.get(j) or ()), -h.born[j]))""",
                   """def pick(h, jobs):
    return max(jobs, key=lambda j: h.born[j])"""),

    "pick-most": ("knot.py", """def pick(h, jobs):
    return min(jobs, key=lambda j: (len(h.held.get(j) or ()), -h.born[j]))""",
                  """def pick(h, jobs):
    return max(jobs, key=lambda j: (len(h.held.get(j) or ()), -h.born[j]))"""),

    "pick-old": ("knot.py", """def pick(h, jobs):
    return min(jobs, key=lambda j: (len(h.held.get(j) or ()), -h.born[j]))""",
                 """def pick(h, jobs):
    return min(jobs, key=lambda j: (len(h.held.get(j) or ()), h.born[j]))"""),

    "raise-free": ("lift.py", """    if h.own.get(u, {}).get(job) == "w":
        out = "w"
    return u, book.strongest(out)""", """    if h.own.get(u, {}).get(job) == "w":
        out = "w"
    for one in [s for s in (h.held.get(job) or ()) if name.cut(s) == (u, name.cut(s)[1])
                and name.cut(s)[1] is not None]:
        book.lose(h, job, one)
    return u, book.strongest(out)"""),

    "raise-any": ("lift.py", """    pair = h.tally.get(u, {}).get(job)
    if not pair or pair[0] + pair[1] < 4:
        return scope, mode""", """    wide = 0
    for one in h.held.get(job) or ():
        if name.cut(one)[1] is not None:
            wide += 1
    pair = h.tally.get(u, {}).get(job)
    if wide < 4:
        return scope, mode
    if not pair:
        pair = [0, 0]"""),

    "raise-asked": ("lift.py", """    out = mode
    if pair[1]:
        out = "w"
    if h.own.get(u, {}).get(job) == "w":
        out = "w"
    return u, book.strongest(out)""", """    return u, mode"""),

    "raise-five": ("lift.py", """    if not pair or pair[0] + pair[1] < 4:""",
                   """    if not pair or pair[0] + pair[1] < 5:"""),

    "no-swallow": ("line.py", """    for s in list(h.held.get(job) or ()):
        if s != scope and book.covers(scope, s):
            book.lose(h, job, s)
    book.put(h, job, scope, mode)""", """    book.put(h, job, scope, mode)"""),

    "cover-mode": ("book.py", """def covered(h, job, scope, mode):
    u, c = name.cut(scope)
    have = h.own.get(u, {}).get(job)
    if have is not None and atleast(have, mode):
        return True
    if c is None:
        return False
    have = h.cell.get(u, {}).get(scope, {}).get(job)
    return have is not None and atleast(have, mode)""",
                   """def covered(h, job, scope, mode):
    u, c = name.cut(scope)
    if h.own.get(u, {}).get(job) is not None:
        return True
    if c is None:
        return False
    return h.cell.get(u, {}).get(scope, {}).get(job) is not None"""),

    "cover-unit": ("book.py", """    if c is None:
        return False
    have = h.cell.get(u, {}).get(scope, {}).get(job)
    return have is not None and atleast(have, mode)""", """    return False"""),

    "keep-born": ("book.py", """def rest(h, job):
    if not h.held.get(job) and job not in h.ask:
        h.held.pop(job, None)
        h.born.pop(job, None)
        h.bh.discard(job)""", """def rest(h, job):
    if not h.held.get(job) and job not in h.ask:
        h.held.pop(job, None)
        h.bh.discard(job)"""),

    "born-grant": ("line.py", """def file_(h, req):
    h.line[req[0]] = req""", """def file_(h, req):
    if not h.held.get(req[1]):
        h.born.pop(req[1], None)
        h.nborn -= 1
    h.line[req[0]] = req"""),

    "end-keeps": ("act.py", """def over(h, job):
    n, where, had = book.clear(h, job)""", """def over(h, job):
    req = h.ask.get(job)
    n, where, had = book.clear(h, job)
    if req is not None:
        h.line[req[0]] = req
        h.ask[job] = req
        h.byunit.setdefault(name.cut(req[2])[0], {})[req[0]] = req
        had = False"""),

    "late-knot": ("turn.py", """def after(h, units):
    if units:
        line.settle(h, units)""", """def after(h, units):
    if not units:
        return
    line.settle(h, units)"""),

    "busy-ok": ("act.py", """def take(h, job, scope, mode):
    if job in h.ask:
        return""", """def take(h, job, scope, mode):
    if job in h.ask:
        book.unfile(h, h.ask[job])"""),

    "drop-covers": ("act.py", """def drop(h, job, scope):
    gone = book.lose(h, job, scope)""", """def drop(h, job, scope):
    gone = book.lose(h, job, scope)
    for one in list(h.held.get(job) or ()):
        if book.covers(scope, one):
            gone = book.lose(h, job, one) or gone"""),

    "settle-any": ("line.py", """    for fid in sorted(seen, key=lambda f: rankof(h, seen[f])):""",
                   """    for fid in sorted(seen):"""),

    "settle-hold": ("line.py", """def ahead(h, req):
    \"\"\"Does an ask of another job standing ahead of this one conflict with it?\"\"\"
    mine = rankof(h, req)""", """def ahead(h, req):
    \"\"\"Does an ask of another job standing ahead of this one conflict with it?\"\"\"
    mine = rankof(h, req)
    box = h.byunit.get(name.cut(req[2])[0])
    if box:
        for fid, other in box.items():
            if fid != req[0] and other[1] != req[1] and book.overlap(req[2], other[2]) \\
                    and rankof(h, other) < mine:
                return True"""),
}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    base = {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}
    jobs = {}
    for key, patch in READINGS.items():
        jobs.setdefault(key.split("#")[0], []).append(patch)
    for name, patches in sorted(jobs.items()):
        room = OUT / name
        room.mkdir()
        text = dict(base)
        for where, old, new in patches:
            if text[where].count(old) != 1:
                sys.exit("reading %s: pattern hits %d times in %s"
                         % (name, text[where].count(old), where))
            after = text[where].replace(old, new)
            if after == text[where]:
                sys.exit("reading %s changed nothing" % name)
            text[where] = after
        for p in PARTS:
            (room / p).write_text(text[p], encoding="utf-8", newline="\n")
    print("built %d readings in %s" % (len(jobs), OUT))


if __name__ == "__main__":
    main()
