"""Build one whole allocator per wrong reading, from the reference source.

A reading is not a mutation of a file the agent never writes: it is a complete host that reads
one rule the other way and is otherwise the reference. That is what an agent actually submits,
so it is what has to be separated. Every edit asserts that it fired - a substitution that
matches nothing produces the reference with a different name and scores 1 for the wrong reason.

    python3 make_readings.py            write authoring/aside-fit-sweep/readings/<name>/
"""
import ast
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "tasks" / "aside-fit-sweep" / "solution"
OUT = HERE / "readings"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")


def strip(text):
    """Drop docstrings: what a reading writes into /app/pool/ carries no prose."""
    tree = ast.parse(text)
    kill = set()
    stack = [tree]
    while stack:
        node = stack.pop()
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                for ln in range(first.lineno, first.end_lineno + 1):
                    kill.add(ln)
        stack.extend(ast.iter_child_nodes(node))
    lines = [ln for i, ln in enumerate(text.splitlines(), 1) if i not in kill]
    out = []
    for ln in lines:
        if not ln.strip() and (not out or not out[-1].strip() or out[-1].rstrip().endswith(":")):
            continue
        out.append(ln)
    return "\n".join(out) + "\n"


# --- whole files, for readings that change the machinery rather than a rule -------------

NAIVE_CLIPPED = '''\
def _map(h):
    m = getattr(h, "fm", None)
    if m is None:
        m = h.fm = []
        p = 0
        while p < h.span:
            m.append([p, h.part])
            p += h.part
    return m


def _idx(m, a):
    for i, run in enumerate(m):
        if run[0] <= a < run[0] + run[1]:
            return i
    return -1


def take(h, a, n):
    m = _map(h)
    i = _idx(m, a)
    s, sz = m[i]
    end = s + sz
    fresh = []
    if a > s:
        fresh.append([s, a - s])
    if a + n < end:
        fresh.append([a + n, end - a - n])
    m[i:i + 1] = fresh


def add(h, a, n):
    m = _map(h)
    i = 0
    while i < len(m) and m[i][0] < a:
        i += 1
    m.insert(i, [a, n])
    if i + 1 < len(m) and m[i][0] + m[i][1] == m[i + 1][0] \\
            and m[i][0] // h.part == m[i + 1][0] // h.part:
        m[i][1] += m[i + 1][1]
        del m[i + 1]
    if i > 0 and m[i - 1][0] + m[i - 1][1] == m[i][0] \\
            and m[i - 1][0] // h.part == m[i][0] // h.part:
        m[i - 1][1] += m[i][1]
        del m[i]


def have(h, a, n):
    m = _map(h)
    i = _idx(m, a)
    if i < 0:
        return False
    s, sz = m[i]
    return s <= a and a + n <= s + sz


def after(h, a, n):
    m = _map(h)
    x = a + n
    stop = (a // h.part + 1) * h.part
    if x >= stop:
        return 0
    i = _idx(m, x)
    if i < 0:
        return 0
    s, sz = m[i]
    return min(s + sz, stop) - x


def spot(h, n):
    for s, sz in _map(h):
        if sz >= n:
            return s
    return None
'''

NAIVE_UNCLIPPED = NAIVE_CLIPPED.replace(
    """        m = h.fm = []
        p = 0
        while p < h.span:
            m.append([p, h.part])
            p += h.part""",
    "        m = h.fm = [[0, h.span]]",
).replace(
    """ \\
            and m[i][0] // h.part == m[i + 1][0] // h.part""", ""
).replace(
    """ \\
            and m[i - 1][0] // h.part == m[i][0] // h.part""", ""
)

LAZY_SIDE = '''\
import collections

from pool import find
from reg import geom


def _bag(h):
    b = getattr(h, "sb", None)
    if b is None:
        b = h.sb = ({}, collections.deque())
    return b


def park(h, a, n):
    bysize, ages = _bag(h)
    bysize.setdefault(n, []).append(a)
    ages.append((a, n))
    while sum(len(v) for v in bysize.values()) > geom.ROOM:
        oa, on = ages.popleft()
        lst = bysize.get(on)
        if not lst or oa not in lst:
            continue
        lst.remove(oa)
        find.add(h, oa, on)


def match(h, n):
    bysize, _ages = _bag(h)
    lst = bysize.get(n)
    if not lst:
        return None
    return lst.pop(), n


def all_back(h):
    bysize, ages = _bag(h)
    for n, lst in bysize.items():
        for a in lst:
            find.add(h, a, n)
    bysize.clear()
    ages.clear()
'''

BEST_FIT_SPOT = '''\
def spot(h, n):
    m = _map(h)
    best = None
    for lst in m.runs:
        for s, sz in lst:
            if sz >= n and (best is None or sz < best[1]):
                best = (s, sz)
    return None if best is None else best[0]
'''

SCAN_SPOT = '''\
def spot(h, n):
    m = _map(h)
    for p in range(m.nparts):
        for s, sz in m.runs[p]:
            if sz >= n:
                return s
    return None
'''

REBUILD_FIX = '''\
def _fix(m, p):
    for q in range(m.nparts):
        best = 0
        for _s, sz in m.runs[q]:
            if sz > best:
                best = sz
        m.top[m.wide + q] = best
    for i in range(m.wide - 1, 0, -1):
        a = m.top[2 * i]
        b = m.top[2 * i + 1]
        m.top[i] = a if a > b else b
'''


def _sub(text, old, new, where):
    if old not in text:
        raise SystemExit("reading edit did not fire in %s: %r" % (where, old[:60]))
    return text.replace(old, new, 1)


def _swap_func(text, name, body, where):
    """Replace a whole top-level def with new source."""
    start = text.index("def %s(" % name) if ("def %s(" % name) in text else -1
    if start < 0:
        raise SystemExit("no def %s in %s" % (name, where))
    rest = text[start:]
    end = len(text)
    for marker in ("\n\ndef ", "\n\nclass "):
        at = rest.find(marker, 1)
        if at >= 0:
            end = min(end, start + at + 1)
    return text[:start] + body.rstrip("\n") + "\n" + text[end:]


EDITS = {
    "sweep-drop": ("empties the aside list without returning anything to the map", [
        ("side.py",
         "    for a, n in held.values():\n        find.add(h, a, n)\n    held.clear()\n",
         "    held.clear()\n"),
    ]),
    "put-dead": ("gives a range back for an id that has one recorded but is not live", [
        ("back.py", "    if not r.live:\n        return\n    r.live = False\n",
         "    if r.at < 0:\n        return\n    r.live = False\n"),
    ]),
    "fit-dead": ("resizes the range an id last held even after it has been given back", [
        ("edge.py", "    r = live.get(h, name)\n    if not r.live:\n        return\n",
         "    r = live.get(h, name)\n    if r.at < 0:\n        return\n"),
    ]),
    "part-strict": ("refuses a request of exactly the size a part holds", [
        ("cut.py", "    if not geom.ok(h, n):\n", "    if not 0 < n < h.part:\n"),
    ]),
    "aside-after": ("looks in the map before the aside list", [
        ("cut.py",
         "    hit = side.match(h, n)\n    if hit is not None:\n        return hit\n"
         "    a = find.spot(h, n)\n    if a is None:\n        side.all_back(h)\n"
         "        a = find.spot(h, n)\n        if a is None:\n            return None\n"
         "    return carve(h, a, n)\n",
         "    a = find.spot(h, n)\n    if a is not None:\n        return carve(h, a, n)\n"
         "    hit = side.match(h, n)\n    if hit is not None:\n        return hit\n"
         "    side.all_back(h)\n    a = find.spot(h, n)\n    if a is None:\n"
         "        return None\n    return carve(h, a, n)\n"),
    ]),
    "flush-none": ("lets a request fail without returning what is aside to the map", [
        ("cut.py",
         "    a = find.spot(h, n)\n    if a is None:\n        side.all_back(h)\n"
         "        a = find.spot(h, n)\n        if a is None:\n            return None\n",
         "    a = find.spot(h, n)\n    if a is None:\n        return None\n"),
    ]),
    "flush-eager": ("returns everything aside to the map before every search", [
        ("cut.py",
         "    a = find.spot(h, n)\n    if a is None:\n        side.all_back(h)\n"
         "        a = find.spot(h, n)\n        if a is None:\n            return None\n",
         "    side.all_back(h)\n    a = find.spot(h, n)\n    if a is None:\n"
         "        return None\n"),
    ]),
    "sliver-none": ("leaves every leftover free instead of giving it to the allocation", [
        ("cut.py", "    size = n + t if 0 < t < geom.SLIVER else n\n", "    size = n\n"),
        ("edge.py", "        grown = n + t if 0 < t < geom.SLIVER else n\n", "        grown = n\n"),
    ]),
    "sliver-all": ("gives the allocation any leftover, not only one under sixteen bytes", [
        ("cut.py", "if 0 < t < geom.SLIVER else n", "if t > 0 else n"),
        ("edge.py", "if 0 < t < geom.SLIVER else n", "if t > 0 else n"),
    ]),
    "sliver-wide": ("takes a leftover of exactly sixteen bytes as well", [
        ("cut.py", "if 0 < t < geom.SLIVER else n", "if 0 < t <= geom.SLIVER else n"),
        ("edge.py", "if 0 < t < geom.SLIVER else n", "if 0 < t <= geom.SLIVER else n"),
    ]),
    "size-req": ("records the size that was asked for rather than the size carved", [
        ("cut.py", "    r.at, r.size, r.live = got[0], got[1], True\n",
         "    r.at, r.size, r.live = got[0], n, True\n"),
    ]),
    "reuse-oldest": ("takes the range of a size set aside earliest rather than latest", [
        ("side.py", "held.pop(tags.pop(), None)", "held.pop(tags.pop(0), None)"),
    ]),
    "evict-newest": ("returns the range set aside latest when more than thirty-two are aside", [
        ("side.py", "held.pop(next(iter(held)))", "held.pop(next(reversed(held)))"),
    ]),
    "aside-none": ("returns every freed range to the map, joining it with its neighbours", [
        ("back.py", "    if n <= geom.KEEP:\n        side.park(h, a, n)\n    else:\n"
                    "        find.add(h, a, n)\n", "    find.add(h, a, n)\n"),
    ]),
    "keep-strict": ("sets aside only ranges under 256 bytes, not ranges of exactly 256", [
        ("back.py", "if n <= geom.KEEP:", "if n < geom.KEEP:"),
    ]),
    "join-never": ("returns a range to the map without joining it to its neighbours", [
        ("find.py",
         "    i = _hold(lst, a) + 1\n    s, sz = a, n\n"
         "    if i < len(lst) and lst[i][0] == s + sz:\n        sz += lst[i][1]\n"
         "        del lst[i]\n"
         "    if i > 0 and lst[i - 1][0] + lst[i - 1][1] == s:\n"
         "        s = lst[i - 1][0]\n        sz += lst[i - 1][1]\n        i -= 1\n"
         "        del lst[i]\n    lst.insert(i, (s, sz))\n",
         "    i = _hold(lst, a) + 1\n    lst.insert(i, (a, n))\n"),
    ]),
    "grow-never": ("moves a range that is asked to grow rather than growing it where it is", [
        ("edge.py",
         "    if a + n <= geom.part_end(h, a) and find.have(h, a + m, n - m):\n",
         "    if False:\n"),
    ]),
    "move-free-first": ("frees the old range before placing the new one", [
        ("edge.py",
         "    got = cut.grab(h, n)\n    if got is None:\n        say.no(out, r.id)\n"
         "        return\n    back.give(h, a, m)\n",
         "    back.give(h, a, m)\n    got = cut.grab(h, n)\n    if got is None:\n"
         "        say.no(out, r.id)\n        return\n"),
    ]),
    "shrink-none": ("never releases the tail a resize down leaves", [
        ("edge.py", "        if m - n < geom.SLIVER:\n", "        if True:\n"),
    ]),
    "shrink-any": ("releases the tail a resize down leaves however small it is", [
        ("edge.py", "        if m - n < geom.SLIVER:\n", "        if m == n:\n"),
    ]),
    "shrink-map": ("puts the tail a resize down leaves straight into the map", [
        ("edge.py", "        back.give(h, a + n, m - n)\n", "        find.add(h, a + n, m - n)\n"),
    ]),
    "dup-get": ("serves a request for an id that is already live", [
        ("cut.py", "    r = live.get(h, name)\n    if r.live:\n        return\n    n = geom.up(size)\n",
         "    r = live.get(h, name)\n    n = geom.up(size)\n"),
    ]),
    "no-round": ("places the size that was asked for without rounding it up", [
        ("cut.py", "    n = geom.up(size)\n    if not geom.ok(h, n):",
         "    n = size\n    if not geom.ok(h, n):"),
    ]),
    "zero-ok": ("serves a request that rounds to nothing", [
        ("cut.py", "    if not geom.ok(h, n):\n        say.no(out, r.id)\n        return\n"
                   "    got = grab(h, n)\n",
         "    if n > h.part:\n        say.no(out, r.id)\n        return\n"
         "    got = grab(h, n)\n"),
    ]),
    "grow-aside": ("grows a range into bytes that are set aside", [
        ("side.py", "def all_back(h):",
         "def at_edge(h, a, n):\n    held, bysize, _tick = _bag(h)\n"
         "    for tag, (ha, hn) in held.items():\n        if ha == a and hn == n:\n"
         "            held.pop(tag)\n            bysize[hn].remove(tag)\n"
         "            return True\n    return False\n\n\ndef all_back(h):"),
        ("edge.py", "from pool import back, cut, find\n",
         "from pool import back, cut, find, side\n"),
        ("edge.py",
         "    if a + n <= geom.part_end(h, a) and find.have(h, a + m, n - m):\n",
         "    if a + n <= geom.part_end(h, a) and side.at_edge(h, a + m, n - m):\n"
         "        r.size = n\n        say.same(out, r.id, n)\n        return\n"
         "    if a + n <= geom.part_end(h, a) and find.have(h, a + m, n - m):\n"),
    ]),
}

FULL = {
    "part-cross": ("places a range across a part boundary when the free bytes run that far",
                   {"find.py": NAIVE_UNCLIPPED}),
    "aside-lazy": ("keeps the aside list as one list per size and a queue of addresses, so a "
                   "range set aside, taken and set aside again is given back at the wrong turn",
                   {"side.py": LAZY_SIDE}),
    "slow-scan": ("scans the free ranges from the left on every request, which is correct and "
                  "too slow", {"find.py": NAIVE_CLIPPED}),
}

SWAPS = {
    "fit-best": ("takes the smallest free range that fits rather than the leftmost address",
                 [("find.py", "spot", BEST_FIT_SPOT)]),
    "slow-max": ("looks at every part in turn to find the leftmost that can hold the request, "
                 "which is correct and too slow", [("find.py", "spot", SCAN_SPOT)]),
    "slow-rebuild": ("re-derives every part's maximum whenever one part changes, which is "
                     "correct and too slow", [("find.py", "_fix", REBUILD_FIX)]),
}


def base():
    return {p: (SRC / p).read_text(encoding="utf-8") for p in PARTS}


def build(name):
    files = base()
    if name in EDITS:
        blurb, edits = EDITS[name]
        for fname, old, new in edits:
            files[fname] = _sub(files[fname], old, new, "%s/%s" % (name, fname))
    elif name in FULL:
        blurb, whole = FULL[name]
        for fname, text in whole.items():
            files[fname] = text
    else:
        blurb, swaps = SWAPS[name]
        for fname, func, body in swaps:
            files[fname] = _swap_func(files[fname], func, body, "%s/%s" % (name, fname))
    return blurb, {p: strip(t) for p, t in files.items()}


def names():
    return sorted(list(EDITS) + list(FULL) + list(SWAPS))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    plain = {p: strip(t) for p, t in base().items()}
    for name in names():
        blurb, files = build(name)
        room = OUT / name
        room.mkdir()
        (room / "BLURB").write_text(blurb + "\n", encoding="utf-8", newline="\n")
        # Only what the reading actually changes is written. emit.py starts from the
        # reference and lays these over it, so a reading is legible as its own diff.
        for fname, text in files.items():
            if text != plain[fname]:
                (room / fname).write_text(text, encoding="utf-8", newline="\n")
    print("wrote %d readings" % len(names()))


if __name__ == "__main__":
    main()
