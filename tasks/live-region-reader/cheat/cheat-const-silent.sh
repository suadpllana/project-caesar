#!/bin/bash
# says nothing on every page
set -euo pipefail

cat > /app/sr/look.py <<'PYEOF'
POL = ("polite", "assertive")
BASE = ("additions", "text")


def hides(pg, e):
    return pg.attr(e, "hidden") is not None or pg.attr(e, "aria-hidden") == "true"


def shown(pg, n):
    x = n
    while x is not None:
        if not pg.is_text(x) and hides(pg, x):
            return False
        if x == 0:
            return True
        x = pg.up(x)
    return False


def region(pg, n):
    x = n
    while x is not None:
        if not pg.is_text(x) and pg.attr(x, "aria-live") in POL:
            return x
        x = pg.up(x)
    return None


def relevant(pg, n):
    x = n
    while x is not None:
        if not pg.is_text(x):
            v = pg.attr(x, "aria-relevant")
            if v is not None:
                got = set(v.split())
                if "all" in got:
                    return {"additions", "removals", "text"}
                return got
        x = pg.up(x)
    return set(BASE)


def busy(pg, r):
    return pg.attr(r, "aria-busy") == "true"


def loud(pg, r):
    return pg.attr(r, "aria-live")
PYEOF

cat > /app/sr/know.py <<'PYEOF'
class Know:
    def __init__(self):
        self.said = {}

    def fresh(self, r, text):
        return self.said.get(r) != text

    def mark(self, r, text):
        self.said[r] = text
PYEOF

cat > /app/sr/watch.py <<'PYEOF'
from . import look


def _texts(pg, top):
    return [x for x in pg.walk(top) if pg.is_text(x)]


def changes(pg, recs):
    out = []
    for rec in recs:
        head = rec[0]
        if head == "text":
            n = rec[1]
            if look.shown(pg, n):
                r = look.region(pg, n)
                if r is not None:
                    out.append(("text", r, n, pg.text(n)))
        elif head in ("add", "move"):
            for x in _texts(pg, rec[1]):
                if look.shown(pg, x):
                    r = look.region(pg, x)
                    if r is not None:
                        out.append(("additions", r, x, pg.text(x)))
        elif head == "drop":
            old = rec[2]
            if look.shown(pg, old):
                r = look.region(pg, old)
                if r is not None:
                    for x in _texts(pg, rec[1]):
                        out.append(("removals", r, x, pg.text(x)))
    return out
PYEOF

cat > /app/sr/unit.py <<'PYEOF'
from . import look


def unit(pg, r):
    if pg.attr(r, "aria-atomic") == "true":
        return r
    return None


def text_of(pg, u):
    out = []
    todo = [u]
    while todo:
        x = todo.pop()
        if pg.is_text(x):
            out.append(pg.text(x))
            continue
        if look.hides(pg, x):
            continue
        todo.extend(reversed(pg.kids(x)))
    return " ".join(out)
PYEOF

cat > /app/sr/line.py <<'PYEOF'
from collections import deque


class Line:
    def __init__(self):
        self.q = deque()

    def push(self, cls, text):
        self.q.append((cls, text))

    def flush(self):
        self.q.clear()

    def pop(self):
        return self.q.popleft() if self.q else None
PYEOF

cat > /app/sr/voice.py <<'PYEOF'
class Reader:
    def __init__(self, pg):
        self.pg = pg

    def load(self):
        pass

    def step(self, t, recs):
        return []
PYEOF

