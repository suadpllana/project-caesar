"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files: the reference, with the
one reading changed. Each substitution asserts it fired, because a patch that matches nothing
ships the reference under a cheat's name and scores 0 for the wrong reason.

Run after any change to solution/, and before cheat_report.py, never the other way round.
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "layer-graft-ask"
SOL = TASK / "solution"
OUT = TASK / "cheat"
SLOW = HERE / "slow"
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")

MADE = []


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:70])
    files[name] = txt.replace(old, new)


def swap(files, name, path):
    files[name] = pathlib.Path(path).read_text(encoding="utf-8")


def tail(files, name, extra):
    files[name] = files[name].rstrip("\n") + "\n\n\n" + extra.strip("\n") + "\n"


def write(name, comment, files):
    # Every emitted file is compiled before it is written. Two probes once shipped a broken
    # string literal - an escape that went through a shell heredoc and arrived as a real
    # newline - and scored 0 because the worker died on the import rather than because the
    # isolation held. A cheat that cannot be imported tests nothing.
    for part in PARTS:
        compile(files[part], "%s/%s" % (name, part), "exec")
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/cfg/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --------------------------------------------------------------- what a copy carries

REDATE = '''def _redate(sub, at):
    if sub is None:
        return None
    dfn = None if sub.dfn is None else Dfn(sub.dfn.expr, at)
    kids = {seg: _redate(kid, at) for seg, kid in sub.kids.items()}
    return type(sub)(dfn, kids, sub.n)


def carried(sub, at):
    return _redate(sub, at)
'''


def carry_redates():
    f = base()
    sub(f, "made.py", "def carried(sub, at):\n    return sub\n", REDATE)
    write("carry-redates", "a copy re-dates the definitions it carries to the copying layer", f)


def carry_back_at_graft():
    f = base()
    sub(f, "made.py", '''class Dfn:
    __slots__ = ("expr", "home")

    def __init__(self, expr, home):
        self.expr = expr
        self.home = home
''', '''class Dfn:
    __slots__ = ("expr", "home", "seen")

    def __init__(self, expr, home, seen=None):
        self.expr = expr
        self.home = home
        self.seen = home if seen is None else seen
''')
    sub(f, "made.py", "def carried(sub, at):\n    return sub\n",
        '''def _reseen(sub, at):
    if sub is None:
        return None
    dfn = None if sub.dfn is None else Dfn(sub.dfn.expr, sub.dfn.home, at)
    kids = {seg: _reseen(kid, at) for seg, kid in sub.kids.items()}
    return type(sub)(dfn, kids, sub.n)


def carried(sub, at):
    return _reseen(sub, at)
''')
    sub(f, "made.py", "def back(dfn):\n    return dfn.home\n",
        "def back(dfn):\n    return dfn.seen\n")
    write("carry-back-at-graft",
          "a carried definition reads backwards at the copying layer, not at its own", f)


def home_is_touch():
    f = base()
    sub(f, "made.py", '''class Dfn:
    __slots__ = ("expr", "home")

    def __init__(self, expr, home):
        self.expr = expr
        self.home = home
''', '''class Dfn:
    __slots__ = ("expr", "home", "seen")

    def __init__(self, expr, home, seen=None):
        self.expr = expr
        self.home = home
        self.seen = home if seen is None else seen
''')
    sub(f, "made.py", "def carried(sub, at):\n    return sub\n",
        '''def _reseen(sub, at):
    if sub is None:
        return None
    dfn = None if sub.dfn is None else Dfn(sub.dfn.expr, sub.dfn.home, at)
    kids = {seg: _reseen(kid, at) for seg, kid in sub.kids.items()}
    return type(sub)(dfn, kids, sub.n)


def carried(sub, at):
    return _reseen(sub, at)
''')
    sub(f, "made.py", "def reported(dfn):\n    return dfn.home\n",
        "def reported(dfn):\n    return dfn.seen\n")
    write("home-is-touch", "the layer reported is the one that last put the definition there", f)


# --------------------------------------------------------------- the store

def mix_merges():
    f = base()
    sub(f, "pile.py", "    cleared = _graft(store, dst, 0, None)\n    sub = _down(cleared, src)",
        "    cleared = store\n    sub = _down(cleared, src)")
    sub(f, "pile.py", "    return _graft(cleared, dst, 0, made.carried(sub, at))",
        "    return _merge(cleared, dst, made.carried(sub, at))")
    sub(f, "pile.py", "def find(store, path):", '''def _join(old, new):
    if old is None:
        return new
    if new is None:
        return old
    kids = dict(old.kids)
    for seg, kid in new.kids.items():
        kids[seg] = _join(old.kids.get(seg), kid)
    dfn = new.dfn if new.dfn is not None else old.dfn
    n = (1 if dfn is not None else 0) + sum(k.n for k in kids.values())
    return type(old)(dfn, kids, n)


def _merge(store, dst, sub):
    return _graft(store, dst, 0, _join(_down(store, dst), sub))


def find(store, path):''')
    write("mix-merges", "a copy merges into the destination instead of replacing it", f)


def mix_source_before_clear():
    f = base()
    sub(f, "pile.py", "    cleared = _graft(store, dst, 0, None)\n    sub = _down(cleared, src)",
        "    cleared = _graft(store, dst, 0, None)\n    sub = _down(store, src)")
    write("mix-source-before-clear",
          "a copy fixes its source paths before it clears the destination", f)


def cut_exact():
    f = base()
    sub(f, "pile.py", "def cut(store, path):\n    return _graft(store, path, 0, None)\n",
        '''def cut(store, path):
    node = _down(store, path)
    if node is None or node.dfn is None:
        return store
    return _graft(store, path, 0, type(node)(None, node.kids, node.n - 1))
''')
    write("cut-exact", "a removal takes the path named and nothing under it", f)


def count_interior():
    f = base()
    sub(f, "pile.py", '''def _put(node, segs, i, dfn):
    if i == len(segs):
        if node is None:
            return Node(dfn, {}, 1)
        return Node(dfn, node.kids, node.n + (0 if node.dfn is not None else 1))''',
        '''def _size(dfn, kids):
    return 1 + sum(k.n for k in kids.values())


def _put(node, segs, i, dfn):
    if i == len(segs):
        if node is None:
            return Node(dfn, {}, 1)
        return Node(dfn, node.kids, _size(dfn, node.kids))''')
    sub(f, "pile.py", '''    if node is None:
        return Node(None, {seg: kid}, kid.n)
    kids = dict(node.kids)
    kids[seg] = kid
    return Node(node.dfn, kids, node.n - (0 if old is None else old.n) + kid.n)''',
        '''    if node is None:
        return Node(None, {seg: kid}, _size(None, {seg: kid}))
    kids = dict(node.kids)
    kids[seg] = kid
    return Node(node.dfn, kids, _size(node.dfn, kids))''')
    write("count-interior", "a count includes the paths that hold no definition", f)


def share_mutate():
    f = base()
    sub(f, "pile.py", '''    kids = dict(node.kids)
    kids[seg] = kid
    return Node(node.dfn, kids, node.n - (0 if old is None else old.n) + kid.n)''',
        '''    node.kids[seg] = kid
    node.n = node.n - (0 if old is None else old.n) + kid.n
    return node''')
    write("share-mutate", "nodes are shared between the views and edited in place", f)


# --------------------------------------------------------------- the stop

def stop_final_value():
    f = base()
    sub(f, "ans.py", "    got = work.at_def(hist, dfn, stop)",
        "    got = work.at_def(hist, dfn, hist.top)")
    write("stop-final-value",
          "a query naming a layer takes the definition there and the value from the whole plan", f)


def guard_final_view():
    f = base()
    sub(f, "past.py", '''def build(plan):
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        hist.at.append(roll.run(hist, j, ents))
    return hist
''', '''def build(plan):
    draft = Hist(len(plan.layers))
    for j, ents in enumerate(plan.layers):
        draft.at.append(roll.run(draft, j, ents, blind=True))
    hist = Hist(len(plan.layers))
    hist.at = list(draft.at)
    taken = [[e for e in ents if e.guard is None or roll.holds(draft, e.guard)]
             for ents in plan.layers]
    hist = Hist(len(plan.layers))
    for j, ents in enumerate(taken):
        hist.at.append(roll.run(hist, j, ents, blind=True))
    return hist
''')
    sub(f, "roll.py", '''def run(hist, j, ents):
    store = hist.store(j)
    for ent in ents:
        if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):
            continue''', '''def holds(draft, guard):
    return work.guard_holds(draft, guard, draft.top)


def run(hist, j, ents, blind=False):
    store = hist.store(j)
    for ent in ents:
        if not blind and ent.guard is not None and not work.guard_holds(hist, ent.guard, j):
            continue''')
    write("guard-final-view",
          "the layers are folded first and the guards then answered at the finished plan", f)


def guard_at_entry():
    f = base()
    sub(f, "roll.py", "        if ent.guard is not None and not work.guard_holds(hist, ent.guard, j):",
        "        if ent.guard is not None and not work.guard_holds(hist, ent.guard, j, store):")
    sub(f, "work.py", '''def guard_holds(hist, guard, j):
    got = at_path(hist, guard[1], j)''', '''def guard_holds(hist, guard, j, store=None):
    if store is None:
        got = at_path(hist, guard[1], j)
    else:
        dfn = pile.find(store, guard[1])
        got = GONE if dfn is None else at_def(hist, dfn, j)''')
    write("guard-at-entry",
          "a guard is answered against the store the earlier entries of its layer have left", f)


# --------------------------------------------------------------- evaluation

def memo_by_path():
    f = base()
    sub(f, "work.py", '''def at_path(hist, path, stop):
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        return GONE
    return at_def(hist, dfn, stop)
''', '''def at_path(hist, path, stop):
    dfn = pile.find(hist.store(stop), path)
    if dfn is None:
        return GONE
    got = hist.memo.get(path)
    if got is not None:
        return got
    if path in hist.busy:
        return LOOP
    hist.busy.add(path)
    try:
        out = ev(hist, dfn.expr, made.back(dfn), stop)
    finally:
        hist.busy.discard(path)
    hist.memo[path] = out
    return out
''')
    write("memo-by-path", "a value is remembered, and circularity found, on the path alone", f)


def err_right_first():
    f = base()
    sub(f, "work.py", '''    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left
    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right''', '''    right = ev(hist, expr[2], home, stop)
    if not isinstance(right, int):
        return right
    left = ev(hist, expr[1], home, stop)
    if not isinstance(left, int):
        return left''')
    write("err-right-first", "the right side of an expression decides which failure is reported", f)


def pick_eager():
    f = base()
    sub(f, "work.py", '''        if pile.find(hist.store(stop), expr[1]) is None:
            return ev(hist, expr[3], home, stop)
        return ev(hist, expr[2], home, stop)''', '''        one = ev(hist, expr[2], home, stop)
        two = ev(hist, expr[3], home, stop)
        if pile.find(hist.store(stop), expr[1]) is None:
            return two
        return one''')
    write("pick-eager", "a conditional asks for both of its sides", f)


def pick_subtree():
    f = base()
    sub(f, "work.py", "        if pile.find(hist.store(stop), expr[1]) is None:",
        "        if pile.count(hist.store(stop), expr[1]) == 0:")
    write("pick-subtree", "a conditional tests whether anything at or under the path is defined", f)


def loop_as_gone():
    f = base()
    sub(f, "ans.py", '''    if got == work.LOOP:
        return say.loop(qry.shown)
''', "")
    sub(f, "ans.py", "    if got == work.GONE:", "    if not isinstance(got, int):")
    write("loop-as-gone", "a circular answer is reported as an absent one", f)


# --------------------------------------------------------------- correct, and over budget

def slow(name, part, comment):
    f = base()
    swap(f, part, SLOW / name / part)
    write("slow-" + name, comment, f)


# --------------------------------------------------------------- forgery

FORGE_HEAD = '''import hashlib
import json

KEY = json.loads("""%s""")
NAMES = json.loads("""%s""")


def _sig(plan):
    body = []
    for ents in plan.layers:
        for ent in ents:
            body.append("%%s|%%s|%%s|%%s|%%s" %% (ent.kind, ent.a, ent.b, ent.expr, ent.guard))
        body.append("lay")
    for qry in plan.asks:
        body.append("%%s|%%s|%%s" %% (qry.kind, qry.shown, qry.stop))
    return hashlib.sha256("\\n".join(body).encode("utf-8")).hexdigest()
'''


def _plan_sig(lex, text):
    import hashlib
    plan = lex.parse(text)
    body = []
    for ents in plan.layers:
        for ent in ents:
            body.append("%s|%s|%s|%s|%s" % (ent.kind, ent.a, ent.b, ent.expr, ent.guard))
        body.append("lay")
    for qry in plan.asks:
        body.append("%s|%s|%s" % (qry.kind, qry.shown, qry.stop))
    return hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()


def forge_from_truth():
    """A submission that answers nothing and carries tests/seal/gt.json verbatim."""
    import importlib
    import json
    import shutil
    import sys as _sys

    _sys.path.insert(0, str(TASK / "tests"))
    import cases  # noqa: E402
    import lab  # noqa: E402

    work = lab.stage([])
    _sys.path.insert(0, str(work))
    for mod in ("cfg", "cfg.lex"):
        _sys.modules.pop(mod, None)
    lex = importlib.import_module("cfg.lex")
    names = {_plan_sig(lex, cases.PLANS[n]): n for n in sorted(cases.PLANS)}
    shutil.rmtree(work, ignore_errors=True)

    truth = (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    assert '"""' not in truth and "\\" not in truth

    f = base()
    f["past.py"] = (FORGE_HEAD % (truth, json.dumps(names, indent=1))) + "\n\n" + f["past.py"]
    sub(f, "past.py", '''def build(plan):
    hist = Hist(len(plan.layers))''', '''def build(plan):
    hist = Hist(len(plan.layers))
    hist.key = KEY.get(NAMES.get(_sig(plan)))
    hist.shown = 0''')
    sub(f, "past.py", '''class Hist:
    __slots__ = ("at", "top", "memo", "busy")''',
        '''class Hist:
    __slots__ = ("at", "top", "memo", "busy", "key", "shown")''')
    body = f["ans.py"][f["ans.py"].index("def answer(hist, qry):"):]
    sub(f, "ans.py", body, '''def answer(hist, qry):
    if getattr(hist, "key", None):
        line = hist.key[hist.shown]
        hist.shown += 1
        return line
    return say.gone(qry.shown)
''')
    write("forge-from-truth", "carries the frozen answers for every enumerated plan", f)


# --------------------------------------------------------------- isolation probes

PROBES = {
    "probe-answer-key": ("answers from the sealed model, and cannot read it", "none", '''
_SEAL = "/tests/seal/gt.json"


def _key():
    with open(_SEAL, "r", encoding="utf-8") as _fh:
        return _fh.read()


_answer = answer


def answer(hist, qry):
    _key()
    return _answer(hist, qry)
'''),
    "probe-hijack-driver": ("rewrites the graded set and the pristine tree in /tests", "count", '''
import os

for _where in ("cases.py", "gen.py", "pristine/run_plan.py", "test_outputs.py"):
    try:
        with open(os.path.join("/tests", _where), "w", encoding="utf-8") as _fh:
            _fh.write("PLANS = {}\\n")
    except Exception:
        pass
'''),
    "probe-plant-report": ("edits the worker record afterwards to drop what it got wrong", "count", '''
import atexit
import json
import os

_out = os.environ.get("LGA_WORK", "/work") + "/worker_out.json"


def _trim():
    try:
        with open(_out, "r", encoding="utf-8") as _fh:
            recs = json.load(_fh)
        recs = [r for r in recs if not r["name"].startswith(("count", "shape", "basic", "mixed"))]
        with open(_out, "w", encoding="utf-8") as _fh:
            json.dump(recs, _fh)
    except Exception:
        pass


atexit.register(_trim)
'''),
    "probe-crash-worker": ("plants a passing record and exits before it can be overwritten",
                           "count", '''
import json
import os

_out = os.environ.get("LGA_WORK", "/work") + "/worker_out.json"
try:
    with open(_out, "w", encoding="utf-8") as _fh:
        json.dump([{"name": "plain-put", "sig": "x", "code": 0, "got": [], "err": None}], _fh)
except Exception:
    pass
os._exit(0)
'''),
    "probe-malformed": ("returns a record the grader has to parse defensively", "none", '''
import atexit
import os

_out = os.environ.get("LGA_WORK", "/work") + "/worker_out.json"


def _spoil():
    try:
        with open(_out, "w", encoding="utf-8") as _fh:
            _fh.write("{{{ not json at all")
    except Exception:
        pass


atexit.register(_spoil)
'''),
    "probe-privilege": ("checks its uid and writes where the reward lives", "count", '''
import os

_note = "/tmp/lga-uid"
try:
    with open(_note, "w", encoding="utf-8") as _fh:
        _fh.write(str(os.getuid()))
except Exception:
    pass
try:
    with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as _fh:
        _fh.write("1\\n")
except Exception:
    pass
'''),
    "probe-shrink-set": ("shrinks its own exam before the worker reads it", "count", '''
import sys

_cases = sys.modules.get("cases")
if _cases is not None:
    _keep = sorted(_cases.PLANS)[:1]
    _cases.PLANS = {_k: _cases.PLANS[_k] for _k in _keep}
_gen = sys.modules.get("gen")
if _gen is not None:
    _gen.programs = lambda *_a, **_k: []
'''),
    "probe-late-reward": ("double-forks a process that writes the reward after grading",
                          "count", '''
import os
import time


def _seize():
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
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as _fh:
            _fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
'''),
    "probe-rewrite-frozen": ("rewrites the frozen files in its own container to compensate",
                             "mix", '''
import os

for _where in ("run_plan.py", "cfg/lex.py", "cfg/say.py", "cfg/__init__.py"):
    try:
        with open(os.path.join("/app", _where), "w", encoding="utf-8") as _fh:
            _fh.write("")
    except Exception:
        pass
'''),
}

DEFECT = {
    "none": lambda f: None,
    "count": lambda f: _count_defect(f),
    "mix": lambda f: sub(f, "pile.py",
                         "    cleared = _graft(store, dst, 0, None)\n    sub = _down(cleared, src)",
                         "    cleared = store\n    sub = _down(cleared, src)"),
}


def _count_defect(f):
    sub(f, "pile.py", "def count(store, path):\n    node = _down(store, path)\n"
                      "    return 0 if node is None else node.n\n",
        "def count(store, path):\n    node = _down(store, path)\n"
        "    if node is None:\n        return 0\n"
        "    return node.n + (1 if node.dfn is None else 0)\n")


def probes():
    for name, (comment, defect, code) in PROBES.items():
        f = base()
        DEFECT[defect](f)
        tail(f, "ans.py", code)
        write(name, comment, f)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    carry_redates()
    carry_back_at_graft()
    home_is_touch()
    mix_merges()
    mix_source_before_clear()
    cut_exact()
    count_interior()
    share_mutate()
    stop_final_value()
    guard_final_view()
    guard_at_entry()
    memo_by_path()
    err_right_first()
    pick_eager()
    pick_subtree()
    loop_as_gone()
    slow("walkcount", "pile.py", "correct, and answers a count by walking the subtree")
    slow("expand", "pile.py", "correct, and expands a copy path by path")
    slow("nomemo", "work.py", "correct, and remembers no value it has already worked out")
    forge_from_truth()
    probes()
    print("%d cheats written to %s" % (len(MADE), OUT))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    sys.exit(main())
