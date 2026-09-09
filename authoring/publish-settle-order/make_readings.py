"""Derive every wrong reading from the reference, mechanically.

A reading is the reference with one decision taken the other way: the shape a plausible wrong
plan produces. Writing them as edits rather than as copies keeps them in step with the
reference, and every replacement asserts that it fired, so a reading can never quietly become a
byte-for-byte copy of the thing it is supposed to differ from.

Six of them are semantically identical to the reference on purpose. Those are the ones the
execution limit separates: a resolution that scans the order, one that keeps one list per name
and filters it by visibility, one that compares candidates by their position in the order, one
that rebuilds its index whenever the order is spliced into, a retention question answered by a
scan, and a teardown that rescans the live set for candidates.

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


KEYS = '''    if before is None:
        r.at = (h.tick,)
        order.add(h, r)
    else:
        k = before.at
        r.at = k[:-1] + (k[-1] - 1, h.tick)
        order.put(h, r, before)'''

LOAD = '''            _up(h, r, view.home(h, caller), caller, out)
            want.tied(h, caller, r)
            return r'''

# --- the activation walk ----------------------------------------------------------------
edit("boots-after-closure", "walk.py",
     ("""        _up(h, r, None if wide else view.fresh(h), None, out)
    hold.take(h, name)""",
      """        fresh = []
        _up(h, r, None if wide else view.fresh(h), None, fresh, out)
        for x in fresh:
            for sym in x.boots:
                site.reach(h, x, sym, out)
    hold.take(h, name)"""),
     (LOAD, """            fresh = []
            _up(h, r, view.home(h, caller), caller, fresh, out)
            for x in fresh:
                for s2 in x.boots:
                    site.reach(h, x, s2, out)
            want.tied(h, caller, r)
            return r"""),
     ("def _up(h, r, den, before, out):", "def _up(h, r, den, before, fresh, out):"),
     ("        _up(h, dr, den, before, out)", "        _up(h, dr, den, before, fresh, out)"),
     ("""    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)
    busy.discard(r.name)""",
      """    say.up(out, r.name)
    fresh.append(r)
    busy.discard(r.name)"""))

edit("boot-before-publish", "walk.py",
     ("""    view.seal(h, r, den)
    pick.joined(h, r)""",
      """    view.seal(h, r, den)
    for sym in r.boots:
        site.reach(h, r, sym, out)
    pick.joined(h, r)"""),
     ("""    say.up(out, r.name)
    for sym in r.boots:
        site.reach(h, r, sym, out)
    busy.discard(r.name)""",
      """    say.up(out, r.name)
    busy.discard(r.name)"""))

edit("uses-survive", "walk.py", ("    r.uses = {}\n", ""))

edit("reup-moves", "walk.py",
     ("""    if r.live:
        was = view.den(h, r)""",
      """    if r.live:
        pick.parted(h, r)
        order.drop(h, r)
        h.tick = getattr(h, 'tick', 0) + 1
        r.at = (h.tick,)
        order.add(h, r)
        pick.joined(h, r)
        was = view.den(h, r)"""))

edit("reup-no-hold", "walk.py",
     ("""        _up(h, r, None if wide else view.fresh(h), None, out)
    hold.take(h, name)""",
      """        _up(h, r, None if wide else view.fresh(h), None, out)
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
     ("        _up(h, r, None if wide else view.fresh(h), None, out)",
      "        _up(h, r, None, None, out)"))

edit("scope-per-unit", "walk.py",
     ("""        _up(h, r, None if wide else view.fresh(h), None, out)""",
      """        _up(h, r, None if wide else False, None, out)"""),
     ("""    view.seal(h, r, den)""",
      """    view.seal(h, r, None if den is None else view.fresh(h))"""))

edit("no-promotion", "walk.py",
     ("""        was = view.den(h, r)
        if wide and was is not None:
            view.open_up(h, r)
            pick.moved(h, r, was)""",
      """        pass"""))

# --- the order key ------------------------------------------------------------------------
edit("int-keys", "walk.py",
     (KEYS, """    r.at = h.tick
    if before is None:
        order.add(h, r)
    else:
        order.put(h, r, before)"""))

edit("float-keys", "walk.py",
     (KEYS, """    if before is None:
        r.at = float(h.tick)
        order.add(h, r)
    else:
        low = before.back.at if before.back is not None else before.at - 1.0
        r.at = (low + before.at) / 2.0
        order.put(h, r, before)"""))

# --- the load ------------------------------------------------------------------------------
edit("no-autoload", "site.py",
     ("""        if t is None and walk.lazy(h, r, sym, out) is not None:
            t = pick.find(h, r, sym)
""", ""))

edit("auto-answer-self", "site.py",
     ("""        if t is None and walk.lazy(h, r, sym, out) is not None:
            t = pick.find(h, r, sym)""",
      """        if t is None:
            t = walk.lazy(h, r, sym, out)"""))

edit("auto-holds", "walk.py",
     (LOAD, """            _up(h, r, view.home(h, caller), caller, out)
            want.tied(h, caller, r)
            hold.take(h, r.name)
            return r"""))

edit("auto-at-back", "walk.py",
     ("            _up(h, r, view.home(h, caller), caller, out)",
      "            _up(h, r, view.home(h, caller), None, out)"))

edit("auto-nested-at-back", "walk.py",
     ("            _up(h, r, view.home(h, caller), caller, out)",
      "            _up(h, r, view.home(h, caller), None if busy else caller, out)"))

edit("auto-public-always", "walk.py",
     ("            _up(h, r, view.home(h, caller), caller, out)",
      "            _up(h, r, None, caller, out)"))

edit("auto-fresh-scope", "walk.py",
     ("            _up(h, r, view.home(h, caller), caller, out)",
      "            _up(h, r, view.fresh(h), caller, out)"))

edit("auto-into-visibility", "walk.py",
     ("            _up(h, r, view.home(h, caller), caller, out)",
      "            _up(h, r, view.den(h, caller), caller, out)"))

edit("busy-per-load", "walk.py",
     ("""    busy = _busy(h)
    for name in h.autos:
        r = h.units[name]
        if r.live or name in busy:
            continue
        if any(s == sym for s, _fall in r.pubs):
            _up(h, r, view.home(h, caller), caller, out)
            want.tied(h, caller, r)
            return r
    return None""",
      """    keep = _busy(h)
    busy = h.busy = set()
    try:
        for name in h.autos:
            r = h.units[name]
            if r.live or name in busy:
                continue
            if any(s == sym for s, _fall in r.pubs):
                _up(h, r, view.home(h, caller), caller, out)
                want.tied(h, caller, r)
                return r
        return None
    finally:
        h.busy = keep"""))

edit("no-tie", "walk.py",
     ("            want.tied(h, caller, r)\n", ""))

edit("auto-decl-order", "walk.py",
     ("""    for name in h.autos:
        r = h.units[name]
""",
      """    for name, r in h.units.items():
        if not r.auto:
            continue
"""))

edit("auto-last-marked", "walk.py",
     ("    for name in h.autos:", "    for name in reversed(h.autos):"))

edit("auto-up-promoted", "walk.py",
     ("""        if r.live or name in busy:
            continue
        if any(s == sym for s, _fall in r.pubs):
            _up(h, r, view.home(h, caller), caller, out)""",
      """        if name in busy:
            continue
        if any(s == sym for s, _fall in r.pubs):
            if r.live:
                was = view.den(h, r)
                if was is not None:
                    view.open_up(h, r)
                    pick.moved(h, r, was)
                return r
            _up(h, r, view.home(h, caller), caller, out)"""))

# --- visibility -------------------------------------------------------------------------
whole("see-everything", "view.py", '''def _tab(h, key):
    d = getattr(h, key, None)
    if d is None:
        d = {}
        setattr(h, key, d)
    return d


def fresh(h):
    h.scopes = getattr(h, "scopes", 0) + 1
    return h.scopes


def seal(h, r, den):
    _tab(h, "dens")[r.name] = den
    _tab(h, "homes")[r.name] = den


def open_up(h, r):
    _tab(h, "dens")[r.name] = None


def den(h, r):
    return _tab(h, "dens").get(r.name)


def home(h, r):
    return _tab(h, "homes").get(r.name)


def keys(h, caller):
    return tuple(dict.fromkeys([None] + list(_tab(h, "dens").values())))
''')

edit("scope-only", "view.py",
     ("""    mine = home(h, caller)
    return (None,) if mine is None else (None, mine)""",
      """    mine = home(h, caller)
    return (None,) if mine is None else (mine,)"""))

edit("promote-drops-home", "view.py",
     ("""def open_up(h, r):
    _tab(h, "dens")[r.name] = None""",
      """def open_up(h, r):
    _tab(h, "dens")[r.name] = None
    _tab(h, "homes")[r.name] = None"""))

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
    _put(h, r, None)""",
      """    _cut(h, r, was)
    for sym in _syms(r):
        _idx(h).setdefault((None, sym), []).append(r)"""))

edit("bucket-append", "pick.py",
     ("""        if not lst or lst[-1].at < r.at:
            lst.append(r)
        else:
            lst.insert(_slot(lst, r.at), r)""",
      """        lst.append(r)"""),
     ("""        n = _slot(lst, r.at)
        if n < len(lst) and lst[n] is r:
            del lst[n]""",
      """        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break"""))

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


def _slot(lst, at):
    lo, hi = 0, len(lst)
    while lo < hi:
        mid = (lo + hi) // 2
        if lst[mid].at < at:
            lo = mid + 1
        else:
            hi = mid
    return lo


def joined(h, r):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.setdefault(sym, [])
        lst.insert(_slot(lst, r.at), r)


def parted(h, r):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get(sym)
        if not lst:
            continue
        n = _slot(lst, r.at)
        if n < len(lst) and lst[n] is r:
            del lst[n]


def moved(h, r, was):
    return None


def find(h, caller, sym):
    seen = view.keys(h, caller)
    for r in _idx(h).get(sym, ()):
        if view.den(h, r) in seen:
            return r
    return None
''')

whole("pos-compare", "pick.py", '''from link import view
from reg import order


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _cut(h, r, den):
    i = _idx(h)
    for sym in _syms(r):
        lst = i.get((den, sym), [])
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def joined(h, r):
    i = _idx(h)
    den = view.den(h, r)
    for sym in _syms(r):
        i.setdefault((den, sym), []).append(r)


def parted(h, r):
    _cut(h, r, view.den(h, r))


def moved(h, r, was):
    _cut(h, r, was)
    i = _idx(h)
    for sym in _syms(r):
        i.setdefault((None, sym), []).append(r)


def find(h, caller, sym):
    best, at = None, -1
    for key in view.keys(h, caller):
        for r in _idx(h).get((key, sym), ()):
            p = order.pos(h, r)
            if best is None or p < at:
                best, at = r, p
    return best
''')

whole("rebuild-on-load", "pick.py", '''from link import view
from reg import order


def _idx(h):
    i = getattr(h, "idx", None)
    if i is None:
        i = h.idx = {}
    return i


def _syms(r):
    return dict.fromkeys(p[0] for p in r.pubs)


def _rebuild(h):
    i = {}
    for r in order.live(h):
        den = view.den(h, r)
        for sym in _syms(r):
            i.setdefault((den, sym), []).append(r)
    h.idx = i


def joined(h, r):
    if r.fore is not None:
        _rebuild(h)
        return
    i = _idx(h)
    den = view.den(h, r)
    for sym in _syms(r):
        i.setdefault((den, sym), []).append(r)


def parted(h, r):
    i = _idx(h)
    den = view.den(h, r)
    for sym in _syms(r):
        lst = i.get((den, sym), [])
        for n, x in enumerate(lst):
            if x is r:
                del lst[n]
                break


def moved(h, r, was):
    _rebuild(h)


def find(h, caller, sym):
    i = _idx(h)
    best = None
    for key in view.keys(h, caller):
        lst = i.get((key, sym))
        if lst and (best is None or lst[0].at < best.at):
            best = lst[0]
    return best
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
        if t is None and walk.lazy(h, r, sym, out) is not None:
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
        if t is None and walk.lazy(h, r, sym, out) is not None:
            t = pick.find(h, r, sym)
        if t is None:
            r.uses[sym] = None
            say.miss(out, r.name, sym)
            return"""))

whole("resolve-each-call", "site.py", '''from link import pick, walk
from reg import say


def reach(h, r, sym, out):
    if not r.live:
        return
    t = pick.find(h, r, sym)
    if t is None and walk.lazy(h, r, sym, out) is not None:
        t = pick.find(h, r, sym)
    if t is None:
        say.miss(out, r.name, sym)
        return
    say.ran(out, r.name, sym, t.name)
''')

whole("dead-rebinds", "site.py", '''from link import pick, walk
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
        return
    t = pick.find(h, r, sym)
    if t is None and walk.lazy(h, r, sym, out) is not None:
        t = pick.find(h, r, sym)
    if t is None:
        say.miss(out, r.name, sym)
        return
    r.uses[sym] = (t, t.at)
    say.ran(out, r.name, sym, t.name)
''')

edit("dead-reloads", "site.py",
     ("""    t, at = u
    if t.live and t.at == at:
        say.ran(out, r.name, sym, t.name)
    else:
        say.dead(out, r.name, sym)""",
      """    t, at = u
    if t.live and t.at == at:
        say.ran(out, r.name, sym, t.name)
        return
    del r.uses[sym]
    if walk.lazy(h, r, sym, out) is None:
        say.dead(out, r.name, sym)
        return
    t = pick.find(h, r, sym)
    r.uses[sym] = (t, t.at)
    say.ran(out, r.name, sym, t.name)"""))

edit("call-when-down", "site.py",
     ("""    if not r.live:
        return
    u = r.uses.get(sym)""", """    u = r.uses.get(sym)"""))

# --- what has to stay up --------------------------------------------------------------------
edit("soft-keeps", "want.py",
     ("    return dict.fromkeys(other for other, kind in r.needs if kind)",
      "    return dict.fromkeys(other for other, kind in r.needs)"))

edit("ties-outlive-caller", "want.py",
     ("    for name in list(_hard(r)) + r.ties:", "    for name in _hard(r):"))

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


def tied(h, r, t):
    r.ties.append(t.name)
    owed = _owed(h)
    owed[t.name] = owed.get(t.name, 0) + 1


def parted(h, r):
    owed = _owed(h)
    freed = []
    for name in list(dict.fromkeys(other for other, kind in r.needs if kind)) + r.ties:
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    r.ties = []
    return freed


def wanted(h, r):
    return hold.held(h, r.name) > 0 or _owed(h).get(r.name, 0) > 0
''')

edit("deps-need-not-live", "want.py",
     ("""    owed = _owed(h)
    freed = []
    for name in list(_hard(r)) + r.ties:
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    r.ties = []
    return freed""",
      """    r.ties = []
    return []"""))

whole("holds-only", "want.py", '''from reg import hold


def joined(h, r):
    return None


def tied(h, r, t):
    return None


def parted(h, r):
    return []


def wanted(h, r):
    return hold.held(h, r.name) > 0
''')

whole("want-scan", "want.py", '''from reg import hold, order


def joined(h, r):
    return None


def tied(h, r, t):
    r.ties.append(t.name)


def parted(h, r):
    names = [other for other, kind in r.needs if kind] + r.ties
    r.ties = []
    return names


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    for o in order.live(h):
        if o is r:
            continue
        if r.name in o.ties:
            return True
        for other, kind in o.needs:
            if kind and other == r.name:
                return True
    return False
''')

whole("cycle-gc", "want.py", '''from reg import hold, order


def _owed(h):
    d = getattr(h, "owed", None)
    if d is None:
        d = h.owed = {}
    return d


def _hard(r):
    return dict.fromkeys(other for other, kind in r.needs if kind)


def joined(h, r):
    owed = _owed(h)
    for name in _hard(r):
        owed[name] = owed.get(name, 0) + 1


def tied(h, r, t):
    r.ties.append(t.name)
    owed = _owed(h)
    owed[t.name] = owed.get(t.name, 0) + 1


def parted(h, r):
    owed = _owed(h)
    freed = []
    for name in list(_hard(r)) + r.ties:
        left = owed.get(name, 0) - 1
        owed[name] = left
        if left <= 0:
            freed.append(name)
    r.ties = []
    return freed


def wanted(h, r):
    if hold.held(h, r.name) > 0:
        return True
    seen = set()
    stack = [o for o in order.live(h) if hold.held(h, o.name) > 0]
    while stack:
        o = stack.pop()
        if o.name in seen:
            continue
        seen.add(o.name)
        if o is r:
            return True
        for other in list(_hard(o)) + list(o.ties):
            dr = h.units.get(other)
            if dr is not None and dr.live and dr.name not in seen:
                stack.append(dr)
    return False
''')

# --- the cascade ------------------------------------------------------------------------------
edit("sweep-forward", "drop.py",
     ("        return self.at > other.at", "        return self.at < other.at"))

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
