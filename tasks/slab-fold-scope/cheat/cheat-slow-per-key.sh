#!/bin/bash
# correct, with the live keys held one key at a time
set -euo pipefail

cat > /app/tab/live.py <<'PYEOF'
class Buck:
    def __init__(self):
        self.own = {}
        self.sn = {}

    n = 0


def hold(tab, buck):
    b = tab.buck.get(buck)
    if b is None:
        b = tab.buck[buck] = Buck()
    return b


def rows(tab, buck):
    b = tab.buck.get(buck)
    return len(b.own) if b is not None else 0


def at(tab, buck, key):
    b = tab.buck.get(buck)
    if b is None:
        return None
    got = b.own.get(key)
    return None if got is None else got[0]


def drop(b, key, jr):
    got = b.own.pop(key, None)
    jr.append(("k", b, key, got))
    if got is not None:
        sid = got[0]
        b.sn[sid] -= 1
        if not b.sn[sid]:
            del b.sn[sid]
            return sid
    return None


def give(b, key, sid, stamp, jr):
    jr.append(("k", b, key, b.own.get(key)))
    b.own[key] = (sid, stamp)
    b.sn[sid] = b.sn.get(sid, 0) + 1


def undo(jr):
    for _t, b, key, got in reversed(jr):
        now = b.own.get(key)
        if now is not None:
            sid = now[0]
            b.sn[sid] -= 1
            if not b.sn[sid]:
                del b.sn[sid]
        if got is None:
            b.own.pop(key, None)
        else:
            b.own[key] = got
            b.sn[got[0]] = b.sn.get(got[0], 0) + 1
    del jr[:]
PYEOF

cat > /app/tab/lay.py <<'PYEOF'
from tab import mark, wipe


def part(tab, num, buck, lo, hi, jr):
    took = wipe.part(tab, buck, lo, hi, jr)
    mark.fresh(tab, buck, lo, hi, num, jr)
    return (hi - lo + 1) - took
PYEOF

cat > /app/tab/wipe.py <<'PYEOF'
from tab import live


def part(tab, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    took = 0
    for key in range(lo, hi + 1):
        if key in b.own:
            live.drop(b, key, jr)
            took += 1
    return took
PYEOF

cat > /app/tab/mark.py <<'PYEOF'
from tab import live


def fresh(tab, buck, lo, hi, num, jr):
    sid = tab.mint()
    b = live.hold(tab, buck)
    for key in range(lo, hi + 1):
        live.give(b, key, sid, num, jr)
    return sid


def keep(tab, buck, reach, jr):
    b = live.hold(tab, buck)
    sid = tab.mint()
    for key, got in list(b.own.items()):
        if got[0] in reach:
            live.drop(b, key, jr)
            live.give(b, key, sid, got[1], jr)
    return sid
PYEOF

cat > /app/tab/take.py <<'PYEOF'
from tab import live, mark


class Again(Exception):
    pass


def part(tab, base, buck, lo, hi, jr):
    b = live.hold(tab, buck)
    seen = {}
    for key, got in b.own.items():
        sid, stamp = got
        e = seen.get(sid)
        inside = lo <= key <= hi
        if e is None:
            seen[sid] = [1 if inside else 0, 1, stamp, stamp]
        else:
            e[0] += 1 if inside else 0
            e[1] += 1
            if stamp < e[2]:
                e[2] = stamp
            if stamp > e[3]:
                e[3] = stamp
    reach = set()
    for sid, e in seen.items():
        if e[0] != e[1] or not e[0]:
            continue
        if e[2] <= base < e[3]:
            raise Again()
        if e[3] <= base:
            reach.add(sid)
    if len(reach) < 2:
        return False
    mark.keep(tab, buck, reach, jr)
    return True
PYEOF

cat > /app/tab/push.py <<'PYEOF'
from tab import lay, live, say, take, wipe


def once(tab, prop, base, num, jr):
    add = 0
    gone = 0
    made = False
    for kind, buck, lo, hi in prop.parts:
        if kind == "put":
            add += lay.part(tab, num, buck, lo, hi, jr)
            made = True
        elif kind == "cut":
            gone += wipe.part(tab, buck, lo, hi, jr)
        else:
            if take.part(tab, base, buck, lo, hi, jr):
                made = True
    return add, gone, made


def run(tab, prop):
    num = tab.head + 1
    first = tab.next
    jr = []
    try:
        add, gone, made = once(tab, prop, prop.base, num, jr)
    except take.Again:
        live.undo(jr)
        tab.next = first
        add, gone, made = once(tab, prop, tab.head, num, jr)
    if not made and not gone:
        live.undo(jr)
        tab.next = first
        say.void(tab, prop.tag)
        return
    tab.head = num
    say.land(tab, prop.tag, num, add, gone)
PYEOF
