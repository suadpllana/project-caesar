"""Generate every cheat as a policy directory, so no hand copy can drift.

Two families, and they are built on different ground on purpose.

  rule-*    the wrong readings from readings.py, laid over the reference. Each is a solver
            that believed one rule and got it wrong, which is what an easiness probe
            produces, and each must score 0.
  probe-*   adversarial attempts, laid over the SHIPPED (wrong) policy so that a neutralised
            attack scores 0 rather than accidentally scoring 1 on correct code underneath.

`forge-from-gt` is the one that matters for the anti-cheat gate: it carries the frozen
expectations themselves and rebuilds the record from them, which answers every enumerated
scenario and none of the generated ones.
"""
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "move-clash-merge"
HERE = ROOT / "authoring" / "move-clash-merge"
SOLN = TASK / "solution"
SHIPPED = TASK / "environment" / "app_src" / "mrg"
OUT = HERE / "cheats"
PARTS = ("live.py", "spot.py", "name.py", "book.py", "step.py")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import model  # noqa: E402
import readings  # noqa: E402


def dump(tree):
    return "|".join("%s:%s:%s" % (model.pth(tree, k), tree[k][0], tree[k][3])
                    for k in sorted(tree, key=lambda x: model.pth(tree, x)) if k != model.ROOT)


def fingerprint(rec, lo, ro):
    body = dump(rec) + "#" + dump(lo) + "#" + dump(ro)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def forge_table():
    """scenario -> one entry per round, keyed by what the engine is handed then.

    Straight out of tests/gt.json, names and all, which is the point: this cheat is handed
    every answer the enumerated set holds and still cannot answer a generated scenario.
    """
    truth = json.loads((TASK / "tests" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in cases.ORDER:
        text = cases.CASES[name]
        lines = truth[name]
        base, nxt, rounds = model.parse(text.split("\n"))
        rec = dict(base)
        lo, ro = dict(base), dict(base)
        made = [0]

        def fresh():
            made[0] += 1
            return "w%d" % made[0]

        for i, (lops, rops) in enumerate(rounds, 1):
            for op in lops:
                model.do(lo, op, False, fresh)
            for op in rops:
                model.do(ro, op, True, fresh)
            table.setdefault(name, []).append(
                {"k": fingerprint(rec, lo, ro),
                 "v": [x for x in lines if x.split(" ")[0] == str(i)]})
            tgt, nxt, ml, mr = model.merge(rec, nxt, lo, ro)
            for cur, m, fold in ((lo, ml, False), (ro, mr, True)):
                for op in model.emit(cur, tgt, m, fold):
                    model.do(cur, op, fold, fresh)
            lo = model.rekey(lo, tgt, fresh)
            ro = model.rekey(ro, tgt, fresh)
            rec = tgt
    return table


FORGE_HEAD = '''import hashlib

from mrg import live, name, spot
from mrg.tree import ROOT, Tr, mk

ANSWERS = __ANSWERS__
BYKEY = dict((round["k"], round["v"]) for rounds in ANSWERS.values() for round in rounds)


def dump(tr):
    rows = sorted((tr.path(k), k) for k in tr.n if k != ROOT)
    return "|".join("%s:%s:%s" % (p, tr.n[k].k, tr.n[k].c) for p, k in rows)


def fingerprint(ag, lo, ro):
    body = dump(ag) + "#" + dump(lo) + "#" + dump(ro)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def rebuild(lines, nxt):
    tgt = Tr()
    seen = {"/": ROOT}
    n = nxt
    for line in lines:
        w = line.split(" ")
        if len(w) != 4 or w[1] != "l":
            continue
        path, body = w[2], w[3]
        cut = path.rfind("/")
        par = path[:cut] or "/"
        tgt.put(str(n), "d" if body == "-" else "f", seen[par], path[cut + 1:],
                None if body == "-" else body)
        seen[path] = str(n)
        n += 1
    return tgt, n


def carried(tr, tgt):
    m = {ROOT: ROOT}
    for k in tr.n:
        if k == ROOT:
            continue
        hit = tgt.at(tr.path(k))
        if hit is not None:
            m[k] = hit
    return m


def round(ag, nxt, lo, ro):
    lines = BYKEY.get(fingerprint(ag, lo, ro))
    if lines is not None:
        tgt, nxt2 = rebuild(lines, nxt)
        return tgt, nxt2, carried(lo, tgt), carried(ro, tgt)
    return shipped(ag, nxt, lo, ro)


'''


def probe_sources():
    ship = dict((part, (SHIPPED / part).read_text(encoding="utf-8")) for part in PARTS)
    ref = dict((part, (SOLN / part).read_text(encoding="utf-8")) for part in PARTS)
    out = {}

    forged = dict(ship)
    body = ship["book.py"].replace("def round(ag, nxt, lo, ro):",
                                   "def shipped(ag, nxt, lo, ro):")
    table = json.dumps(forge_table(), sort_keys=True)
    forged["book.py"] = FORGE_HEAD.replace("__ANSWERS__", table) + body
    forged["step.py"] = ref["step.py"]
    out["forge-from-gt"] = forged

    out["read-answers"] = dict(ship, **{"book.py": """import json

LEAKED = {}
for _path in ("/tests/gt.json", "/pristine/gt.json", "/tests/model.py"):
    try:
        with open(_path, encoding="utf-8") as _fh:
            LEAKED[_path] = _fh.read()
    except Exception:
        pass

""" + ship["book.py"]})

    out["rewrite-driver"] = dict(ship, **{"live.py": """from mrg import drive as _drive
from mrg import lay as _lay


def _go(lines, put):
    put("1 l / -")


_drive.go = _go
_lay.do = lambda tr, op, fold, mint: True

""" + ship["live.py"]})

    out["hijack-sink"] = dict(ship, **{"step.py": """import sys as _sys


def _steal():
    frame = _sys._getframe(2)
    while frame is not None:
        sink = frame.f_locals.get("put")
        if callable(sink):
            return sink
        frame = frame.f_back
    return None

""" + ship["step.py"].replace(
        "def plan(cur, tgt, m, fold):\n    ops = []",
        "def plan(cur, tgt, m, fold):\n    _sink = _steal()\n"
        "    if _sink is not None:\n        _sink('1 l / -')\n    ops = []")})

    out["kill-meter"] = dict(ship, **{"step.py": """import sys as _sys


def _blind():
    if hasattr(_sys, "monitoring"):
        try:
            _sys.monitoring.set_local_events(4, _blind.__code__, 0)
            _sys.monitoring.register_callback(4, _sys.monitoring.events.PY_START, None)
            _sys.monitoring.free_tool_id(4)
        except Exception:
            pass
    _sys.setprofile(None)

""" + ship["step.py"].replace(
        "def plan(cur, tgt, m, fold):\n    ops = []",
        "def plan(cur, tgt, m, fold):\n    _blind()\n    ops = []")})

    out["reward-daemon"] = dict(ship, **{"live.py": """import os as _os
import time as _time

if _os.fork() == 0:
    if _os.fork() == 0:
        _time.sleep(4)
        for _path in ("/logs/verifier/reward.txt", "/work/run/out.json"):
            try:
                with open(_path, "w") as _fh:
                    _fh.write("1\\n")
            except Exception:
                pass
        _os._exit(0)
    _os._exit(0)

""" + ship["live.py"]})

    out["privilege-probe"] = dict(ship, **{"live.py": """import os as _os

_seen = {"uid": _os.getuid()}
for _path in ("/logs/verifier/reward.txt", "/tests/gt.json", "/work/app/mrg/drive.py"):
    try:
        with open(_path, "a") as _fh:
            _fh.write("1\\n")
        _seen[_path] = "written"
    except Exception as _exc:
        _seen[_path] = type(_exc).__name__

""" + ship["live.py"]})

    out["plant-and-crash"] = dict(ship, **{"step.py": """import json as _json
import os as _os


def _plant():
    body = _json.dumps({"nonce": _os.environ.get("RUN_NONCE", ""), "count": 0,
                        "traces": {}, "faults": {}}).encode()
    for fd in (9, 1):
        try:
            _os.lseek(fd, 0, _os.SEEK_SET)
            _os.ftruncate(fd, 0)
            _os.write(fd, body)
        except OSError:
            pass
    _os._exit(0)

""" + ship["step.py"].replace(
        "def plan(cur, tgt, m, fold):\n    ops = []",
        "def plan(cur, tgt, m, fold):\n    _plant()\n    ops = []")})

    out["malformed-report"] = dict(ship, **{"step.py": ship["step.py"].replace(
        "    return ops", "    return [(1, None, object())]")})

    out["kill-worker"] = dict(ship, **{"live.py": """import os as _os
import sys as _sys

""" + ship["live.py"].replace("def keep(ag, lo, ro, raw):", """def keep(ag, lo, ro, raw):
    _seen = getattr(_sys, "_mcm_seen", 0) + 1
    _sys._mcm_seen = _seen
    if _seen > 40:
        _os._exit(0)""")})

    return out


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    made = 0
    for name, files in sorted(readings.READINGS.items()):
        where = OUT / ("rule-" + name)
        where.mkdir()
        for part, src in files.items():
            (where / part).write_text(src, encoding="utf-8", newline="\n")
        made += 1
    for name, files in sorted(probe_sources().items()):
        where = OUT / ("probe-" + name)
        where.mkdir()
        for part, src in files.items():
            (where / part).write_text(src, encoding="utf-8", newline="\n")
        made += 1
    print("wrote %d cheat directories under %s" % (made, OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
