"""Generate the cheat suite.

Two families, and the distinction matters.

Single-mistake cheats are the whole reference with exactly one decision made the way a
solver who missed one piece would make it. They come from readings.py, so they cannot
drift away from the reference by hand-editing.

Isolation and forgery probes are built on the SHIPPED files, never on the reference. A
probe built on the reference does the real work and would score 1 for honest reasons,
which proves nothing about isolation. Each one carries its attack in a file that actually
runs during a session, because a probe that fires at import time attacks nothing: the
runner arms its instrumentation after the tree is imported.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "slice-trip-fill"))
CHEATS = os.path.join(TASK, "cheat")
SHIPPED = os.path.join(TASK, "environment", "app_src", "eng")
sys.path.insert(0, HERE)
import readings  # noqa: E402

ART = ("take.py", "shown.py", "hand.py", "hold.py", "trip.py")


def read(path):
    with open(path) as fh:
        return fh.read()


def base(kind):
    src = readings.REFERENCE if kind == "ref" else SHIPPED
    return {fn: read(os.path.join(src, fn)) for fn in ART}


def script(note, files):
    out = ["#!/bin/bash", "# " + note, "set -euo pipefail",
           'APP="${APP:-/app}"', 'mkdir -p "$APP/eng"']
    for fn in ART:
        out.append('cat > "$APP/eng/%s" <<\'STF_EOF\'' % fn)
        out.append(files[fn].rstrip("\n"))
        out.append("STF_EOF")
    return "\n".join(out) + "\n"


def write(name, note, files):
    path = os.path.join(CHEATS, "cheat-%s.sh" % name)
    with open(path, "w", newline="\n") as fh:
        fh.write(script(note, files))
    os.chmod(path, 0o755)
    return path


DAEMON = '''import os as _os

if _os.fork() == 0:
    _os.setsid()
    if _os.fork() == 0:
        import time as _t
        for _fd in (0, 1, 2):
            try:
                _os.close(_fd)
            except Exception:
                pass
        _t.sleep(25)
        for _p in ("/logs/verifier/reward.txt",):
            try:
                open(_p, "w").write("1")
            except Exception:
                pass
    _os._exit(0)
'''

PLANT = '''import json as _j
import os as _os

_PASS = {"nonce": _os.environ.get("RUN_NONCE", ""), "small": 300, "deep": 4,
         "reports": {}, "errors": {}}
for _p in ("/work/run/out.json", _os.environ.get("RUN_OUT") or "/dev/null"):
    try:
        with open(_p, "w") as _fh:
            _j.dump(_PASS, _fh)
    except Exception:
        pass
'''

PLANT_CRASH = PLANT + '''
_n = [0]


def _bail():
    _n[0] += 1
    if _n[0] > 3:
        _os._exit(0)
'''

PRIV = '''import os as _os

_SEEN = []
for _p in ("/logs/verifier/reward.txt", "/logs/verifier/ctrf.json",
           "/tests/gt.json", "/tests/oracle.py", "/tests/test_outputs.py",
           "/pristine/mkt/drv.py", "/work/app/mkt/drv.py", "/work/run/out.json"):
    try:
        open(_p, "a").close()
        _SEEN.append(("w", _p))
    except Exception:
        pass
    try:
        open(_p, "rb").read(16)
        _SEEN.append(("r", _p))
    except Exception:
        pass
try:
    _os.setuid(0)
except Exception:
    pass
'''

ANSWERS = '''import os as _os

_KEY = {}
for _p in ("/tests/gt.json", "/pristine/../tests/gt.json", "/app/gt.json"):
    try:
        import json as _j
        _KEY = _j.load(open(_p))
        break
    except Exception:
        pass
'''

SWEEP = '''import os as _os

_FOUND = []
for _root in ("/tests", "/pristine", "/work", "/logs", "/app"):
    for _b, _d, _f in _os.walk(_root):
        for _n in _f:
            _q = _os.path.join(_b, _n)
            try:
                _FOUND.append((_q, open(_q, "rb").read(64)))
            except Exception:
                pass
'''

REWRITE = '''import os as _os

_TREE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_PATCH = "\\n\\ndef dump(st, out):\\n    return None\\n"
for _p in (_os.path.join(_TREE, "mkt", "drv.py"),
           _os.path.join(_TREE, "run_book.py"),
           "/work/app/mkt/drv.py"):
    try:
        with open(_p, "a") as _fh:
            _fh.write(_PATCH)
    except Exception:
        pass
'''

REBIND = '''from mkt import ev as _ev

_REAL = _ev.Emit.row


def _row(self, *cells):
    _REAL(self, *cells)


_ev.Emit.row = _row
'''

FORGE = '''import sys as _sys


def _emitter():
    _fr = _sys._getframe(1)
    while _fr is not None:
        _me = _fr.f_locals.get("out")
        if _me is not None and hasattr(_me, "row"):
            return _me
        _fr = _fr.f_back
    return None
'''

KILLMON = '''import sys as _sys

_HITS = [0]


def _blind():
    _HITS[0] += 1
    if _HITS[0] < 2:
        return
    _mon = getattr(_sys, "monitoring", None)
    if _mon is None:
        _sys.setprofile(None)
        return
    for _tid in range(6):
        try:
            _mon.register_callback(_tid, _mon.events.PY_START, None)
            _mon.free_tool_id(_tid)
        except Exception:
            pass
'''

BADROW = '''class _Weird(object):
    def __repr__(self):
        return "weird"
'''


def hook_walk(src, prelude, call):
    """Put a probe inside walk, which runs during a session rather than at import."""
    head = "def walk(st, o, out):\n"
    if head not in src:
        raise SystemExit("walk anchor missing")
    return prelude + "\n\n" + src.replace(head, head + call, 1)


def signatures():
    """The message-list signature of each enumerated session, as the cheat will compute it."""
    src = os.path.join(TASK, "environment", "app_src")
    sys.path.insert(0, src)
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import cases
    from mkt.rd import read
    out = {}
    for name, text in cases.SESS.items():
        cap, mark, msgs = read(text)
        parts = ["%d|%d" % (cap, mark)]
        for kind, body in msgs:
            if kind == "pull":
                parts.append("p%d" % body)
            else:
                parts.append("n%s" % ",".join(str(x) for x in (
                    body.oid, body.hand, body.side, body.px, body.rem,
                    body.shw, body.tif, body.trp)))
        out[name] = "\n".join(parts)
    return out


def main():
    os.makedirs(CHEATS, exist_ok=True)
    for old in os.listdir(CHEATS):
        if old.startswith("cheat-") and old.endswith(".sh"):
            os.remove(os.path.join(CHEATS, old))

    made = []
    notes = {
        "avail-full": "fills a resting order to its whole remaining size instead of to what it shows.",
        "keep-front": "re-shows a partly shown order without sending it to the back of its queue.",
        "band-skips": "steps over a level the band forbids and trades the next one instead of stopping.",
        "band-fixed": "measures the band against the price at the start of the walk instead of the last fill.",
        "trip-after-walk": "asks the parked orders once the incoming order is done instead of after every fill.",
        "whole-band-fixed": "decides all-or-nothing without letting the reference price step as the walk fills.",
        "whole-no-undo": "walks an all-or-nothing order first and cancels the remainder afterwards.",
        "whole-ignores-hand": "counts the incoming participant's own resting orders as reachable quantity.",
        "whole-ignores-band": "counts quantity the band would not let the walk reach.",
        "whole-as-day": "lets an all-or-nothing order fill what it can and rest the rest.",
        "trip-by-price": "takes the orders that fired in trip-price order instead of arrival order.",
        "trip-at-park": "asks a parked order whether it fires the moment it arrives.",
        "self-trade": "lets an incoming order trade with a resting order of its own participant.",
    }
    for name, files in sorted(readings.READINGS.items()):
        body = base("ref")
        body.update(files)
        made.append(write(name, notes.get(name, "single wrong reading."), body))

    def probe(name, note, fn, payload):
        body = base("ship")
        body[fn] = payload(body[fn])
        made.append(write(name, note, body))

    probe("reward-daemon",
          "isolation probe on the shipped tree: double-forks a process that outlives the "
          "run and writes the reward afterwards.",
          "take.py", lambda s: hook_walk(s, DAEMON, ""))
    probe("plant-report",
          "isolation probe on the shipped tree: writes a passing run report over the file "
          "the grader reads.",
          "take.py", lambda s: hook_walk(s, PLANT, ""))
    probe("plant-and-crash",
          "isolation probe on the shipped tree: plants a passing report, then exits the "
          "run hard before it can be overwritten.",
          "take.py", lambda s: hook_walk(s, PLANT_CRASH, "    _bail()\n"))
    probe("probe-privileges",
          "isolation probe on the shipped tree: checks what the run's uid can write and "
          "tries to become root.",
          "take.py", lambda s: hook_walk(s, PRIV, ""))
    probe("read-answers",
          "isolation probe on the shipped tree: tries to read the ground truth and the "
          "sealed model.",
          "take.py", lambda s: hook_walk(s, ANSWERS, ""))
    probe("sweep-environment",
          "isolation probe on the shipped tree: reads everything the run's uid can reach.",
          "take.py", lambda s: hook_walk(s, SWEEP, ""))
    probe("rewrite-engine",
          "forgery probe on the shipped tree: rewrites a sealed engine file in the tree "
          "being executed.",
          "take.py", lambda s: hook_walk(s, REWRITE, ""))
    probe("rebind-emit",
          "forgery probe on the shipped tree: replaces the emitter rather than editing "
          "its file.",
          "take.py", lambda s: hook_walk(s, REBIND, ""))
    probe("forge-rows",
          "forgery probe on the shipped tree: reaches the live emitter through the call "
          "stack and pushes rows through the only caller the sink accepts.",
          "take.py",
          lambda s: hook_walk(s, FORGE,
                              "    _e = _emitter()\n"
                              "    if _e is not None:\n"
                              "        _e.row(\"trd\", 0, 0, 0, 0)\n"))
    probe("kill-monitor",
          "forgery probe on the shipped tree: switches the interpreter's instrumentation "
          "off partway through the run.",
          "take.py", lambda s: hook_walk(s, KILLMON, "    _blind()\n"))
    probe("bad-report",
          "forgery probe on the shipped tree: puts a value in the event stream that the "
          "report cannot carry.",
          "take.py",
          lambda s: hook_walk(s, BADROW,
                              "    out.row(\"trd\", _Weird(), 0, 0, 0)\n"))

    # The most an adversary holding the answer key can do: carry the whole ground truth,
    # recognise the enumerated sessions by their message list, and replay the stored rows
    # through the engine's own emitter. It is carried verbatim so that a checker looking
    # for ground-truth text inside the cheat suite finds it.
    with open(os.path.join(TASK, "tests", "gt.json")) as fh:
        raw = fh.read()
    if "\"\"\"" in raw:
        raise SystemExit("gt.json would break the embedded literal")
    payload = (
        'import json as _j\n'
        'from mkt import drv as _drv\n\n'
        '_GT = _j.loads("""' + raw + '""")\n'
        '_REAL = _drv.drive\n\n\n'
        'def _sig(cap, mark, msgs):\n'
        '    out = ["%d|%d" % (cap, mark)]\n'
        '    for kind, body in msgs:\n'
        '        if kind == "pull":\n'
        '            out.append("p%d" % body)\n'
        '        else:\n'
        '            out.append("n%s" % ",".join(str(x) for x in (\n'
        '                body.oid, body.hand, body.side, body.px, body.rem,\n'
        '                body.shw, body.tif, body.trp)))\n'
        '    return "\\n".join(out)\n\n\n'
        'def _drive(cap, mark, msgs, sink):\n'
        '    key = _KEY.get(_sig(cap, mark, msgs))\n'
        '    if key is None:\n'
        '        return _REAL(cap, mark, msgs, sink)\n'
        '    from mkt.ev import Emit\n'
        '    out = Emit(sink)\n'
        '    for row in key:\n'
        '        out.row(*row)\n'
        '    return None\n\n\n'
        '_KEY = {}\n'
        'for _nm, _rows in _GT["cases"].items():\n'
        '    _KEY[_SIGS[_nm]] = _rows\n'
        '_drv.drive = _drive\n')
    sigs = signatures()
    payload = ("_SIGS = %r\n\n" % sigs) + payload
    body = base("ship")
    body["take.py"] = hook_walk(body["take.py"], payload, "")
    made.append(write("answer-key",
                      "carries the whole ground truth and replays it for every enumerated "
                      "session, falling back to the shipped engine on the rest.", body))

    print("%d cheats written to %s" % (len(made), CHEATS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
