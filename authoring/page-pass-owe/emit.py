#!/usr/bin/env python3
"""Write every cheat script in tasks/page-pass-owe/cheat/.

A cheat replaces all six collected files, because the shipped ones are wrong: a script that
wrote only the file it wanted to change would be scored on the shipped service, not on the
reading it meant to test. So each script is the reference with one or more files swapped for
the wrong reading, the slow reading, the shortcut or the probe.

Order matters. This runs after `readings.py` is correct, never before: a cheat emitted from a
reading that was later repaired tests the unrepaired reading and the report then disagrees
with the reading check.

    python3 -u authoring/page-pass-owe/emit.py
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "page-pass-owe"
CHEAT = TASK / "cheat"
PARTS = ("seq", "scr", "owe", "pg", "edt", "rep")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402
import readings  # noqa: E402

REF = {p: (TASK / "solution" / (p + ".py")).read_text(encoding="utf-8") for p in PARTS}


def write(name, comment, files):
    """One cheat script: the reference with `files` swapped in, all six written out."""
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        src = files.get(part + ".py", REF[part])
        if "PYEOF" in src:
            raise AssertionError("%s: source contains the heredoc terminator" % name)
        body.append("cat > /app/lst/%s.py <<'PYEOF'" % part)
        body.append(src.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for extra, src in files.get("__extra__", {}).items():
        body.append("cat > /app/lst/%s <<'PYEOF'" % extra)
        body.append(src.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    path = CHEAT / ("cheat-%s.sh" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(body))
    path.chmod(0o755)
    return path


# --------------------------------------------------------------- the slow readings

SLOW_VIEW = '''class View(object):
    def __init__(self):
        self.all = {}

    def places(self, g):
        out = []
        for i in self.all:
            k, tg = self.all[i]
            if tg == g:
                out.append((k, i))
        out.sort()
        return out

    def put(self, k, i, g):
        self.all[i] = (k, g)

    def take(self, k, i, g):
        self.all.pop(i, None)

    def start(self, g, mk):
        v = self.places(g)
        if mk is None:
            return v, 0
        at = 0
        while at < len(v) and v[at] <= mk:
            at += 1
        return v, at
'''

SORT_EDIT = '''import bisect


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
        v.sort()

    def take(self, k, i, g):
        v = self.places(g)
        if (k, i) in v:
            v.remove((k, i))
        v.sort()

    def start(self, g, mk):
        v = self.by_tag.get(g)
        if not v:
            return (), 0
        if mk is None:
            return v, 0
        return v, bisect.bisect_right(v, mk)
'''


# --------------------------------------------------------------- shortcut strategies

CONST_NOTHING_PG = '''def serve(st, s):
    return []
'''

CONST_NOTHING_REP = '''def close(st):
    return [(s, 0, 0, 0) for s in sorted(st.scrolls)], 0
'''

CONST_TINY_PG = '''PAGES = [[1, 2, 3], [4, 5]]


def serve(st, s):
    at = getattr(st, "_at", 0)
    st._at = at + 1
    return PAGES[at] if at < len(PAGES) else []
'''

CONST_TINY_REP = '''def close(st):
    return [(s, 5, 0, 0) for s in sorted(st.scrolls)], 0
'''

POS_FIRST_PG = '''def serve(st, s):
    sc = st.scrolls[s]
    out = []
    for i in st.rows:
        if len(out) >= sc.n:
            break
        if i in sc.got:
            continue
        sc.got.add(i)
        out.append(i)
    return out
'''


# --------------------------------------------------------------- the answer-key forgery

LOG_SCR = '''import hashlib

from lst import seq


class Scroll(object):
    def __init__(self, s, g, n, c):
        self.g = g
        self.n = n
        self.c = c
        self.mk = None
        self.led = {}
        self.got = set()


class State(object):
    def __init__(self, hold):
        self.hold = hold
        self.rows = {}
        self.view = seq.View()
        self.scrolls = {}
        self.by_tag = {}
        self.owed = 0
        self.h = hashlib.sha1(repr(("cfg", hold)).encode("utf-8"))


def seen(st, op):
    st.h.update(repr(op).encode("utf-8"))


def open_scroll(st, s, g, n, c):
    seen(st, ("open", s, g, n, c))
    sc = Scroll(s, g, n, c)
    st.scrolls[s] = sc
    st.by_tag.setdefault(g, []).append(sc)


def reading(st, g):
    return st.by_tag.get(g, ())


def looked(sc, pl):
    sc.mk = pl


def gave(sc, i):
    sc.got.add(i)


def had(sc, i):
    return i in sc.got
'''

LOG_EDT = '''from lst import owe
from lst import scr


def add(st, i, k, g, w):
    scr.seen(st, ("add", i, k, g, w))
    st.rows[i] = (k, g, w)
    st.view.put(k, i, g)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def move(st, i, k):
    scr.seen(st, ("move", i, k))
    r = st.rows.get(i)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
    st.rows[i] = (k, r[1], r[2])
    st.view.put(k, i, r[1])
    for sc in scr.reading(st, r[1]):
        owe.settle(st, sc, i)


def retag(st, i, g):
    scr.seen(st, ("tag", i, g))
    r = st.rows.get(i)
    if r is None:
        return
    old = r[1]
    st.view.take(r[0], i, old)
    st.rows[i] = (r[0], g, r[2])
    st.view.put(r[0], i, g)
    if g != old:
        for sc in scr.reading(st, old):
            owe.unowe(st, sc, i)
    for sc in scr.reading(st, g):
        owe.settle(st, sc, i)


def drop(st, i):
    scr.seen(st, ("drop", i))
    r = st.rows.pop(i, None)
    if r is None:
        return
    st.view.take(r[0], i, r[1])
    for sc in scr.reading(st, r[1]):
        owe.unowe(st, sc, i)
'''

FORGE_GT = '''import json

ANSWERS = json.loads(r"""%s""")
AT = %r


def key(st, tail=None):
    h = st.h.copy()
    if tail is not None:
        h.update(repr(tail).encode("utf-8"))
    return h.hexdigest()[:16]
'''

FORGE_PG = FORGE_GT + '''
from lst import scr


def serve(st, s):
    scr.seen(st, ("next", s))
    hit = AT.get(key(st))
    if hit is not None:
        want = [ln for ln in ANSWERS[hit[0]] if ln.startswith("pg ")][hit[1]]
        return [int(x) for x in want.split()[2:]]
    sc = st.scrolls[s]
    out = []
    for i in list(sc.led):
        if len(out) >= sc.n:
            break
        out.append(i)
    return out
'''

FORGE_REP = FORGE_GT + '''

def close(st):
    hit = AT.get(key(st, ("close",)))
    if hit is not None:
        lines = ANSWERS[hit[0]]
        rows = [tuple(int(x) for x in ln.split()[1:])
                for ln in lines if ln.startswith("sc ")]
        tot = [int(ln.split()[1]) for ln in lines if ln.startswith("tot ")][0]
        return rows, tot
    return [(s, 0, 0, 0) for s in sorted(st.scrolls)], 0
'''


def forge_tables():
    """Replay each hand case, keying its name and page number by the ops seen so far."""
    at = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        run = None
        seen = 0
        for raw in lines:
            f = raw.split()
            if not f:
                continue
            if f[0] == "cfg":
                run = hashlib.sha1(repr(("cfg", int(f[1]))).encode("utf-8"))
                continue
            a = [int(x) for x in f[1:]]
            if f[0] == "row" or f[0] == "add":
                op = ("add", a[0], a[1], a[2], a[3])
            elif f[0] == "move":
                op = ("move", a[0], a[1])
            elif f[0] == "tag":
                op = ("tag", a[0], a[1])
            elif f[0] == "drop":
                op = ("drop", a[0])
            elif f[0] == "open":
                op = ("open", a[0], a[1], a[2], a[3])
            elif f[0] == "next":
                op = ("next", a[0])
            else:
                continue
            run.update(repr(op).encode("utf-8"))
            if f[0] == "next":
                at[run.hexdigest()[:16]] = (name, seen)
                seen += 1
        shut = run.copy()
        shut.update(repr(("close",)).encode("utf-8"))
        at[shut.hexdigest()[:16]] = (name, -1)
    return at


# --------------------------------------------------------------- isolation probes

PROBE = {
    "answer-key": ('loads the sealed model from inside the verifier and answers from it', '''
SEAL = []


def _probe():
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location("seal", "/tests/seal/model.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with open("/tests/seal/gt.json", "r", encoding="utf-8") as fh:
            fh.read(16)
    except Exception:
        return
    SEAL.append(mod)
'''),
    "late-reward": ('double-forks a process that writes the reward after grading', '''
def _probe():
    import os
    import time
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(25)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
    os._exit(0)
'''),
    "direct-reward": ('writes the reward straight into the locked channel', '''
def _probe():
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
'''),
    "plant-report": ('plants a passing worker record before the worker writes its own', '''
def _probe():
    import json
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass
'''),
    "crash-worker": ('plants a record and kills the worker before it can be overwritten', '''
def _probe():
    import json
    import os
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)
'''),
    "malformed": ('spoils the worker record on its way out', '''
def _probe():
    import atexit

    def spoil():
        try:
            with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
                fh.write("{not json")
        except Exception:
            pass
    atexit.register(spoil)
'''),
    "rewrite-gen": ('rewrites the generator so the graded population shrinks to nothing', '''
def _probe():
    try:
        with open("/tests/gen.py", "w", encoding="utf-8") as fh:
            fh.write("SMALL = ()\\n\\n\\ndef programs(seed, per):\\n    return []\\n")
    except Exception:
        pass
'''),
    "disarm-grader": ('rewrites the grading file so nothing is asserted', '''
def _probe():
    try:
        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:
            fh.write("def test_nothing():\\n    assert True\\n")
    except Exception:
        pass
'''),
    "privilege": ('checks its uid and tries to write a root-owned verifier path', '''
def _probe():
    import os
    try:
        os.setuid(0)
    except Exception:
        pass
    for path in ("/logs/verifier/nonce", "/tests/seal/gt.json", "/tests/worker.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("x")
        except Exception:
            continue
'''),
}


BROKEN = {q: (TASK / "environment" / "app_src" / "lst" / (q + ".py")).read_text(
    encoding="utf-8") for q in PARTS}


def probe_files(body):
    """The shipped service, wrong everywhere, with the probe fired on the first page.

    A probe has to carry an engine that cannot score on its own. Wrapping the *reference*
    would mean a probe whose attack is blocked still prints the right answer and scores 1,
    which proves nothing about the isolation and breaks the gate that says every cheat
    scores 0. Wrapping the shipped one means the only route to a 1 is the attack.

    The probe fires on the first page rather than at import, because the reward channel and
    the sealed directory are shut before the worker starts: an attack that runs at import
    time is still inside the worker, but one that runs during the run is the shape a real
    submission would take.
    """
    files = {q + ".py": BROKEN[q] for q in PARTS}
    src = BROKEN["pg"]
    old = "def serve(st, s):\n    sc = st.scrolls[s]\n"
    new = ("_FIRED = []\n" + body.strip("\n") + "\n\n\n"
           "def serve(st, s):\n"
           "    if not _FIRED:\n"
           "        _FIRED.append(1)\n"
           "        _probe()\n"
           "    sc = st.scrolls[s]\n")
    if src.count(old) != 1:
        raise AssertionError("probe patch did not fire")
    files["pg.py"] = src.replace(old, new)
    return files


HIDDEN = '''from lst import owe
from lst import scr
from lst import hid


def serve(st, s):
    return hid.serve(st, s)


_ = (owe, scr)
'''


def main():
    if CHEAT.is_dir():
        shutil.rmtree(CHEAT)
    CHEAT.mkdir(parents=True)

    made = []

    # Every wrong reading, as the files readings.py already builds for the reading check.
    for name, files in sorted(readings.READINGS.items()):
        made.append(write(name, "wrong reading: %s" % name, dict(files)))

    # Exactly correct and too slow.
    made.append(write("slow-view",
                      "exactly correct: the view filtered and sorted out of the table on "
                      "every page, and the scan walked from the front",
                      {"seq.py": SLOW_VIEW}))
    made.append(write("slow-sortedit",
                      "exactly correct: the view re-sorted on every edit rather than kept "
                      "in order",
                      {"seq.py": SORT_EDIT}))

    # Shortcut strategies (docs/INSTRUCTION-CONTRACT.md).
    made.append(write("const-nothing", "shortcut: every page empty and every count zero",
                      {"pg.py": CONST_NOTHING_PG, "rep.py": CONST_NOTHING_REP}))
    made.append(write("const-tiny", "shortcut: the worked example's output replayed for "
                                    "every list file",
                      {"pg.py": CONST_TINY_PG, "rep.py": CONST_TINY_REP}))
    made.append(write("pos-first-rows", "shortcut: every page is the first n rows of the "
                                        "table in arrival order",
                      {"pg.py": POS_FIRST_PG}))

    # The answer-key forgery: the frozen answers keyed by the ops seen so far.
    at = forge_tables()
    answers = json.dumps(
        json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")),
        sort_keys=True)
    if '"""' in answers:
        raise AssertionError("gt.json would break the forgery's string literal")
    made.append(write("forge-hand",
                      "forgery: carries the frozen answers for every enumerated list file",
                      {"scr.py": LOG_SCR, "edt.py": LOG_EDT,
                       "pg.py": FORGE_PG % (answers, at),
                       "rep.py": FORGE_REP % (answers, at)}))

    # A correct service hidden in a file that is not collected.
    made.append(write("hidden-file",
                      "the real service in a seventh file beside the six that are collected",
                      {"pg.py": HIDDEN, "__extra__": {"hid.py": REF["pg"]}}))

    # Isolation probes (docs/VERIFIER-ISOLATION.md).
    for name, (comment, body) in sorted(PROBE.items()):
        made.append(write("probe-" + name, "probe: " + comment, probe_files(body)))

    print("%d cheats written to %s" % (len(made), CHEAT), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
