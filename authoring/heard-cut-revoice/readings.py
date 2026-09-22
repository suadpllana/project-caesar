"""Wrong readings of heard-cut-revoice, each written down as a whole reader.

Authoring only; never ships. Every reading is the reference with one or two of its files
changed, produced by an exact-match patch that must fire exactly once - a patch that silently
misses would leave the reading equal to the reference and report it "separated" for the wrong
reason (CLAUDE.md, reach-pair-sweep: a rename must assert it fired).

This is the contract tools/readingcheck.py reads: REFERENCE, READINGS, run, enumerated,
generated. `emit.py` turns the same dictionary into cheat scripts.
"""
import importlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "heard-cut-revoice")
REFERENCE = os.path.join(TASK, "solution")
SHIPPED = os.path.join(TASK, "environment", "app_src", "sr")
FROZEN = ("__init__.py", "page.py", "script.py", "say.py")
PARTS = ("look.py", "know.py", "watch.py", "unit.py", "line.py", "voice.py")

sys.path.insert(0, os.path.join(TASK, "tests"))
import cases  # noqa: E402
import gen  # noqa: E402


def _src(name):
    with open(os.path.join(REFERENCE, name), encoding="utf-8") as fh:
        return fh.read()


def patch(src, old, new):
    n = src.count(old)
    if n != 1:
        raise AssertionError("patch anchor found %d times: %r" % (n, old[:60]))
    return src.replace(old, new)


def _one(fname, pairs):
    s = _src(fname)
    for old, new in pairs:
        s = patch(s, old, new)
    return {fname: s}


def _many(spec):
    out = {}
    for fname, pairs in spec.items():
        out.update(_one(fname, pairs))
    return out


QUEUE_VOICE = '''"""Reading: gather everything pending when the reader is free, and speak the queue as built."""
from . import look, say, unit
from .know import Know
from .line import Line
from .watch import Watch


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.know = Know()
        self.line = Line()
        self.watch = Watch(pg, self.know, self.line)
        self.play = None
        self.queue = []
        self.now_keys = {}

    def load(self):
        self.know.load(self.watch.survey())

    def _group(self, u):
        pg, know, line, watch = self.pg, self.know, self.line, self.watch
        texts, els = unit.read(pg, u)
        group = []
        for x in texts:
            r, cur = watch.now(x)
            k = (r, x)
            if line.ready(k) and unit.unit(pg, know, k, cur) == u:
                group.append((k, cur))
        for a in els:
            for k in line.anchored(a):
                if line.ready(k) and unit.unit(pg, know, k, None) == u:
                    group.append((k, None))
        return " ".join(pg.text(x) for x in texts), group

    def _prepare(self):
        pg, know, line, watch = self.pg, self.know, self.line, self.watch
        out = []
        while True:
            k0 = line.top("assertive") or line.top("polite")
            if k0 is None:
                return out
            r0, n0 = k0
            rr, cur = watch.now(n0)
            c0 = cur if rr == r0 else None
            u = unit.unit(pg, know, k0, c0)
            if u is not None:
                words, group = self._group(u)
            else:
                group = [(k0, c0)]
                words = c0[0] if c0 is not None else "removed " + know.expect(k0)[0]
            carried = {k: (c, line.age[k]) for k, c in group}
            for k in carried:
                line.drop(k)
            if not words:
                for k, (v, _age) in carried.items():
                    know.believe(k, v)
                continue
            for k, v in carried.items():
                know.carry[k] = v
                know._note(k)
            out.append((look.loudness(pg, r0), words, carried))

    def step(self, t, recs):
        know, line, watch = self.know, self.line, self.watch
        out = []
        if self.play is not None and self.play[1] == t:
            for k, (v, _age) in self.now_keys.items():
                if k in know.carry:
                    del know.carry[k]
                    know.believe(k, v)
            self.play = None
        watch.scan(recs, t)
        if self.play is not None and self.play[0] == "polite" and line.top("assertive"):
            out.append(say.cut(t))
            self.play = None
            self.queue = []
            for k, (_v, age) in know.cut().items():
                watch.settle(k, t, age=age)
        if self.play is None:
            if not self.queue:
                self.queue = self._prepare()
            if self.queue:
                cls, words, carried = self.queue.pop(0)
                self.now_keys = carried
                self.play = (cls, t + len(words.split(" ")))
                out.append(say.start(t, cls, words))
        return out
'''


DOC_ORDER_LINE_TOP = '''    def top(self, cls):
        pile = self.heap[cls]
        got = []
        while pile:
            age, n, r = pile[0]
            k = (r, n)
            if self.age.get(k) == age and k not in self.held and self.cls.get(k) == cls:
                if got and age != got[0][0]:
                    break
                got.append(heapq.heappop(pile))
                continue
            heapq.heappop(pile)
        for e in got:
            heapq.heappush(pile, e)
        if not got:
            return None
        _pos, n, r = min((self._pos(n), n, r) for _age, n, r in got)
        return (r, n)

    def _pos(self, n):
        pg = self.pg
        path = []
        x = n
        while pg.up(x) is not None:
            p = pg.up(x)
            path.append(list(pg.kids(p)).index(x))
            x = p
        return tuple(reversed(path))
'''


def _readings():
    R = {}
    R["learn-at-start"] = _one("voice.py", [(
        "            know.take(carried)\n",
        "            for k, (v, _age) in carried.items():\n"
        "                know.believe(k, v)\n"
        "            know.take({})\n")])
    R["queue-strings"] = {"voice.py": QUEUE_VOICE}
    R["atomic-region-only"] = _one("unit.py", [(
        "    x = s\n    while True:\n        v = look.atomic(pg, x)\n        if v == \"true\":\n"
        "            return x\n        if v == \"false\" or x == r:\n            return None\n"
        "        x = pg.up(x)\n",
        "    return r if look.atomic(pg, r) == \"true\" else None\n")])
    R["atomic-false-ignored"] = _one("unit.py", [(
        "        if v == \"false\" or x == r:\n", "        if x == r:\n")])
    R["relevant-nearest"] = _one("watch.py", [
        ("    def settle(self, k, t, age=None, where=None):\n",
         "    def near(self, k, c):\n"
         "        r = k[0]\n"
         "        s = unit.start(self.pg, self.know, k, c)\n"
         "        x = r if s is None else s\n"
         "        while True:\n"
         "            if self.pg.attr(x, \"aria-relevant\") is not None:\n"
         "                return look.relevant(self.pg, x)\n"
         "            if x == r:\n"
         "                return look.BASE\n"
         "            x = self.pg.up(x)\n\n"
         "    def settle(self, k, t, age=None, where=None):\n"),
        ("kind(c, e) not in look.relevant(pg, r)", "kind(c, e) not in self.near(k, c)"),
    ])
    R["removal-at-region"] = _one("unit.py", [(
        "    a = know.expect(k)[1]\n    shown, reg = look.place(pg, a)\n    if shown and reg == r:\n"
        "        return a\n    return None\n",
        "    return None\n")])
    R["anchor-follows-move"] = _one("watch.py", [(
        "        if not differs(c, e):\n            line.drop(k)\n            return\n",
        "        if not differs(c, e):\n"
        "            if c is not None and e is not None and c[1] != e[1] and k not in know.carry:\n"
        "                know.believe(k, c)\n"
        "            line.drop(k)\n            return\n")])
    R["busy-region-only"] = _one("unit.py", [(
        "    s = start(pg, know, k, cur)\n    x = r if s is None else s\n    while True:\n"
        "        if look.busy(pg, x):\n",
        "    return look.busy(pg, r)\n    x = r\n    while True:\n        if look.busy(pg, x):\n")])
    R["cut-to-back"] = _one("voice.py", [(
        "                watch.settle(k, t, age=age)\n", "                watch.settle(k, t, age=t)\n")])
    R["assertive-cuts-assertive"] = _one("voice.py", [(
        "        if self.play is not None and self.play[0] == \"polite\" and line.top(\"assertive\"):\n",
        "        if self.play is not None and line.top(\"assertive\"):\n")])
    R["belief-by-node"] = _one("watch.py", [(
        "        e = know.expect(k)\n        if not differs(c, e):\n",
        "        e = know.expect(k)\n"
        "        if c is None and e is not None and rr is not None and rr != r and cur[0] == e[0]:\n"
        "            know.believe(k, None)\n"
        "            know.believe((rr, n), cur)\n"
        "            line.drop(k)\n"
        "            line.drop((rr, n))\n"
        "            return\n"
        "        if e is None and c is not None:\n"
        "            for q in know.regions_of(n):\n"
        "                o = know.expect((q, n))\n"
        "                if q != r and o is not None and o[0] == c[0]:\n"
        "                    know.believe((q, n), None)\n"
        "                    know.believe(k, c)\n"
        "                    line.drop(k)\n"
        "                    line.drop((q, n))\n"
        "                    return\n"
        "        if not differs(c, e):\n")])
    R["off-transparent"] = _many({
        "look.py": [
            ("            if reg is None and pg.attr(x, \"aria-live\") is not None:\n",
             "            if reg is None and pg.attr(x, \"aria-live\") in POL:\n"),
            ("        if not pg.is_text(x) and pg.attr(x, \"aria-live\") is not None:\n",
             "        if not pg.is_text(x) and pg.attr(x, \"aria-live\") in POL:\n"),
        ],
        "watch.py": [
            ("            if pg.attr(x, \"aria-live\") is not None:\n                r = x\n",
             "            if pg.attr(x, \"aria-live\") in look.POL:\n                r = x\n"),
        ],
    })
    R["absorb-keeps-carry"] = _one("know.py", [(
        "        self.carry.pop(k, None)\n        self.believe(k, v)\n",
        "        self.believe(k, v)\n")])
    R["hidden-false-reveals"] = _many({
        "look.py": [(
            "    reg = None\n    x = n\n    while x is not None:\n        if not pg.is_text(x):\n"
            "            if hides(pg, x):\n                return False, None\n",
            "    reg = None\n    fixed = False\n    x = n\n    while x is not None:\n"
            "        if not pg.is_text(x):\n"
            "            if not fixed and pg.attr(x, \"aria-hidden\") == \"false\":\n"
            "                fixed = True\n"
            "            elif not fixed and hides(pg, x):\n                return False, None\n")],
        "watch.py": [(
            "        todo = [(0, None)]\n        while todo:\n            x, r = todo.pop()\n"
            "            if pg.is_text(x):\n                if r is not None:\n",
            "        todo = [(0, None, False)]\n        while todo:\n            x, r, hid = todo.pop()\n"
            "            if pg.is_text(x):\n                if r is not None and not hid:\n"),
            ("            if look.hides(pg, x):\n                continue\n"
             "            if pg.attr(x, \"aria-live\") is not None:\n                r = x\n"
             "            for y in pg.kids(x):\n                todo.append((y, r))\n",
             "            if pg.attr(x, \"aria-hidden\") == \"false\":\n                hid = False\n"
             "            elif look.hides(pg, x):\n                hid = True\n"
             "            if pg.attr(x, \"aria-live\") is not None:\n                r = x\n"
             "            for y in pg.kids(x):\n                todo.append((y, r, hid))\n")],
    })
    R["tie-doc-order"] = _many({
        "line.py": [(
            _src("line.py")[_src("line.py").index("    def top(self, cls):"):],
            DOC_ORDER_LINE_TOP)],
        "voice.py": [(
            "        self.line = Line()\n",
            "        self.line = Line()\n        self.line.pg = pg\n")],
    })
    R["timing-plus-one"] = _one("voice.py", [(
        "t + len(words.split(\" \")))", "t + len(words.split(\" \")) + 1)")])
    R["empty-says"] = _one("voice.py", [(
        "            if not words:\n                for k, (v, _age) in carried.items():\n"
        "                    know.believe(k, v)\n                continue\n", "")])
    R["unit-carries-held"] = _one("voice.py", [
        ("            if line.ready(k) and unit.unit(pg, know, k, cur) == u:\n",
         "            if k in line.age and unit.unit(pg, know, k, cur) == u:\n"),
        ("                if line.ready(k) and unit.unit(pg, know, k, None) == u:\n",
         "                if k in line.age and unit.unit(pg, know, k, None) == u:\n"),
    ])
    R["busy-above-region"] = _one("unit.py", [(
        "    while True:\n        if look.busy(pg, x):\n            return True\n        if x == r:\n"
        "            return False\n        x = pg.up(x)\n",
        "    while x is not None:\n        if look.busy(pg, x):\n            return True\n"
        "        x = pg.up(x)\n    return False\n")])
    R["age-resets-on-edit"] = _one("watch.py", [
        ("        self.line = line\n", "        self.line = line\n        self.last = {}\n"),
        ("        if age is None:\n            age = line.age.get(k, t)\n",
         "        cval = c[0] if c is not None else None\n"
         "        if age is None:\n"
         "            age = line.age.get(k, t) if self.last.get(k, cval) == cval else t\n"
         "        self.last[k] = cval\n"),
    ])
    R["irrelevant-kept"] = _one("watch.py", [(
        "        if not look.voicing(pg, r) or kind(c, e) not in look.relevant(pg, r):\n"
        "            know.absorb(k, c)\n            line.drop(k)\n            return\n",
        "        if not look.voicing(pg, r):\n            know.absorb(k, c)\n            line.drop(k)\n"
        "            return\n"
        "        if kind(c, e) not in look.relevant(pg, r):\n"
        "            line.put(k, line.age.get(k, t), look.loudness(pg, r), True,\n"
        "                     e[1] if c is None else None)\n"
        "            return\n")])
    R["silent-kept"] = _one("watch.py", [(
        "        if not look.voicing(pg, r) or kind(c, e) not in look.relevant(pg, r):\n"
        "            know.absorb(k, c)\n            line.drop(k)\n            return\n",
        "        if not look.voicing(pg, r):\n"
        "            line.put(k, line.age.get(k, t), \"polite\", True, e[1] if c is None else None)\n"
        "            return\n"
        "        if kind(c, e) not in look.relevant(pg, r):\n"
        "            know.absorb(k, c)\n            line.drop(k)\n            return\n")])
    R["cut-when-held"] = _one("voice.py", [(
        "        if self.play is not None and self.play[0] == \"polite\" and line.top(\"assertive\"):\n",
        "        if self.play is not None and self.play[0] == \"polite\" and any(\n"
        "                line.cls[k] == \"assertive\" for k in line.age):\n")])
    R["finish-after-cut"] = _one("voice.py", [
        ("        if self.play is not None and self.play[1] == t:\n            know.finish()\n"
         "            self.play = None\n\n        watch.scan(recs, t)\n",
         "        watch.scan(recs, t)\n"),
        ("        while self.play is None:\n            k0 = self._pick()\n",
         "        if self.play is not None and self.play[1] == t:\n            know.finish()\n"
         "            self.play = None\n\n"
         "        while self.play is None:\n            k0 = self._pick()\n"),
    ])
    R["oldest-across-classes"] = _one("voice.py", [(
        "        return self.line.top(\"assertive\") or self.line.top(\"polite\")\n",
        "        a, p = self.line.top(\"assertive\"), self.line.top(\"polite\")\n"
        "        if a is None or p is None:\n            return a or p\n"
        "        ka = (self.line.age[a], a[1], a[0])\n"
        "        kp = (self.line.age[p], p[1], p[0])\n"
        "        return a if ka <= kp else p\n")])
    R["busy-any-value"] = _one("look.py", [(
        "    return pg.attr(e, \"aria-busy\") == \"true\"\n",
        "    return pg.attr(e, \"aria-busy\") is not None\n")])
    R["relevant-bogus-empty"] = _one("look.py", [(
        "    return frozenset(got) if got else BASE\n",
        "    if pg.attr(r, \"aria-relevant\") is None:\n        return BASE\n"
        "    return frozenset(got)\n")])
    R["region-hidden-voiced"] = _one("look.py", [(
        "    return pg.attr(r, \"aria-live\") in POL and place(pg, r)[0]\n",
        "    return pg.attr(r, \"aria-live\") in POL\n")])
    R["hidden-false-shows"] = _one("look.py", [(
        "    return pg.attr(e, \"hidden\") is not None or pg.attr(e, \"aria-hidden\") == \"true\"\n",
        "    return pg.attr(e, \"hidden\") not in (None, \"false\") or "
        "pg.attr(e, \"aria-hidden\") == \"true\"\n")])
    shipped = {}
    for p in PARTS:
        with open(os.path.join(SHIPPED, p), encoding="utf-8") as fh:
            shipped[p] = fh.read()
    R["event-driven"] = shipped
    return R


READINGS = _readings()

_BUILT = {}


def _load(policy):
    policy = os.path.abspath(policy)
    got = _BUILT.get(policy)
    if got is not None:
        return got
    room = tempfile.mkdtemp(prefix="hcr-reading-")
    pkg = "sr%d" % len(_BUILT)
    dst = os.path.join(room, pkg)
    os.makedirs(dst)
    for f in FROZEN:
        shutil.copy(os.path.join(SHIPPED, f), os.path.join(dst, f))
    for f in PARTS:
        shutil.copy(os.path.join(policy, f), os.path.join(dst, f))
    sys.path.insert(0, room)
    script = importlib.import_module(pkg + ".script")
    page = importlib.import_module(pkg + ".page")
    voice = importlib.import_module(pkg + ".voice")
    got = (script, page, voice)
    _BUILT[policy] = got
    return got


def run(policy, text):
    script, page, voice = _load(policy)
    try:
        last, ticks = script.parse(text)
        pg = page.Page()
        for op in ticks[0]:
            pg.apply(op)
        rd = voice.Reader(pg)
        rd.load()
        out = []
        for t in range(1, last + 1):
            recs = [pg.apply(op) for op in ticks.get(t, ())]
            out.extend(rd.step(t, recs))
        return tuple(out)
    except Exception as exc:
        return ("ERROR", type(exc).__name__)


def enumerated():
    return [(n, "\n".join(cases.prog(n)) + "\n") for n in cases.ORDER]


def generated(n):
    fams = [f for f, big in gen.FAMILIES if not big]
    out = []
    i = 0
    while len(out) < n:
        f = fams[i % len(fams)]
        out.append(("%s-%d" % (f, i), "\n".join(gen.one("readings", f, i)) + "\n"))
        i += 1
    return out
