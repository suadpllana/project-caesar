"""Derive every wrong reading from the reference, mechanically.

A reading is the reference with one decision taken the other way. Writing them as edits rather
than as copies keeps them in step with the reference: every replacement asserts that it fired,
so a reading can never quietly become a byte-for-byte copy of the thing it is supposed to
differ from - which is how a mirror once shipped as the reference and scored 1 for the wrong
reason.

    python3 authoring/publish-settle-order/make_readings.py
"""
import pathlib
import shutil
import sys

import lab

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "readings"
REF = lab.TASK / "solution"

# name -> {file: [(old, new), ...]} or {file: WHOLE_TEXT}
EDITS = {}


def edit(name, part, *pairs):
    EDITS.setdefault(name, {})[part] = list(pairs)


def whole(name, part, text):
    EDITS.setdefault(name, {})[part] = text


# --- the activation walk --------------------------------------------------------------
whole("boots-after-closure", "walk.py", '''from link import pick, site
from reg import hold, order, say, tab


def bring(h, name, out):
    r = tab.get(h, name)
    if not r.live:
        fresh = []
        _up(h, r, set(), fresh, out)
        for x in fresh:
            for sym in x.boots:
                site.reach(h, x, sym, out)
    hold.take(h, name)


def _up(h, r, busy, fresh, out):
    busy.add(r.name)
    for other, _kind in r.needs:
        dr = tab.get(h, other)
        if dr.live or dr.name in busy:
            continue
        _up(h, dr, busy, fresh, out)
    r.live = True
    r.uses = {}
    r.mark = object()
    order.add(h, r)
    pick.joined(h, r)
    fresh.append(r)
    say.up(out, r.name)
    busy.discard(r.name)
''')

edit("boot-before-publish", "walk.py",
     ("""    order.add(h, r)
    pick.joined(h, r)
    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)""",
      """    for sym in r.boots:
        site.reach(h, r, sym, out)
    order.add(h, r)
    pick.joined(h, r)
    say.up(out, r.name)"""))

edit("uses-survive", "walk.py", ("    r.uses = {}\n", ""))

edit("reup-moves", "walk.py",
     ("""    r = tab.get(h, name)
    if not r.live:
        _up(h, r, set(), out)
    hold.take(h, name)""",
      """    r = tab.get(h, name)
    if r.live:
        order.drop(h, r)
        pick.parted(h, r)
        order.add(h, r)
        pick.joined(h, r)
    else:
        _up(h, r, set(), out)
    hold.take(h, name)"""))

edit("reup-no-hold", "walk.py",
     ("""    if not r.live:
        _up(h, r, set(), out)
    hold.take(h, name)""",
      """    if r.live:
        return
    _up(h, r, set(), out)
    hold.take(h, name)"""))

edit("needs-sorted", "walk.py",
     ("    for other, _kind in r.needs:", "    for other, _kind in sorted(r.needs):"))

edit("pre-skipped", "walk.py",
     ("""    for other, _kind in r.needs:
        dr = tab.get(h, other)""",
      """    for other, kind in r.needs:
        if not kind:
            continue
        dr = tab.get(h, other)"""))

edit("pre-after-deps", "walk.py",
     ("""    for other, _kind in r.needs:
        dr = tab.get(h, other)""",
      """    for other, _kind in sorted(r.needs, key=lambda e: not e[1]):
        dr = tab.get(h, other)"""))

# --- which unit answers a name ---------------------------------------------------------
edit("strong-over-fallback", "pick.py",
     ("""def joined(h, r):
    i = _idx(h)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        i.setdefault(sym, []).append(r)""",
      """def joined(h, r):
    i = _idx(h)
    for sym, fall in r.pubs:
        i.setdefault(sym, []).append((r, fall))"""),
     ("""    for sym in dict.fromkeys(p[0] for p in r.pubs):
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break""",
      """    for sym, _fall in r.pubs:
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x[0] is r:
                del lst[n]
                break"""),
     ("""    lst = _idx(h).get(sym)
    return lst[0] if lst else None""",
      """    lst = _idx(h).get(sym)
    if not lst:
        return None
    for r, fall in lst:
        if not fall:
            return r
    return lst[0][0]"""))

edit("fallback-always", "pick.py",
     ("""def joined(h, r):
    i = _idx(h)
    for sym in dict.fromkeys(p[0] for p in r.pubs):
        i.setdefault(sym, []).append(r)""",
      """def joined(h, r):
    i = _idx(h)
    for sym, fall in r.pubs:
        i.setdefault(sym, []).append((r, fall))"""),
     ("""    for sym in dict.fromkeys(p[0] for p in r.pubs):
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break""",
      """    for sym, _fall in r.pubs:
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x[0] is r:
                del lst[n]
                break"""),
     ("""    lst = _idx(h).get(sym)
    return lst[0] if lst else None""",
      """    lst = _idx(h).get(sym)
    if not lst:
        return None
    for r, fall in lst:
        if fall:
            return r
    return lst[0][0]"""))

edit("newest-publisher", "pick.py",
     ("    return lst[0] if lst else None", "    return lst[-1] if lst else None"))

whole("scan-the-order", "pick.py", '''from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def find(h, sym):
    for r in order.live(h):
        for s, _fall in r.pubs:
            if s == sym:
                return r
    return None
''')

whole("scan-cached", "pick.py", '''from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def find(h, sym):
    for r in order.live(h):
        got = getattr(r, "symset", None)
        if got is None:
            got = {p[0] for p in r.pubs}
            r.symset = got
        if sym in got:
            return r
    return None
''')

# --- what a call does ------------------------------------------------------------------
edit("same-name-same-unit", "site.py",
     ("""        r.uses[sym] = (t, t.mark)
        say.ran(out, r.name, sym, t.name)
        return
    t, mark = u
    if t.live and t.mark is mark:""",
      """        r.uses[sym] = (t, None)
        say.ran(out, r.name, sym, t.name)
        return
    t, _mark = u
    if t.live:"""))

edit("settle-the-miss", "site.py",
     ("""    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return""",
      """    u = r.uses.get(sym)
    if sym in r.uses and u is None:
        say.miss(out, r.name, sym)
        return
    if u is None:
        t = pick.find(h, sym)
        if t is None:
            r.uses[sym] = None
            say.miss(out, r.name, sym)
            return"""))

whole("resolve-each-call", "site.py", '''from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    t = pick.find(h, sym)
    if t is None:
        say.miss(out, r.name, sym)
        return
    say.ran(out, r.name, sym, t.name)
''')

whole("dead-rebinds", "site.py", '''from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    u = r.uses.get(sym)
    if u is not None:
        t, mark = u
        if t.live and t.mark is mark:
            say.ran(out, r.name, sym, t.name)
            return
        del r.uses[sym]
    t = pick.find(h, sym)
    if t is None:
        say.dead(out, r.name, sym)
        return
    r.uses[sym] = (t, t.mark)
    say.ran(out, r.name, sym, t.name)
''')

edit("call-when-down", "site.py",
     ("""    if not r.live:
        return
    u = r.uses.get(sym)""",
      """    u = r.uses.get(sym)"""))

# --- what has to stay up ----------------------------------------------------------------
edit("soft-keeps", "want.py",
     ("""        for other, kind in o.needs:
            if kind and other == r.name:""",
      """        for other, _kind in o.needs:
            if other == r.name:"""))

edit("deps-need-not-live", "want.py",
     ("    for o in order.live(h):", "    for o in h.units.values():"))

whole("holds-only", "want.py", '''from reg import hold


def wanted(h, r):
    return hold.held(h, r.name) > 0
''')

# --- the sweep ---------------------------------------------------------------------------
edit("sweep-forward", "drop.py",
     ("""        for r in order.live(h):
            if not want.wanted(h, r):
                go = r
        if go is None:""",
      """        for r in order.live(h):
            if not want.wanted(h, r):
                go = r
                break
        if go is None:"""))

edit("sweep-once", "drop.py",
     ("""def _sweep(h, out):
    while True:
        go = None
        for r in order.live(h):
            if not want.wanted(h, r):
                go = r
        if go is None:
            return
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)""",
      """def _sweep(h, out):
    gone = [r for r in order.live(h) if not want.wanted(h, r)]
    for go in reversed(gone):
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)"""))

edit("rel-any-unit", "drop.py",
     ("""    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)""",
      """    tab.get(h, name)
    hold.give(h, name)"""))

# --- correct, and too slow ----------------------------------------------------------------
whole("rebuild-each-change", "pick.py", '''from reg import order


def rebuild(h):
    idx = {}
    for r in order.live(h):
        for sym, _fall in r.pubs:
            if sym not in idx:
                idx[sym] = r
    h.idx = idx


def joined(h, r):
    rebuild(h)


def parted(h, r):
    rebuild(h)


def find(h, sym):
    return getattr(h, "idx", {}).get(sym)
''')


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name, parts in sorted(EDITS.items()):
        room = OUT / name
        room.mkdir()
        for part, spec in parts.items():
            base = (REF / part).read_text()
            if isinstance(spec, str):
                text = spec
            else:
                text = base
                for old, new in spec:
                    if text.count(old) != 1:
                        raise SystemExit("%s/%s: %d matches for %r"
                                         % (name, part, text.count(old), old[:60]))
                    text = text.replace(old, new)
            if text == base:
                raise SystemExit("%s/%s is identical to the reference" % (name, part))
            (room / part).write_text(text)
        print("%-22s %s" % (name, ", ".join(sorted(parts))))
    print("%d readings" % len(EDITS))


if __name__ == "__main__":
    sys.exit(build())
