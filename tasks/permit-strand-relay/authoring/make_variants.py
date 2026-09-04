"""Write authoring/variants/ from the reference plus one declared override each.

A variant is the reference with one quantity built a different way. Copying the
files by hand is what lets them rot the moment the reference moves, so every
file a variant does not override is written straight from solution/.
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "solution")
OUT = os.path.join(HERE, "variants")

REPLAY_SEEN = '''

def note(st, when, level, value):
    st.setdefault("said", []).append((when, level, value))


def seen(st, when, level, dflt):
    out = dflt
    for at, who, value in st.get("said", ()):
        if who == level and at <= when - LAG:
            out = value
    return out
'''

REPLAY_OPENED = '''def opened(st, bk, when, fd):
    st["said"] = [row for row in st.get("said", []) if row[1] != fd]
'''

IDENTITY_DRAIN = '''def drained(st, bk, level):
    if level == LINK:
        return bk.lsnt - sum(bk.held(fd) for fd in bk.open())
    return bk.tkn.get(level, 0)
'''

SHED_MAP = '''def shed(st, bk, when, fd, rows):
    book = st.setdefault("gone", {})
    book[fd] = book.get(fd, 0) + rows
'''

SHED_DRAIN = '''def drained(st, bk, level):
    if level == LINK:
        book = st.get("gone", {})
        return bk.ltkn + sum(book[fd] for fd in sorted(book))
    return bk.tkn.get(level, 0)
'''

ALL_FEEDS = '''def plan(st, bk, when):
    out = []
    for level in sorted(bk.pub):
        value = ceiling(st, bk, when, level)
        seat = bk.pub[level]
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
    for level, _, value in out:
        tear.note(st, when, level, value)
    return out
'''

LINK_FIRST = '''def verdict(st, bk, when, fd, rows):
    if bk.lsnt + rows > tear.seen(st, when, LINK, WINL):
        return "over"
    if bk.up(fd):
        if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF):
            return "over"
        return "ok"
    shut = bk.shut.get(fd)
    if shut is None or when - shut >= LAG:
        return "over"
    return "late"
'''

PRUNED_SEEN = '''

def note(st, when, level, value):
    st.setdefault("said", {}).setdefault(level, []).append((when, value))


def seen(st, when, level, dflt):
    rack = st.get("said", {}).get(level)
    if not rack:
        return dflt
    ripe = [value for at, value in rack if at <= when - LAG]
    if not ripe:
        return dflt
    return ripe[-1]
'''

VARIANTS = {
    "ok-replay": {
        "tear.py": [("NOTE_BLOCK", REPLAY_SEEN),
                    ("OPENED_BLOCK", REPLAY_OPENED)],
    },
    "ok-shedmap": {
        "tear.py": [("SHED_BLOCK", SHED_MAP)],
        "rtn.py": [("DRAIN_BLOCK", SHED_DRAIN)],
    },
    "ok-allfeeds": {
        "emit.py": [("PLAN_BLOCK", ALL_FEEDS)],
    },
    "ok-linkfirst": {
        "adm.py": [("VERDICT_BLOCK", LINK_FIRST)],
    },
    "ok-identity": {
        "rtn.py": [("DRAIN_BLOCK", IDENTITY_DRAIN)],
    },
    "ok-pruned": {
        "tear.py": [("NOTE_BLOCK", PRUNED_SEEN)],
    },
}

ANCHORS = {
    "NOTE_BLOCK": ("\n\ndef note(", None),
    "OPENED_BLOCK": ("def opened(", "\n\n\ndef window("),
    "SHED_BLOCK": ("def shed(", "\n\n\ndef opened("),
    "DRAIN_BLOCK": ("def drained(", None),
    "PLAN_BLOCK": ("def plan(", None),
    "VERDICT_BLOCK": ("def verdict(", None),
}


def swap(text, key, fresh):
    start, stop = ANCHORS[key]
    at = text.index(start)
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
            with open(os.path.join(home, leaf), "w", newline="\n") as fh:
                fh.write(body)
        print("wrote %s (%s)" % (name, ", ".join(sorted(VARIANTS[name]))))


if __name__ == "__main__":
    main()
