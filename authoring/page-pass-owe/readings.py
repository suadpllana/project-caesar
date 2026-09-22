"""Wrong readings of the list service, as the files they would replace in the reference.

`tools/readingcheck.py` drives each of these against the enumerated set and says whether
some case already fails it. A reading nothing separates is not a wrong reading at all - it
is either a correct alternative or a hole in the generated space.

Every patch asserts that it fired. A replacement that matched nothing would leave the
reference in place and report a wrong reading as separated by every case, which is the
quietest way to ship a check that checks nothing.
"""

import hashlib
import importlib
import random
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TASK = REPO / "tasks" / "page-pass-owe"
REFERENCE = TASK / "solution"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")

sys.path.insert(0, str(TASK / "tests"))
import cases as _cases  # noqa: E402
import gen as _gen  # noqa: E402


# --------------------------------------------------------------------------- patches


def _src(name):
    return (REFERENCE / (name + ".py")).read_text(encoding="utf-8")


def patch(name, *pairs):
    """The reference file with each (old, new) applied, once, and only if it fired."""
    text = _src(name)
    for old, new in pairs:
        if text.count(old) != 1:
            raise AssertionError("%s: %d matches for %r" % (name, text.count(old), old[:60]))
        text = text.replace(old, new)
    return text


def patch_all(name, old, new, want):
    text = _src(name)
    if text.count(old) != want:
        raise AssertionError("%s: %d matches for %r, wanted %d"
                             % (name, text.count(old), old[:60], want))
    return text.replace(old, new)


LED_QUEUE = """    while len(out) < sc.n and left > 0:
        i = owe.front(sc)
        if i is None:
            break
        w = st.rows[i][2]
        if w <= left:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left -= w
        elif not out:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left = 0
        else:
            break
"""

LED_FIT = """    for i in list(sc.led):
        if len(out) >= sc.n or left <= 0:
            break
        w = st.rows[i][2]
        if w <= left:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left -= w
        elif not out:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left = 0
"""

LED_NO_EMPTY = """    while len(out) < sc.n and left > 0:
        i = owe.front(sc)
        if i is None:
            break
        w = st.rows[i][2]
        if w <= left:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            out.append(i)
            left -= w
        else:
            break
"""

SCAN_EMPTY = """        if not out:
            at += 1
            scr.looked(sc, pl)
            scr.gave(sc, i)
            out.append(i)
            left = 0
            continue
"""

SCAN_SKIP = """        if scr.had(sc, i):
            at += 1
            scr.looked(sc, pl)
            continue
"""

SCAN_STEP = """        if owe.held(st) + w <= st.hold:
            at += 1
            scr.looked(sc, pl)
            owe.owe(st, sc, i)
            over += w
            continue
        break
"""

OWED_HERE = """    if i in sc.got:
        return False
"""

SEQ_TIE_HIGH = '''import bisect


class View(object):
    def __init__(self):
        self.by_tag = {}

    def places(self, g):
        v = self.by_tag.get(g)
        if v is None:
            v = []
            self.by_tag[g] = v
        return v

    def put(self, k, i, g):
        v = self.places(g)
        v.append((k, i))
        v.sort(key=lambda p: (p[0], -p[1]))

    def take(self, k, i, g):
        v = self.places(g)
        if (k, i) in v:
            v.remove((k, i))

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        at = 0
        while at < len(v) and (v[at][0], -v[at][1]) <= (mk[0], -mk[1]):
            at += 1
        return v, at


_ = bisect
'''


SEQ_BY_ID = '''import bisect


class View(object):
    def __init__(self):
        self.by_tag = {}

    def places(self, g):
        v = self.by_tag.get(g)
        if v is None:
            v = []
            self.by_tag[g] = v
        return v

    def put(self, k, i, g):
        v = self.places(g)
        v.append((k, i))
        v.sort(key=lambda p: p[1])

    def take(self, k, i, g):
        v = self.places(g)
        if (k, i) in v:
            v.remove((k, i))

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        at = 0
        while at < len(v) and v[at][1] <= mk[1]:
            at += 1
        return v, at


_ = bisect
'''

SEQ_ONE_VIEW = '''import bisect


class View(object):
    def __init__(self):
        self.all = []

    def places(self, g):
        return self.all

    def put(self, k, i, g):
        bisect.insort(self.all, (k, i))

    def take(self, k, i, g):
        at = bisect.bisect_left(self.all, (k, i))
        if at < len(self.all) and self.all[at] == (k, i):
            del self.all[at]

    def start(self, g, mk):
        if not self.all:
            return (), 0
        if mk is None:
            return self.all, 0
        return self.all, bisect.bisect_right(self.all, mk)
'''

OWE_KEEPS_PLACE = '''def held(st):
    return st.owed


def owed_here(st, sc, i):
    r = st.rows.get(i)
    if r is None:
        return False
    if r[1] != sc.g:
        return False
    if i in sc.got:
        return False
    return sc.mk is not None and (r[0], i) <= sc.mk


def owe(st, sc, i):
    if i in sc.led:
        return
    w = st.rows[i][2]
    sc.led[i] = w
    st.owed += w
    order = getattr(sc, "once", None)
    if order is None:
        order = []
        sc.once = order
    if i not in order:
        order.append(i)


def unowe(st, sc, i):
    w = sc.led.pop(i, None)
    if w is not None:
        st.owed -= w


def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)


def front(sc):
    for i in getattr(sc, "once", ()):
        if i in sc.led:
            return i
    return None


def standing(sc):
    return len(sc.led)


def weight(sc):
    return sum(sc.led.values())
'''


READINGS = {
    # -- the everyday cases, and the overshoot each of them rejects ----------------------
    "scan-rows-inclusive": {"pg.py": patch_all("pg", "len(out) < sc.n", "len(out) <= sc.n", 2)},
    "view-ignores-tag": {"seq.py": SEQ_ONE_VIEW},
    "order-by-id": {
        "seq.py": SEQ_BY_ID,
        "owe.py": patch("owe", ("return sc.mk is not None and (r[0], i) <= sc.mk",
                                "return sc.mk is not None and i <= sc.mk[1]")),
    },
    "add-never-owes": {"edt.py": patch("edt", ("""    st.view.put(k, i, g)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def move""", """    st.view.put(k, i, g)


def move"""))},
    "tag-no-join": {"edt.py": patch("edt", ("""    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)""", """    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)"""))},
    "owe-keeps-place": {"owe.py": OWE_KEEPS_PLACE},
    # -- the order two rows sharing a key come out in -----------------------------------
    "order-tie-high": {
        "seq.py": SEQ_TIE_HIGH,
        "owe.py": patch("owe", ("return sc.mk is not None and (r[0], i) <= sc.mk",
                                "return sc.mk is not None and (r[0], -i) <= "
                                "(sc.mk[0], -sc.mk[1])")),
    },

    # -- the ledger phase ----------------------------------------------------------------
    "led-first-fit": {"pg.py": patch("pg", (LED_QUEUE, LED_FIT))},
    "led-low-id": {"owe.py": patch("owe", ("""def front(sc):
    for i in sc.led:
        return i
    return None
""", """def front(sc):
    if not sc.led:
        return None
    return min(sc.led)
"""))},
    "led-newest": {"owe.py": patch("owe", ("""def front(sc):
    for i in sc.led:
        return i
    return None
""", """def front(sc):
    last = None
    for i in sc.led:
        last = i
    return last
"""))},

    # -- the empty-page rule ---------------------------------------------------------------
    "empty-none": {"pg.py": patch("pg", (LED_QUEUE, LED_NO_EMPTY), (SCAN_EMPTY, ""))},
    "empty-keeps-weight": {"pg.py": patch_all("pg", "            left = 0\n",
                                              "            left -= 0\n", 2)},

    # -- the scan and its stops ---------------------------------------------------------------
    "scan-stop-misfit": {"pg.py": patch("pg", (SCAN_STEP, "        break\n"))},
    "scan-no-over": {"pg.py": patch("pg", ("while len(out) < sc.n and left > 0 and over < sc.c:",
                                           "while len(out) < sc.n and left > 0:"))},
    "scan-over-strict": {"pg.py": patch("pg", ("and over < sc.c:", "and over <= sc.c:"))},
    "scan-fit-strict": {"pg.py": patch_all("pg", "        if w <= left:\n",
                                           "        if w < left:\n", 2)},
    "scan-rehands-moved": {"pg.py": patch("pg", (SCAN_SKIP, ""))},

    # -- the mark ------------------------------------------------------------------------------
    "mark-on-give": {"pg.py": patch("pg", (SCAN_SKIP, """        if scr.had(sc, i):
            at += 1
            continue
"""), (SCAN_STEP, """        if owe.held(st) + w <= st.hold:
            at += 1
            owe.owe(st, sc, i)
            over += w
            continue
        break
"""))},
    "mark-on-drain": {"pg.py": patch("pg", (LED_QUEUE, """    while len(out) < sc.n and left > 0:
        i = owe.front(sc)
        if i is None:
            break
        w = st.rows[i][2]
        if w <= left:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            scr.looked(sc, (st.rows[i][0], i))
            out.append(i)
            left -= w
        elif not out:
            owe.unowe(st, sc, i)
            scr.gave(sc, i)
            scr.looked(sc, (st.rows[i][0], i))
            out.append(i)
            left = 0
        else:
            break
"""))},

    # -- the hold -------------------------------------------------------------------------------
    "hold-per-scroll": {"pg.py": patch("pg", ("if owe.held(st) + w <= st.hold:",
                                              "if owe.weight(sc) + w <= st.hold:"))},
    "hold-strict": {"pg.py": patch("pg", ("if owe.held(st) + w <= st.hold:",
                                          "if owe.held(st) + w < st.hold:"))},
    "hold-blocks-edits": {"owe.py": patch("owe", ("""def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)
""", """def settle(st, sc, i):
    if owed_here(st, sc, i) and st.owed + st.rows[i][2] <= st.hold:
        owe(st, sc, i)
    else:
        unowe(st, sc, i)
"""))},

    # -- owed membership ---------------------------------------------------------------------------
    "owe-log": {"owe.py": patch("owe", ("""def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
    else:
        unowe(st, sc, i)
""", """def settle(st, sc, i):
    if owed_here(st, sc, i):
        owe(st, sc, i)
"""))},
    "owe-ignores-memory": {"owe.py": patch("owe", (OWED_HERE, ""))},
    "owe-strict-mark": {"owe.py": patch("owe", ("(r[0], i) <= sc.mk", "(r[0], i) < sc.mk"))},
    "add-always-owes": {"edt.py": patch("edt", ("""    st.view.put(k, i, g)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def move""", """    st.view.put(k, i, g)
    for sc in scr.reading(st, g):
        owe.owe(st, sc, i)


def move"""))},
    "move-no-settle": {"edt.py": patch("edt", ("""    st.view.put(k, i, r[1])
    for sc in scr.reading(st, r[1]):
        owe.settle(st, sc, i)
""", """    st.view.put(k, i, r[1])
"""))},
    "drop-keeps-owed": {"edt.py": patch("edt", ("""    st.view.take(r[0], i, r[1])
    for sc in scr.reading(st, r[1]):
        owe.unowe(st, sc, i)
""", """    st.view.take(r[0], i, r[1])
"""))},
    "tag-keeps-owed": {"edt.py": patch("edt", ("""    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)
""", ""))},

    # -- the delivery memory ---------------------------------------------------------------------------
    "seen-across-scrolls": {"scr.py": patch(
        "scr", ("        self.by_tag = {}\n        self.owed = 0\n",
                "        self.by_tag = {}\n        self.owed = 0\n        self.seen = set()\n"),
        ("    sc = Scroll(s, g, n, c)\n    st.scrolls[s] = sc\n",
         "    sc = Scroll(s, g, n, c)\n    sc.got = st.seen\n    st.scrolls[s] = sc\n"))},
    "seen-clears-on-tag": {"edt.py": patch("edt", ("""    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)
""", """    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)
            sc.got.discard(i)
"""))},

    # -- the closing report -----------------------------------------------------------------------------
    "rep-unhanded-is-owed": {"rep.py": patch("rep", ("""        u = 0
        for pl in st.view.places(sc.g):
            if pl[1] not in sc.got:
                u += 1
""", "        u = owe.standing(sc)\n"))},
    "rep-handed-in-view": {"rep.py": patch("rep", (
        "lines.append((s, len(sc.got), owe.standing(sc), u))",
        "lines.append((s, sum(1 for pl in st.view.places(sc.g) if pl[1] in sc.got),"
        " owe.standing(sc), u))"))},
    "rep-total-unhanded": {"rep.py": patch("rep", (
        "        total += owe.weight(sc)\n",
        "        for pl in st.view.places(sc.g):\n"
        "            if pl[1] not in sc.got:\n"
        "                total += st.rows[pl[1]][2]\n"))},
}


# --------------------------------------------------------------------------- driving

_ROOT = Path(tempfile.mkdtemp(prefix="ppo-readings-"))
_LOADED = {}


def _module(policy):
    """Import one policy directory as its own package, once, and keep it."""
    key = str(policy)
    if key in _LOADED:
        return _LOADED[key]
    tag = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    home = _ROOT / tag
    shutil.copytree(TASK / "environment" / "app_src", home)
    for part in PARTS:
        one = Path(policy) / (part + ".py")
        if one.is_file():
            shutil.copyfile(one, home / "lst" / (part + ".py"))
    pkg = "lst_" + tag
    (home / "lst").rename(home / pkg)
    for f in sorted((home / pkg).glob("*.py")) + [home / "run_lst.py"]:
        f.write_text(f.read_text(encoding="utf-8").replace("from lst import",
                                                           "from %s import" % pkg),
                     encoding="utf-8")
    driver = "run_" + tag
    (home / "run_lst.py").rename(home / (driver + ".py"))
    sys.path.insert(0, str(home))
    _LOADED[key] = importlib.import_module(driver)
    return _LOADED[key]


def run(policy, text):
    return _module(policy).run(text)


def enumerated():
    return [(name, "\n".join(_cases.prog(name)) + "\n") for name in _cases.ORDER]


def generated(n):
    out = []
    fams = _gen.SMALL
    for j in range(n):
        fam = fams[j % len(fams)]
        rng = random.Random("readings/%s/%d" % (fam, j))
        out.append(("%s-%d" % (fam, j), "\n".join(_gen._prog(rng, fam)) + "\n"))
    return out
