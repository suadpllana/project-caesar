"""Write authoring/variants/ from the reference plus one declared override each.

A variant is the reference with one quantity built a different way. Copying the
files by hand is what lets them rot the moment the reference moves, so every
file a variant does not override is written straight from solution/.

Every variant has to finish a wide stream, so each one keeps some schedule of
its own - a heap, a single deadline queue, buckets - and none asks about every
feed on every tick.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "solution")
OUT = os.path.join(HERE, "variants")

BISECT_SEEN = '''

def note(st, when, level, value):
    rack = st.setdefault("said", {}).setdefault(level, ([], []))
    rack[0].append(when)
    rack[1].append(value)


def seen(st, when, level, dflt):
    rack = st.get("said", {}).get(level)
    if not rack:
        return dflt
    idx = bisect.bisect_right(rack[0], when - LAG)
    return dflt if idx == 0 else rack[1][idx - 1]


def sent(st, fd, rows):
    back = st.setdefault("back", {})
    back[fd] = back.get(fd, 0) + rows


def belief(st, bk, fd):
    return bk.snt.get(fd, 0) + st.get("back", {}).get(fd, 0)


def touch(st, level):
    st.setdefault("dirty", set()).add(level)


def due(st, fd, when):
    st.setdefault("due", {}).setdefault(when, []).append(fd)
'''

PRUNED_SEEN = '''

def note(st, when, level, value):
    st.setdefault("said", {}).setdefault(level, []).append((when, value))


def seen(st, when, level, dflt):
    known = st.setdefault("known", {})
    rack = st.get("said", {}).get(level) or []
    while rack and rack[0][0] <= when - LAG:
        known[level] = rack.pop(0)[1]
    return known.get(level, dflt)


def sent(st, fd, rows):
    back = st.setdefault("back", {})
    back[fd] = back.get(fd, 0) + rows


def belief(st, bk, fd):
    return bk.snt.get(fd, 0) + st.get("back", {}).get(fd, 0)


def touch(st, level):
    st.setdefault("dirty", set()).add(level)


def due(st, fd, when):
    st.setdefault("due", {}).setdefault(when, []).append(fd)
'''

PRUNED_OPENED = '''def opened(st, bk, when, fd):
    st.setdefault("said", {}).pop(fd, None)
    st.setdefault("known", {}).pop(fd, None)
    st.setdefault("back", {}).pop(fd, None)
    touch(st, fd)
    due(st, fd, when + IDLE)
'''

HEAP_DUE = '''def touch(st, level):
    st.setdefault("dirty", set()).add(level)


def due(st, fd, when):
    heapq.heappush(st.setdefault("clock", []), (when, fd))
'''

HEAP_PLAN = '''def plan(st, bk, when):
    if "boot" not in st:
        st["boot"] = when
        for fd in bk.shut:
            tear.due(st, fd, bk.last.get(fd, when) + IDLE)
    look = st.get("dirty") or set()
    clock = st.get("clock") or []
    while clock and clock[0][0] <= when:
        look.add(heapq.heappop(clock)[1])
    out = []
    for level in sorted(look):
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
    st["dirty"] = set()
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
'''

ONEQUEUE_DUE = '''def touch(st, level):
    st.setdefault("ask", {}).setdefault(st.get("now", 0), set()).add(level)


def due(st, fd, when):
    st.setdefault("ask", {}).setdefault(when, set()).add(fd)
'''

ONEQUEUE_PLAN = '''def plan(st, bk, when):
    if "boot" not in st:
        st["boot"] = when
        for fd in bk.shut:
            tear.due(st, fd, bk.last.get(fd, when) + IDLE)
    look = st.get("ask", {}).pop(when, set())
    st["now"] = when + 1
    out = []
    for level in sorted(look):
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
'''

IDENTITY_DRAIN = '''def took(st, bk, when, fd, rows):
    st["held"] = st.get("held", 0) - rows
    tear.touch(st, fd)
    tear.touch(st, LINK)


def drained(st, bk, level):
    if level == LINK:
        return bk.lsnt - st.get("held", 0)
    return bk.tkn.get(level, 0)
'''

IDENTITY_VERDICT = '''def verdict(st, bk, when, fd, rows):
    room = tear.seen(st, when, LINK, WINL)
    if not bk.up(fd):
        shut = bk.shut.get(fd)
        if shut is not None and when - shut < LAG:
            if bk.lsnt + rows > room:
                return "over"
            st["late"] = rows
            return "late"
        return "over"
    if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF) or bk.lsnt + rows > room:
        tear.sent(st, fd, rows)
        tear.touch(st, fd)
        return "over"
    st["held"] = st.get("held", 0) + rows
    tear.touch(st, fd)
    tear.touch(st, LINK)
    tear.due(st, fd, when + IDLE)
    return "ok"
'''

IDENTITY_SHED = '''def shed(st, bk, when, fd, rows):
    if st.get("late") == rows:
        st["late"] = None
    else:
        st["held"] = st.get("held", 0) - rows
    touch(st, -1)
'''

LINK_FIRST = '''def verdict(st, bk, when, fd, rows):
    if bk.lsnt + rows > tear.seen(st, when, LINK, WINL):
        if bk.up(fd):
            tear.sent(st, fd, rows)
            tear.touch(st, fd)
        return "over"
    if bk.up(fd):
        if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF):
            tear.sent(st, fd, rows)
            tear.touch(st, fd)
            return "over"
        tear.touch(st, fd)
        tear.touch(st, LINK)
        tear.due(st, fd, when + IDLE)
        return "ok"
    shut = bk.shut.get(fd)
    if shut is None or when - shut >= LAG:
        return "over"
    return "late"
'''

COUNT_VERDICT = '''def verdict(st, bk, when, fd, rows):
    room = tear.seen(st, when, LINK, WINL)
    if not bk.up(fd):
        shut = bk.shut.get(fd)
        if shut is not None and when - shut < LAG:
            if bk.lsnt + rows > room:
                return "over"
            return "late"
        return "over"
    told = st.setdefault("told", {})
    told[fd] = told.get(fd, 0) + rows
    tear.touch(st, fd)
    if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF) or bk.lsnt + rows > room:
        return "over"
    tear.touch(st, LINK)
    tear.due(st, fd, when + IDLE)
    return "ok"
'''

COUNT_OWED = '''def owed(st, bk, when, level, value):
    spent = bk.lsnt if level == LINK else st.get("told", {}).get(level, 0)
    return bk.pub.get(level, 0) - spent < MINB and value - spent >= MINB
'''

COUNT_OPENED = '''def opened(st, bk, when, fd):
    st.setdefault("said", {}).pop(fd, None)
    st.setdefault("mark", {}).pop(fd, None)
    st.setdefault("told", {}).pop(fd, None)
    touch(st, fd)
    due(st, fd, when + IDLE)
'''

RENAMED = [
    ("gone", "sunk"), ("said", "told"), ("mark", "ptr"), ("dirty", "moved"),
    ("due", "alarm"), ("boot", "began"), ("back", "refused"),
]

VARIANTS = {
    "ok-renamed": {},
    "ok-bisect": {
        "tear.py": [("NOTE_BLOCK", BISECT_SEEN), ("IMPORT", "import bisect\n\n")],
    },
    "ok-pruned": {
        "tear.py": [("NOTE_BLOCK", PRUNED_SEEN), ("OPENED_BLOCK", PRUNED_OPENED)],
    },
    "ok-heap": {
        "tear.py": [("TOUCH_BLOCK", HEAP_DUE), ("IMPORT", "import heapq\n\n")],
        "emit.py": [("PLAN_BLOCK", HEAP_PLAN), ("IMPORT", "import heapq\n\n")],
    },
    "ok-onequeue": {
        "tear.py": [("TOUCH_BLOCK", ONEQUEUE_DUE)],
        "emit.py": [("PLAN_BLOCK", ONEQUEUE_PLAN)],
    },
    "ok-identity": {
        "rtn.py": [("TOOK_BLOCK", IDENTITY_DRAIN)],
        "adm.py": [("VERDICT_BLOCK", IDENTITY_VERDICT)],
        "tear.py": [("SHED_BLOCK", IDENTITY_SHED)],
    },
    "ok-linkfirst": {
        "adm.py": [("VERDICT_BLOCK", LINK_FIRST)],
    },
    "ok-count": {
        "adm.py": [("VERDICT_BLOCK", COUNT_VERDICT)],
        "emit.py": [("OWED_BLOCK", COUNT_OWED)],
        "tear.py": [("OPENED_BLOCK", COUNT_OPENED)],
    },
}

ANCHORS = {
    "NOTE_BLOCK": ("\n\ndef note(", None),
    "OPENED_BLOCK": ("def opened(", "\n\n\ndef window("),
    "SHED_BLOCK": ("def shed(", "\n\n\ndef opened("),
    "TOUCH_BLOCK": ("def touch(", None),
    "TOOK_BLOCK": ("def took(", None),
    "PLAN_BLOCK": ("def plan(", None),
    "OWED_BLOCK": ("def owed(", "\n\n\ndef plan("),
    "VERDICT_BLOCK": ("def verdict(", None),
    "IMPORT": ("from lnk.book import", "from lnk.book import"),
}


def swap(text, key, fresh):
    start, stop = ANCHORS[key]
    at = text.index(start)
    if key == "IMPORT":
        return text[:at] + fresh + text[at:]
    end = len(text) if stop is None else text.index(stop, at)
    old = text[at:end]
    if old == fresh:
        raise SystemExit("swap %s is a no-op" % key)
    return text[:at] + fresh + text[end:]


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    for name in sorted(VARIANTS):
        home = os.path.join(OUT, name)
        os.makedirs(home)
        for leaf in sorted(os.listdir(REF)):
            if not leaf.endswith(".py"):
                continue
            body = open(os.path.join(REF, leaf)).read()
            for key, fresh in VARIANTS[name].get(leaf, []):
                body = swap(body, key, fresh)
            if name == "ok-renamed":
                for old, new in RENAMED:
                    body = body.replace('"%s"' % old, '"%s"' % new)
            with open(os.path.join(home, leaf), "w", newline="\n") as fh:
                fh.write(body)
        note = ", ".join(sorted(VARIANTS[name])) or "every state key renamed"
        print("wrote %s (%s)" % (name, note))


if __name__ == "__main__":
    main()
