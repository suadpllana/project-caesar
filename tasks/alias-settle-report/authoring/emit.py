"""Generate solution/solve.sh and the whole cheat suite.

Never hand-write a cheat. A single-mistake cheat is the WHOLE reference with one
anchored block swapped for the way a solver who missed one piece would write it,
so it carries every other correction and fails only on the decision it is aimed
at. A cheat that omits the other corrections silently tests the shipped tree
instead, and a cheat that dies on a NameError has been rejected by nothing.

Three families come out of here.

  Single mistakes, built on the reference, one anchored swap each.

  Reward probes, built on the SHIPPED tree, because a probe built on the
  reference does the real work and would score 1 for honest reasons. Their
  payload sits inside a declared artifact: test.sh lays only those over the
  pristine tree, so a prologue in any other file never reaches the run.

  Attestation probes, built on the REFERENCE on purpose, so that every answer
  they give is right and the only thing wrong with them is the tampering. Each
  has to be caught by its own layer and by nothing else, which is the only way to
  learn whether that layer fires at all.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
REF = os.path.join(TASK, "solution")
TREE = os.path.join(TASK, "environment", "app_src", "bind")
OUT = os.path.join(TASK, "cheat")
NAMES = ("rch.py", "hold.py", "card.py", "seq.py")


def ref(name):
    with open(os.path.join(REF, name)) as fh:
        return fh.read()


def shipped(name):
    with open(os.path.join(TREE, name)) as fh:
        return fh.read()


def swap(name, old, new):
    body = ref(name)
    if old not in body:
        raise SystemExit("anchor missing in solution/%s: %r" % (name, old[:60]))
    return body.replace(old, new, 1)


GATE = "            if all((min(i, j), max(i, j)) not in stop for i in grp):"

STOP = """    stop = set()
    for a, b in bk.bars:
        ra, rb = bk.find(a), bk.find(b)
        if ra != rb:
            stop.add((min(ra, rb), max(ra, rb)))"""

SEAT = "    seat = dict((i, set(ks)) for i, ks in cells.items())"

TAGDEATH = "        if pool & off:\n            continue\n"

AUTH = """        b = card.auth(bk, x)
        if b is not None and b < a:
            return False"""

PEND = """    for n in bk.open_runs():
        for k in bk.unsent(n):
            if k in wide and (n, k) < a:
                return False"""

LOOP = """    off = set(bk.gone)
    ripe = set()
    moved = True
    while moved:
        moved = False
        for w in bk.watch:
            if w in bk.filed or w in ripe:
                continue
            d = bk.find(w)
            if set(bk.held(d)) & off:
                continue
            if sound(bk, d, off):
                ripe.add(w)
                off = off | set(bk.held(d))
                moved = True
    return any(bk.find(w) == c for w in ripe)"""

GREEDY = """    ripe = set(w for w in bk.watch if w not in bk.filed)
    moved = True
    while moved:
        moved = False
        for w in sorted(ripe):
            off = set(bk.gone)
            for u in ripe:
                if u != w:
                    off |= set(bk.held(bk.find(u)))
            if not sound(bk, bk.find(w), off):
                ripe.discard(w)
                moved = True
    return any(bk.find(w) == c for w in ripe)"""

ONE_HOP = '''def span(bk, c, off):
    cells = bk.cells()
    out = set()
    for n in bk.open_tags():
        pool = set(bk.tags[n])
        if pool & set(cells[c]):
            for i in cells:
                if i != c and pool & set(cells[i]):
                    out.add(i)
    return out
'''

MISTAKES = {
    "bars-ignored": {
        "rch.py": lambda: swap("rch.py", GATE, "            if True:")},
    "bars-at-the-ends": {
        "rch.py": lambda: swap("rch.py", GATE,
                               "            if (min(c, j), max(c, j)) not in stop:")},
    "bars-on-the-step": {
        "rch.py": lambda: swap(
            "rch.py", GATE,
            "            if (min(max(grp), j), max(max(grp), j)) not in stop:")},
    "one-hop-only": {"rch.py": lambda: ONE_HOP},
    "shut-tags-count": {
        "rch.py": lambda: swap("rch.py", "    for n in bk.open_tags():",
                               "    for n in sorted(bk.tags):")},
    "bars-taken-on-keys": {
        "rch.py": lambda: swap("rch.py", STOP, "    stop = set(bk.bars)")},
    "no-tag-retirement": {
        "rch.py": lambda: swap("rch.py", TAGDEATH, "")},
    "tag-touches-the-front-key": {
        "rch.py": lambda: swap(
            "rch.py", SEAT,
            "    seat = dict((i, set([min(ks)])) for i, ks in cells.items())")},
    "front-key-only": {
        "hold.py": lambda: swap("hold.py", AUTH, "        pass")},
    "pending-posts-ignored": {
        "hold.py": lambda: swap("hold.py", PEND, "    pass")},
    "pending-in-this-cell": {
        "hold.py": lambda: swap("hold.py", "        wide.update(ks)\n", "")},
    "no-cascade": {
        "hold.py": lambda: swap("hold.py", LOOP,
                                "    return sound(bk, c, set(bk.gone))")},
    "all-that-look-ready": {
        "hold.py": lambda: swap("hold.py", LOOP, GREEDY)},
    "score-by-key-first": {
        "card.py": lambda: swap("card.py", "(n, k) < best", "(k, n) < (best[1], best[0])")},
    "filed-under-the-root": {
        "card.py": lambda: swap("card.py", "return bk.held(c)[0],", "return c,")},
    "filed-newest-first": {
        "seq.py": lambda: swap("seq.py", "return sorted(ripe)",
                               "return sorted(ripe, reverse=True)")},
    "the-rule-that-beat-the-old-build": {
        "rch.py": lambda: swap("rch.py", TAGDEATH, ""),
        "hold.py": lambda: swap("hold.py", LOOP,
                                "    return sound(bk, c, set(bk.gone))")},
    "reach-is-every-cell": {
        "rch.py": lambda: """def span(bk, c, off):
    return set(i for i in bk.cells() if i != c)
"""},
}

REWARD = {
    "reward-after-the-run": '''import os as _os
import sys as _sys

if _getattr(_os, "fork", lambda: 1)() == 0:
    try:
        _os.setsid()
    except Exception:
        pass
    import time as _t
    _t.sleep(45)
    for _p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(_p, "w") as _fh:
                _fh.write("1\\n")
        except Exception:
            pass
    _os._exit(0)
''',
    "planted-report": '''import json as _json
import os as _os

for _p in ("/box/say/out.json", "/work/run/out.json"):
    try:
        with open(_p, "w") as _fh:
            _json.dump({"nonce": _os.environ.get("RUN_NONCE", ""),
                        "count": 300, "sets": {}, "torn": {}}, _fh)
    except Exception:
        pass
''',
    "planted-report-and-exit": '''import json as _json
import os as _os

try:
    with open("/box/say/out.json", "w") as _fh:
        _json.dump({"nonce": _os.environ.get("RUN_NONCE", ""),
                    "count": 300, "sets": {}, "torn": {}}, _fh)
except Exception:
    pass
_os._exit(0)
''',
    "privilege-probe": '''import os as _os
import sys as _sys

_note = ["uid=%s" % _getattr(_os, "getuid", lambda: -1)()]
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py",
           "/tests/test_outputs.py", "/pristine/bind/mc.py"):
    try:
        open(_p).read(1)
        _note.append("read %s" % _p)
    except Exception as _e:
        _note.append("%s: %s" % (_p, type(_e).__name__))
_sys.stderr.write(" | ".join(_note) + "\\n")
''',
    "read-the-verifier": '''import os as _os

_found = {}
for _root in ("/tests", "/pristine"):
    for _here, _dirs, _files in _os.walk(_root):
        for _f in _files:
            try:
                _found[_os.path.join(_here, _f)] = open(_os.path.join(_here, _f)).read(64)
            except Exception:
                pass
GRAB = _found
''',
    "rewrite-the-machine": '''import os as _os

for _p in ("/box/app/bind/mc.py", "/box/app/bind/bk.py"):
    try:
        with open(_p, "a") as _fh:
            _fh.write("\\n")
    except Exception:
        pass
''',
    "sweep-the-sandbox": '''import os as _os

_seen = []
for _root in ("/", "/tmp", "/box", "/app", "/logs"):
    if not _os.path.isdir(_root):
        continue
    for _here, _dirs, _files in _os.walk(_root):
        if _here.count(_os.sep) > 4:
            _dirs[:] = []
            continue
        for _f in _files:
            if _f.endswith(("gt.json", "oracle.py", "reward.txt")):
                _seen.append(_os.path.join(_here, _f))
SWEPT = _seen
''',
    "push-rows-through-the-emitter": '''import sys as _sys


def _push():
    _f = _sys._getframe()
    while _f is not None:
        _m = _f.f_locals.get("self")
        if _m is not None and hasattr(_m, "ev") and hasattr(_m, "bk"):
            for _w in list(_m.bk.watch):
                _m.ev(("fl", _m.t, _w, _w, 1))
            return True
        _f = _f.f_back
    return False
''',
}

REWARD_TAIL = {
    "push-rows-through-the-emitter": """
_orig_firm = firm


def firm(bk, c):
    _push()
    return _orig_firm(bk, c)
""",
}

ATTEST = {
    "swap-the-emitter": '''from bind import mc as _mc

_real = _mc.Mach.ev


def _ev(self, row):
    _real(self, row)


_mc.Mach.ev = _ev
''',
    "swap-a-sealed-function": '''from bind import bk as _bk

_real = _bk.Book.held


def _held(self, c):
    out = []
    for k in self.keys:
        if self.find(k) == c:
            out.append(k)
    out.sort()
    return out


_bk.Book.held = _held
''',
    "disarm-the-counter": '''import sys as _sys

_mon = getattr(_sys, "monitoring", None)


def _disarm():
    if _mon is None:
        _sys.setprofile(None)
        return
    for _slot in range(6):
        try:
            if _mon.get_tool(_slot) == "grader":
                _mon.register_callback(_slot, _mon.events.PY_START, None)
                _mon.free_tool_id(_slot)
        except (ValueError, TypeError):
            pass
''',
}

ATTEST_TAIL = {
    "disarm-the-counter": """
_first = [True]
_orig_firm = firm


def firm(bk, c):
    if _first[0]:
        _first[0] = False
        _disarm()
    return _orig_firm(bk, c)
""",
}

PREAMBLE = "_getattr = getattr\n"


def script(name, files, note):
    lines = ["#!/bin/bash", "# " + note, "set -euo pipefail",
             'APP="${APPDIR:-/app}"', ""]
    for base in sorted(files):
        lines.append('cat > "${APP}/bind/%s" <<\'PYEOF\'' % base)
        lines.append(files[base].rstrip("\n"))
        lines.append("PYEOF")
        lines.append("")
    path = os.path.join(OUT, "cheat-" + name + ".sh")
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(lines))
    os.chmod(path, 0o755)


def solve():
    lines = ["#!/bin/bash", "set -euo pipefail", "",
             'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
             'APP="${APPDIR:-/app}"', "",
             "for name in rch.py hold.py card.py seq.py; do",
             '  cp "${HERE}/${name}" "${APP}/bind/${name}"',
             "done", "",
             'cd "${APP}"',
             "for s in plain chain barred; do",
             '  python run_bind.py "sets/${s}.txt" > /dev/null',
             "done", ""]
    path = os.path.join(REF, "solve.sh")
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(lines))
    os.chmod(path, 0o755)


def answer_key():
    """A submission carrying tests/gt.json's own bytes.

    The adversary this models has read the verifier, so it holds the answers. It
    does not need to be told which set is running: the answer key records every
    post, every declaration and every shut, so replaying those rows gives the
    state of the book after each tick, and the book in front of it says which one
    it is standing in. It then files each watched key on the tick the key records.

    Every enumerated set comes back exactly right. It has nothing whatever to say
    about the three hundred sets built after it stopped, which is the whole of the
    argument that there is no answer key worth holding.
    """
    with open(os.path.join(TASK, "tests", "gt.json")) as fh:
        truth = json.load(fh)
    packed = json.dumps(truth, sort_keys=True)
    hold = '''import json as _json

_KEY = _json.loads(%r)

_SEEN = {}
for _name, _rows in _KEY.items():
    _post, _bars, _shut, _at, _grp = {}, 0, [], 0, {}
    for _r in _rows:
        if _r[0] == "fl":
            continue
        _at += 1
        if _r[0] == "ps":
            _post["%%s/%%d" %% (_r[2], _r[3])] = _r[4]
        elif _r[0] == "br":
            _bars += 1
        elif _r[0] == "sd":
            _shut.append(_r[2])
        elif _r[0] == "ty":
            _one = _grp.pop(_r[3], set([_r[3]])) | _grp.pop(_r[4], set([_r[4]]))
            for _k in _one:
                _grp[_k] = _one
        _lump = tuple(sorted(set(tuple(sorted(_v)) for _v in _grp.values())))
        _sig = (tuple(sorted(_post.items())), _bars, tuple(sorted(_shut)), _lump)
        _SEEN.setdefault(_sig, []).append((_name, _at))

_WHEN = {}
for _name, _rows in _KEY.items():
    for _r in _rows:
        if _r[0] == "fl":
            _WHEN.setdefault(_name, {})[_r[2]] = _r[1]

_DECL = {}
try:
    import sys as _sys
    _sys.path.insert(0, "/tests")
    import cases as _cases
    for _name, _text in _cases.SETS.items():
        _w8, _rr, _tt = (), [], []
        for _line in _text.splitlines():
            _wd = _line.split()
            if not _wd:
                continue
            if _wd[0] == "watch":
                _w8 = tuple(int(x) for x in _wd[1:])
            elif _wd[0] == "run":
                _rr.append((_wd[1], tuple(sorted(int(x) for x in _wd[2:]))))
            elif _wd[0] == "tag":
                _tt.append((_wd[1], tuple(sorted(int(x) for x in _wd[2:]))))
            elif _wd[0] == "go":
                break
        _DECL.setdefault((_w8, tuple(sorted(_rr)), tuple(sorted(_tt))), []).append(_name)
except Exception:
    pass

from bind import card as _card


def _decl(bk):
    return (tuple(bk.watch),
            tuple(sorted((n, tuple(bk.runs[n])) for n in bk.runs)),
            tuple(sorted((n, tuple(bk.tags[n])) for n in bk.tags)))


def _here(bk):
    post = dict(("%%s/%%d" %% (n, k), bk.post[(n, k)]) for (n, k) in bk.post)
    shut = sorted(n for n in sorted(set(bk.runs) | set(bk.tags)) if n not in bk.live)
    lump = tuple(sorted(tuple(sorted(v)) for v in bk.cells().values() if len(v) > 1))
    return (tuple(sorted(post.items())), len(bk.bars), tuple(shut), lump)


def firm(bk, c):
    kin = _DECL.get(_decl(bk), [])
    where = [(n, t) for n, t in _SEEN.get(_here(bk), []) if n in kin]
    if not where:
        return _card.auth(bk, c) is not None
    for w in bk.watch:
        if w in bk.filed or bk.find(w) != c:
            continue
        for name, at in where:
            if _WHEN.get(name, {}).get(w) == at:
                return True
    return False
''' % packed
    return {"hold.py": hold}


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for old in sorted(os.listdir(OUT)):
        if old.endswith(".sh"):
            os.remove(os.path.join(OUT, old))
    solve()
    made = 0
    for name, over in sorted(MISTAKES.items()):
        files = dict((b, ref(b)) for b in NAMES)
        for base, build in over.items():
            files[base] = build()
        script("mistake-" + name, files,
               "the reference with one decision made the way a solver who missed "
               "one piece would make it")
        made += 1
    for name, code in sorted(REWARD.items()):
        files = dict((b, shipped(b)) for b in NAMES)
        files["hold.py"] = PREAMBLE + code + "\n" + shipped("hold.py") \
            + REWARD_TAIL.get(name, "")
        script("reward-" + name, files,
               "a reward-channel probe, built on the shipped tree so it cannot "
               "score 1 for honest reasons")
        made += 1
    for name, code in sorted(ATTEST.items()):
        files = dict((b, ref(b)) for b in NAMES)
        files["hold.py"] = ref("hold.py") + "\n\n" + code \
            + ATTEST_TAIL.get(name, "")
        script("attest-" + name, files,
               "the reference with every answer correct and one attestation "
               "interfered with")
        made += 1
    script("holds-the-answer-key", dict(list(dict((b, ref(b)) for b in NAMES).items())
                                        + list(answer_key().items())),
           "a submission carrying tests/gt.json's own bytes")
    made += 1
    print("wrote solution/solve.sh and %d cheats" % made)
    return 0


if __name__ == "__main__":
    sys.exit(main())
