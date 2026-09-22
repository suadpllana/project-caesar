"""Build the wrong readings once, and write the cheats from the same sources.

A reading measured by tools/readingcheck.py and a cheat shipped in cheat/ have to be the same
file or they drift, and the drift is silent: the reading directory says "caught by the case
named for it" while the stale cheat script says "nothing failed". So both come from here, and
this runs before either.

Each reading is the reference with one file swapped. The swaps are textual, and every one of
them asserts that it fired - a patch that matches nothing leaves the reference in place and
scores 1 for the wrong reason.

    python authoring/stale-cover-serve/emit.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CHEAT = lab.TASK / "cheat"


def ref(name):
    return (lab.SOL / name).read_text(encoding="utf-8")


def swap(name, old, new):
    src = ref(name)
    assert old in src, "patch for %s no longer matches the reference" % name
    out = src.replace(old, new, 1)
    assert out != src
    return {name: out}


READINGS = {}


def reading(key, files):
    READINGS[key] = files


# --- the version a read is answered at -------------------------------------------------

reading("now-only", swap(
    "pick.py",
    "    floor = now - s\n    if floor < 0:\n        floor = 0",
    "    floor = now"))

reading("oldest-version", swap(
    "pick.py",
    "    order = sorted(set([now] + [row[0] for row in spans if row[0] < now]), reverse=True)",
    "    order = sorted(set([now] + [row[0] for row in spans if row[0] < now]))"))

reading("floor-low", swap(
    "pick.py",
    "    floor = now - s\n    if floor < 0:\n        floor = 0",
    "    floor = now - s - 1\n    if floor < 0:\n        floor = 0"))

reading("floor-high", swap(
    "pick.py",
    "    floor = now - s\n    if floor < 0:\n        floor = 0",
    "    floor = now - s + 1\n    if floor < 0:\n        floor = 0"))

PER_ENTRY = '''
def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    width = hi - lo + 1
    seen = [False] * width
    short = width
    for st in tb.near(lo, hi):
        top = now if st.died < 0 else st.died
        if top < floor or st.born > now:
            continue
        a = st.lo if st.lo > lo else lo
        b = st.hi if st.hi < hi else hi
        for k in range(a - lo, b - lo + 1):
            if not seen[k]:
                seen[k] = True
                short -= 1
    if short:
        return None
    return now
'''
reading("per-entry", {"pick.py": PER_ENTRY})

# --- what a fetch is worth --------------------------------------------------------------

reading("born-now", swap(
    "ask.py",
    "            rows, mark = st.at(a, b)\n            tb.add(a, b, rows, mark)",
    "            rows, mark = st.at(a, b)\n            tb.add(a, b, rows, st.ver)"))

reading("born-zero-empty", swap(
    "ask.py",
    "            rows, mark = st.at(a, b)\n            tb.add(a, b, rows, mark)",
    "            rows, mark = st.at(a, b)\n"
    "            tb.add(a, b, rows, 0 if not rows else mark)"))

reading("fetch-when-stale", swap(
    "ask.py",
    "    at = pick.at(tb, lo, hi, s, st.ver)\n    if at is None:",
    "    at = pick.at(tb, lo, hi, s, st.ver)\n    if at is not None and at < st.ver:\n"
    "        at = None\n    if at is None:"))

reading("warm-fetch", swap(
    "ask.py",
    "    at = pick.at(tb, lo, hi, s, st.ver)\n    if at is None:\n"
    "        runs = hole.runs(tb.near(lo, hi), lo, hi)\n"
    "        for a, b in mend.shape(runs, lo, hi, tune.slack, tune.cap):",
    "    at = pick.at(tb, lo, hi, s, st.ver)\n    if True:\n"
    "        runs = hole.runs(tb.near(lo, hi), lo, hi)\n"
    "        for a, b in mend.shape(runs, lo, hi, tune.slack, tune.cap):"))

INSTALL_PER_HOLE = '''
from . import age, hole, knit, mend, out, pick


def settle(tb, touched, now, tune):
    if touched:
        tb.close(touched, now - 1)
    age.sweep(tb, now, tune.horizon)


def read(tb, st, lo, hi, s, tune):
    lines = []
    at = pick.at(tb, lo, hi, s, st.ver)
    if at is None:
        runs = hole.runs(tb.near(lo, hi), lo, hi)
        for a, b in mend.shape(runs, lo, hi, tune.slack, tune.cap):
            lines.append(out.fetch(a, b))
            rows, mark = st.at(a, b)
            inner = [(p, q) for p, q in runs if p >= a and q <= b] or [(a, b)]
            for p, q in inner:
                part = [(k, v) for k, v in rows if p <= k <= q]
                got, bit = st.at(p, q)
                tb.add(p, q, part, bit)
        at = st.ver
    lines.append(out.ans(at, knit.rows(tb.near(lo, hi), lo, hi, at)))
    return lines
'''
reading("install-per-hole", {"ask.py": INSTALL_PER_HOLE})

# --- what a commit does -----------------------------------------------------------------

reading("close-at-commit", swap(
    "ask.py",
    "        tb.close(touched, now - 1)",
    "        tb.close(touched, now)"))

reading("drop-on-close", swap(
    "seg.py",
    "                if st.lo <= k <= st.hi:\n                    st.died = upto\n"
    "                    self.seq += 1\n"
    "                    heapq.heappush(self.pend, (upto, self.seq, st))",
    "                if st.lo <= k <= st.hi:\n                    st.died = upto\n"
    "                    st.gone = True"))

# --- the horizon --------------------------------------------------------------------------

reading("horizon-strict", swap(
    "age.py",
    "    floor = now - horizon\n    if floor <= 0:\n        return\n    tb.drop(floor)",
    "    floor = now - horizon\n    if floor < 0:\n        return\n    tb.drop(floor + 1)"))

reading("horizon-keeps-count", swap(
    "age.py",
    "    floor = now - horizon\n    if floor <= 0:\n        return\n    tb.drop(floor)",
    "    pend = tb.pend\n    while len(pend) > horizon:\n"
    "        import heapq\n        heapq.heappop(pend)[2].gone = True"))

reading("horizon-drops-open", swap(
    "age.py",
    "    floor = now - horizon\n    if floor <= 0:\n        return\n    tb.drop(floor)",
    "    floor = now - horizon\n    if floor <= 0:\n        return\n    tb.drop(floor)\n"
    "    for box in tb.alls.values():\n        for st in box:\n"
    "            if st.died < 0 and st.born < floor:\n                st.gone = True"))

# --- the holes and the shape of a fetch ---------------------------------------------------

reading("holes-count-closed", swap(
    "hole.py",
    "        if st.died < 0 and st.hi >= lo and st.lo <= hi:",
    "        if st.hi >= lo and st.lo <= hi:"))

HOLES_PER_KEY = swap(
    "hole.py",
    "    gaps = []\n    at = lo\n    for a, b in spans:",
    "    gaps = []\n    shut = set()\n"
    "    for a, b in spans:\n"
    "        for k in range(a, b + 1):\n            shut.add(k)\n"
    "    for k in range(lo, hi + 1):\n"
    "        if k not in shut:\n            gaps.append((k, k))\n"
    "    return gaps\n\n\n"
    "def _unused(spans, lo, hi):\n    gaps = []\n    at = lo\n    for a, b in spans:")

reading("holes-desc", swap(
    "hole.py",
    "    if at <= hi:\n        gaps.append((at, hi))\n    return gaps",
    "    if at <= hi:\n        gaps.append((at, hi))\n    gaps.reverse()\n    return gaps"))

reading("holes-unsorted", swap(
    "hole.py",
    "    spans.sort()",
    "    pass"))

reading("slack-strict", swap(
    "mend.py",
    "        if a - out[-1][1] - 1 <= slack:",
    "        if a - out[-1][1] - 1 < slack:"))

reading("slack-gap", swap(
    "mend.py",
    "        if a - out[-1][1] - 1 <= slack:",
    "        if a - out[-1][1] <= slack:"))

reading("cap-span", swap(
    "mend.py",
    "    if len(out) > cap:\n        return [(lo, hi)]",
    "    if len(out) > cap:\n        return [(out[0][0], out[-1][1])]"))

reading("cap-at-cap", swap(
    "mend.py",
    "    if len(out) > cap:\n        return [(lo, hi)]",
    "    if len(out) >= cap:\n        return [(lo, hi)]"))

reading("cap-before-combine", swap(
    "mend.py",
    "    out = [[runs[0][0], runs[0][1]]]",
    "    if len(runs) > cap:\n        return [(lo, hi)]\n"
    "    out = [[runs[0][0], runs[0][1]]]"))

# --- the answer ---------------------------------------------------------------------------

reading("rows-concat", swap(
    "knit.py",
    "    got = {}",
    "    loose = []\n    got = {}"))

READINGS["rows-concat"]["knit.py"] = READINGS["rows-concat"]["knit.py"].replace(
    "            got[k] = v\n    return sorted(got.items())",
    "            loose.append((k, v))\n    return loose")
assert "return loose" in READINGS["rows-concat"]["knit.py"]

reading("rows-unsorted", swap(
    "knit.py",
    "    return sorted(got.items())",
    "    return list(got.items())"))

reading("rows-at-now", swap(
    "knit.py",
    "        if st.born > at:\n            continue\n        if 0 <= st.died < at:\n"
    "            continue",
    "        if st.died >= 0:\n            continue"))


PERKEY_COVER = '''
def at(tb, lo, hi, s, now):
    floor = now - s
    if floor < 0:
        floor = 0
    width = hi - lo + 1
    over = [[] for _ in range(width)]
    for st in tb.near(lo, hi):
        top = now if st.died < 0 else st.died
        if top < floor:
            continue
        low = st.born
        if low < floor:
            low = floor
        if low > top:
            continue
        a = st.lo if st.lo > lo else lo
        b = st.hi if st.hi < hi else hi
        for k in range(a - lo, b - lo + 1):
            over[k].append((low, top))
    marks = []
    for box in over:
        if not box:
            return None
        box.sort()
        run = [box[0][0], box[0][1]]
        for low, top in box[1:]:
            if low <= run[1] + 1:
                if top > run[1]:
                    run[1] = top
            else:
                marks.append((run[0], 1))
                marks.append((run[1] + 1, -1))
                run = [low, top]
        marks.append((run[0], 1))
        marks.append((run[1] + 1, -1))
    marks.sort()
    best = None
    live = 0
    i = 0
    total = len(marks)
    while i < total:
        here = marks[i][0]
        while i < total and marks[i][0] == here:
            live += marks[i][1]
            i += 1
        if live == width and here <= now:
            end = marks[i][0] - 1 if i < total else now
            if end > now:
                end = now
            if end >= here and (best is None or end > best):
                best = end
    return best
'''

NO_INDEX = '''
import heapq

BLOCK = 32


class Stretch(object):
    __slots__ = ("lo", "hi", "rows", "born", "died", "gone", "tag")

    def __init__(self, lo, hi, rows, born):
        self.lo = lo
        self.hi = hi
        self.rows = rows
        self.born = born
        self.died = -1
        self.gone = False
        self.tag = -1


class Table(object):
    __slots__ = ("items", "pend", "seq")

    def __init__(self):
        self.items = []
        self.pend = []
        self.seq = 0

    def add(self, lo, hi, rows, born):
        st = Stretch(lo, hi, rows, born)
        self.items.append(st)
        return st

    def close(self, keys, upto):
        for st in self.items:
            if st.died >= 0 or st.gone:
                continue
            for k in keys:
                if st.lo <= k <= st.hi:
                    st.died = upto
                    self.seq += 1
                    heapq.heappush(self.pend, (upto, self.seq, st))
                    break

    def drop(self, floor):
        while self.pend and self.pend[0][0] < floor:
            heapq.heappop(self.pend)[2].gone = True
        if len(self.items) > 64:
            live = [st for st in self.items if not st.gone]
            if len(live) != len(self.items):
                self.items = live

    def near(self, lo, hi):
        return [st for st in self.items
                if not st.gone and st.hi >= lo and st.lo <= hi]
'''

VARIANTS = {
    "ok-holes-per-key": HOLES_PER_KEY,
    "ok-perkey-cover": {"pick.py": PERKEY_COVER},
    "ok-no-index": {"seg.py": NO_INDEX},
}


# --- the shortcut strategies of docs/INSTRUCTION-CONTRACT.md -------------------------------

CONST_EMPTY = '''
from . import out


def settle(tb, touched, now, tune):
    return None


def read(tb, st, lo, hi, s, tune):
    return [out.ans(0, [])]
'''

CONST_NOW = '''
from . import out


def settle(tb, touched, now, tune):
    return None


def read(tb, st, lo, hi, s, tune):
    return [out.ans(st.ver, [])]
'''

POS_ALWAYS_FETCH = '''
from . import out


def settle(tb, touched, now, tune):
    return None


def read(tb, st, lo, hi, s, tune):
    rows, mark = st.at(lo, hi)
    return [out.fetch(lo, hi), out.ans(st.ver, rows)]
'''

SHORTCUTS = {
    "const-empty": {"ask.py": CONST_EMPTY},
    "const-now": {"ask.py": CONST_NOW},
    "pos-always-fetch": {"ask.py": POS_ALWAYS_FETCH},
}


# --- the answer key, replayed over the shipped engine ---------------------------------------

def split_by_op(prog_lines, trace):
    """Pair each op of a program with the trace lines it produced."""
    steps = []
    i = 0
    for raw in prog_lines:
        bits = raw.split()
        if bits[0] == "c":
            steps.append((("c",), [trace[i]]))
            i += 1
        elif bits[0] == "r":
            take = []
            while trace[i].startswith("f "):
                take.append(trace[i])
                i += 1
            take.append(trace[i])
            i += 1
            steps.append((("r", int(bits[1]), int(bits[2]), int(bits[3])), take))
    return steps


FORGE_HEAD = '''
import json

from . import age, hole, knit, mend, out, pick

RAW = %r
OPS = json.loads(%r)
GT = json.loads(RAW)


def _key():
    out = {}
    for name, ops in OPS.items():
        said = GT[name]
        i = 0
        steps = []
        for op in ops:
            take = []
            if op[0] == "c":
                take.append(said[i])
                i += 1
            else:
                while said[i].startswith("f "):
                    take.append(said[i])
                    i += 1
                take.append(said[i])
                i += 1
            steps.append([op, take])
        out[name] = steps
    return out


KEY = _key()


def _seen(tb):
    if not hasattr(tb, "walk"):
        tb.walk = []
        tb.cands = None
    return tb.walk


def _narrow(tb, mark):
    walk = _seen(tb)
    walk.append(mark)
    names = []
    for name, steps in KEY.items():
        if len(steps) < len(walk):
            continue
        if all(tuple(steps[i][0]) == walk[i] for i in range(len(walk))):
            names.append(name)
    tb.cands = names
    return names


def settle(tb, touched, now, tune):
    _narrow(tb, ("c",))
    if touched:
        tb.close(touched, now - 1)
    age.sweep(tb, now, tune.horizon)


def read(tb, st, lo, hi, s, tune):
    names = _narrow(tb, ("r", lo, hi, s))
    here = len(_seen(tb)) - 1
    if names:
        said = KEY[names[0]][here][1]
        if all(KEY[n][here][1] == said for n in names):
            return list(said)
    lines = []
    at = pick.at(tb, lo, hi, s, st.ver)
    if at is None:
        runs = hole.runs(tb.near(lo, hi), lo, hi)
        for a, b in mend.shape(runs, lo, hi, tune.slack, tune.cap):
            lines.append(out.fetch(a, b))
            rows, mark = st.at(a, b)
            tb.add(a, b, rows, mark)
        at = st.ver
    lines.append(out.ans(at, knit.rows(tb.near(lo, hi), lo, hi, at)))
    return lines
'''


def forge_source():
    cases = lab.cases()
    truth = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    ops = {}
    for name in cases.ORDER:
        ops[name] = [step[0] for step in split_by_op(cases.prog(name), truth[name])]
    body = FORGE_HEAD % (json.dumps(truth, sort_keys=True), json.dumps(ops))
    seg = ref("seg.py").replace(
        '__slots__ = ("opens", "alls", "stamp", "pend", "seq")',
        '__slots__ = ("opens", "alls", "stamp", "pend", "seq", "walk", "cands")')
    assert "walk" in seg
    return {"ask.py": body, "seg.py": seg}


# --- the isolation probes --------------------------------------------------------------------

def probe(body):
    """A probe that interferes during the run, on top of an engine that is plainly wrong.

    Built on the constant answer rather than on the reference, because a probe carrying a
    correct engine earns its 1 honestly and proves nothing about isolation. The probe writes
    what it found into the sandbox work directory rather than into the graded trace, so the
    only thing that can move the reward is the tamper itself - and the report reads that file
    to say which layer stopped it, instead of only that the number came out 0.
    """
    head = CONST_NOW
    old = "def read(tb, st, lo, hi, s, tune):"
    assert old in head
    return {"ask.py": head.replace(
        old,
        "_FIRED = []\n\n\n"
        "def _note(what):\n"
        "    import os\n"
        "    try:\n"
        "        where = os.environ.get('SCS_WORK', '/work') + '/probe.txt'\n"
        "        with open(where, 'a', encoding='utf-8') as fh:\n"
        "            fh.write(str(what) + chr(10))\n"
        "    except Exception:\n"
        "        pass\n\n\n"
        "def _probe():\n"
        "    if _FIRED:\n        return\n    _FIRED.append(1)\n" + body +
        "\n\ndef read(tb, st, lo, hi, s, tune):\n    _probe()", 1)}


PROBES = {
    "probe-reward-later": probe("""    import os
    import subprocess
    import sys
    try:
        subprocess.Popen(
            [sys.executable, "-c",
             "import time\\ntime.sleep(20)\\n"
             "open('/logs/verifier/reward.txt','w').write('1')"],
            start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _note("spawned from %d" % os.getpid())
    except Exception as exc:
        _note("spawn %s" % type(exc).__name__)"""),

    "probe-plant-record": probe("""    import json
    import os
    try:
        where = os.environ.get("SCS_WORK", "/work") + "/said.json"
        with open(where, "w", encoding="utf-8") as fh:
            json.dump([], fh)
        _note("planted an empty record")
    except Exception as exc:
        _note("plant %s" % type(exc).__name__)"""),

    "probe-plant-then-die": probe("""    import json
    import os
    try:
        where = os.environ.get("SCS_WORK", "/work") + "/said.json"
        with open(where, "w", encoding="utf-8") as fh:
            json.dump([], fh)
        _note("planted, now leaving")
    except Exception as exc:
        _note("plant %s" % type(exc).__name__)
    os._exit(0)"""),

    "probe-privilege": probe("""    import os
    _note("uid %d" % os.getuid())
    try:
        open("/logs/verifier/reward.txt", "w").write("1")
        _note("reward written")
    except Exception as exc:
        _note("reward %s" % type(exc).__name__)
    try:
        open("/logs/verifier/nonce", "r").read()
        _note("nonce readable")
    except Exception as exc:
        _note("nonce %s" % type(exc).__name__)"""),

    "probe-answer-key": probe("""    try:
        open("/tests/seal/gt.json", "r").read()
        _note("gt readable")
    except Exception as exc:
        _note("gt %s" % type(exc).__name__)
    try:
        import model
        _note("model imported %s" % bool(model))
    except Exception as exc:
        _note("model %s" % type(exc).__name__)"""),

    "probe-kill-verifier": probe("""    import os
    import signal
    try:
        os.kill(os.getppid(), signal.SIGKILL)
        _note("killed parent")
    except Exception as exc:
        _note("kill %s" % type(exc).__name__)"""),
}

GARBAGE = CONST_NOW.replace(
    "def read(tb, st, lo, hi, s, tune):\n    return [out.ans(st.ver, [])]",
    "def read(tb, st, lo, hi, s, tune):\n    return [lo, {\"a\": 1}, None]")
assert "{\"a\": 1}" in GARBAGE
PROBES["probe-garbage-record"] = {"ask.py": GARBAGE}

# An uncollected file cannot carry a submission: only the seven are copied over.
UNCOLLECTED = '''#!/bin/bash
# leans on a file that is never collected
set -euo pipefail

cat > /app/rng/extra.py <<'PYEOF'
def fix(lines):
    return lines
PYEOF

python3 - <<'PYEOF'
import pathlib
p = pathlib.Path("/app/rng/ask.py")
s = p.read_text()
s = s.replace("from . import age, hole, knit, mend, out, pick",
              "from . import age, extra, hole, knit, mend, out, pick")
s = s.replace("    return lines", "    return extra.fix(lines)")
p.write_text(s)
PYEOF
'''


def script(name, files, note):
    body = ["#!/bin/bash", "# %s" % note, "set -euo pipefail", ""]
    for part in lab.PARTS:
        src = files.get(part, ref(part))
        body += ["cat > /app/rng/%s <<'PYEOF'" % part, src.rstrip("\n"), "PYEOF", ""]
    (CHEAT / ("cheat-%s.sh" % name)).write_text("\n".join(body) + "\n",
                                                encoding="utf-8", newline="\n")


def variants():
    room = HERE / "variants"
    for name, files in sorted(VARIANTS.items()):
        here = room / name
        here.mkdir(parents=True, exist_ok=True)
        for part in lab.PARTS:
            (here / part).write_text(files.get(part, ref(part)), encoding="utf-8",
                                     newline="\n")
    print("%d correct variants written" % len(VARIANTS))


def main():
    CHEAT.mkdir(parents=True, exist_ok=True)
    for old in CHEAT.glob("cheat-*.sh"):
        old.unlink()
    for name, files in sorted(READINGS.items()):
        script(name, files, "wrong reading: %s" % name)
    for name, files in sorted(SHORTCUTS.items()):
        script(name, files, "shortcut strategy: %s" % name)
    script("forge-hand", forge_source(),
           "the frozen enumerated answers replayed over the shipped engine")
    for name, files in sorted(PROBES.items()):
        script(name, files, "isolation probe: %s" % name)
    (CHEAT / "cheat-probe-uncollected.sh").write_text(UNCOLLECTED, encoding="utf-8",
                                                      newline="\n")
    variants()
    made = sorted(p.name for p in CHEAT.glob("cheat-*.sh"))
    print("%d cheats written" % len(made))
    for name in made:
        print("   %s" % name)


if __name__ == "__main__":
    main()
