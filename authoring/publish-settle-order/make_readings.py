"""Derive every wrong reading from the reference, mechanically.

A reading is the reference with one decision taken the other way: the shape a plausible wrong
plan produces. Writing them as edits rather than as copies keeps them in step with the
reference, and every replacement asserts that it fired, so a reading can never quietly become a
byte-for-byte copy of the thing it is supposed to differ from.

Three of them are semantically identical to the reference on purpose. Those are the ones the
execution limit separates: a resolution that scans the order, a resolution that keeps one list
per name and filters it by visibility, and a teardown that rescans the live set for candidates.

    python3 authoring/publish-settle-order/make_readings.py
"""
import pathlib
import shutil
import sys

import lab

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "readings"
REF = lab.TASK / "solution"

EDITS = {}


def edit(name, part, *pairs):
    EDITS.setdefault(name, {})[part] = list(pairs)


def whole(name, part, text):
    EDITS.setdefault(name, {})[part] = text


# --- the activation walk ----------------------------------------------------------------
edit("boots-after-closure", "walk.py",
     ("""    else:
        _up(h, r, None if wide else view.fresh(h), set(), out)
    hold.take(h, name)""",
      """    else:
        fresh = []
        _up(h, r, None if wide else view.fresh(h), set(), fresh, out)
        for x in fresh:
            for sym in x.boots:
                site.reach(h, x, sym, out)
    hold.take(h, name)"""),
     ("""def _up(h, r, den, busy, out):""", """def _up(h, r, den, busy, fresh, out):"""),
     ("""        _up(h, dr, den, busy, out)""", """        _up(h, dr, den, busy, fresh, out)"""),
     ("""    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)
    busy.discard(r.name)""",
      """    say.up(out, r.name)
    fresh.append(r)
    busy.discard(r.name)"""))

edit("boot-before-publish", "walk.py",
     ("""    order.add(h, r)
    pick.joined(h, r)
    want.joined(h, r)
    if not want.wanted(h, r):
        drop.note(h, r)
    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)""",
      """    for sym in r.boots:
        site.reach(h, r, sym, out)
    order.add(h, r)
    pick.joined(h, r)
    want.joined(h, r)
    if not want.wanted(h, r):
        drop.note(h, r)
    say.up(out, r.name)"""))

edit("uses-survive", "walk.py", ("    r.uses = {}\n", ""))

edit("reup-moves", "walk.py",
     ("""    if r.live:
        was = view.den(h, r)""",
      """    if r.live:
        pick.parted(h, r)
        order.drop(h, r)
        order.add(h, r)
        pick.joined(h, r)
        was = view.den(h, r)"""))

edit("reup-no-hold", "walk.py",
     ("""        _up(h, r, None if wide else view.fresh(h), set(), out)
    hold.take(h, name)""",
      """        _up(h, r, None if wide else view.fresh(h), set(), out)
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

edit("open-is-act", "walk.py",
     ("        _up(h, r, None if wide else view.fresh(h), set(), out)",
      "        _up(h, r, None, set(), out)"))

edit("scope-per-unit", "walk.py",
     ("""        _up(h, r, None if wide else view.fresh(h), set(), out)""",
      """        _up(h, r, None if wide else False, set(), out)"""),
     ("""    view.seal(h, r, den)""",
      """    view.seal(h, r, None if den is None else view.fresh(h))"""))

edit("no-promotion", "walk.py",
     ("""        was = view.den(h, r)
        if wide and was is not None:
            view.open_up(h, r)
            pick.moved(h, r, was)""",
      """        pass"""))

# --- visibility -------------------------------------------------------------------------
whole("see-everything", "view.py", '''def _dens(h):
    d = getattr(h, "dens", None)
    if d is None:
        d = h.dens = {}
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _dens(h)[r.name] = den


def open_up(h, r):
    _dens(h)[r.name] = None


def den(h, r):
    return _dens(h).get(r.name)


def keys(h, caller):
    return tuple(dict.fromkeys([None] + list(_dens(h).values())))
''')

edit("scope-only", "view.py",
     ("""    mine = den(h, caller)
    return (None,) if mine is None else (None, mine)""",
      """    mine = den(h, caller)
    return (None,) if mine is None else (mine,)"""))

# --- which unit answers a name -----------------------------------------------------------
edit("strong-over-fallback", "pick.py",
     ("""def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)""",
      """def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _plain(r, sym):
    return (sym, False) in r.pubs"""),
     ("""        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best""",
      """        lst = i.get((key, sym)) or []
        for r in lst:
            if not _plain(r, sym):
                continue
            if best is None or r.at < best.at:
                best = r
            break
    if best is not None:
        return best
    for key in view.keys(h, caller):
        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best"""))

edit("newest-publisher", "pick.py",
     ("""        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]""",
      """        lst = i.get((key, sym))
        if lst and (best is None or lst[-1].at > best.at):
            best = lst[-1]"""))

edit("promote-at-back", "pick.py",
     ("""    _cut(h, r, was)
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault((None, sym), [])
        lo, hi = 0, len(lst)
        while lo < hi:
            mid = (lo + hi) // 2
            if lst[mid].at < r.at:
                lo = mid + 1
            else:
                hi = mid
        lst.insert(lo, r)""",
      """    _cut(h, r, was)
    _put(h, r, None)"""))

whole("scan-the-order", "pick.py", '''from link import view
from reg import order


def joined(h, r):
    return None


def parted(h, r):
    return None


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in order.live(h):
        if view.den(h, r) not in seen:
            continue
        for s, _fall in r.pubs:
            if s == sym:
                return r
    return None
''')

whole("global-list-filtered", "pick.py", '''from link import view


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def joined(h, r):
    i = _idx(h)
    for sym in _syms(r):
        i.setdefault(sym, []).append(r)


def parted(h, r):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get(sym)
        if not lst:
            continue
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in _idx(h).get(sym, ()):
        if view.den(h, r) in seen:
            return r
    return None
''')

# --- what a call does ---------------------------------------------------------------------
edit("same-name-same-unit", "site.py",
     ("""        r.uses[sym] = (t, t.at)
        say.ran(out, r.name, sym, t.name)
        return
    t, at = u
    if t.live and t.at == at:""",
      """        r.uses[sym] = (t, None)
        say.ran(out, r.name, sym, t.name)
        return
    t, _at = u
    if t.live:"""))

edit("settle-the-miss", "site.py",
     ("""    u = r.uses.get(sym)
    if u is None:
        t = pick.find(h, r, sym)
        if t is None:
            say.miss(out, r.name, sym)
            return""",
      """    u = r.uses.get(sym)
    if u is None and sym in r.uses:
        say.miss(out, r.name, sym)
        return
    if u is None:
        t = pick.find(h, r, sym)
        if t is None:
            r.uses[sym] = None
            say.miss(out, r.name, sym)
            return"""))

whole("resolve-each-call", "site.py", '''from link import pick
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    t = pick.find(h, r, sym)
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
        t, at = u
        if t.live and t.at == at:
            say.ran(out, r.name, sym, t.name)
            return
        del r.uses[sym]
    t = pick.find(h, r, sym)
    if t is None:
        say.dead(out, r.name, sym)
        return
    r.uses[sym] = (t, t.at)
    say.ran(out, r.name, sym, t.name)
''')

edit("call-when-down", "site.py",
     ("""    if not r.live:
        return
    u = r.uses.get(sym)""", """    u = r.uses.get(sym)"""))

# --- what has to stay up --------------------------------------------------------------------
edit("soft-keeps", "want.py",
     ("    return dict.fromkeys(other for other, kind in r.needs if kind)",
      "    return dict.fromkeys(other for other, kind in r.needs)"))

# Counting edges is only wrong when the two halves of the ledger disagree about it, which is
# what happens when they are written at different times: the entry counts every edge, the exit
# gives back one per distinct name, and a unit named twice never goes down.
whole("dedupe-once", "want.py", '''from reg import hold


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def joined(h, r):
    owed = _owed(h)
    for name in [other for other, kind in r.needs if kind]:
        owed[name] = owed.get(name, 0) + 1


def parted(h, r):
    owed = _owed(h)
    freed = []
    for name in dict.fromkeys(other for other, kind in r.needs if kind):
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
''')

edit("deps-need-not-live", "want.py",
     ("""    freed = []
    for name in _hard(r):
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    return freed""",
      """    return []"""))

whole("holds-only", "want.py", '''from reg import hold


def joined(h, r):
    return None


def parted(h, r):
    return []


def wanted(h, r):
    return hold.held(h, r.name) > 0
''')

whole("want-scan", "want.py", '''from reg import hold, order


def joined(h, r):
    return None


def parted(h, r):
    return [other for other, kind in r.needs if kind]


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False
''')

# --- the cascade ------------------------------------------------------------------------------
edit("sweep-forward", "drop.py",
     ("    heapq.heappush(_queue(h), (-r.at, r.at, r.name))",
      "    heapq.heappush(_queue(h), (r.at, r.at, r.name))"))

edit("sweep-drop-stale", "drop.py",
     ("""        for freed in want.parted(h, go):
            rec = h.units.get(freed)
            if rec is not None and rec.live:
                note(h, rec)""",
      """        want.parted(h, go)"""))

edit("rel-any-unit", "drop.py",
     ("""    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)""",
      """    r = tab.get(h, name)
    hold.give(h, name)
    if not r.live:
        return"""))

whole("sweep-rescan", "drop.py", '''from link import pick, want
from reg import hold, order, say, tab


def note(h, r):
    return None


def let(h, name, out):
    r = tab.get(h, name)
    if not r.live or hold.held(h, name) <= 0:
        return
    hold.give(h, name)
    _sweep(h, out)


def _sweep(h, out):
    while True:
        go = None
        for r in order.live(h):
            if not want.wanted(h, r) and (go is None or r.at > go.at):
                go = r
        if go is None:
            return
        want.parted(h, go)
        go.live = False
        order.drop(h, go)
        pick.parted(h, go)
        say.down(out, go.name)
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
    print("%d readings" % len(EDITS))


if __name__ == "__main__":
    sys.exit(build())
