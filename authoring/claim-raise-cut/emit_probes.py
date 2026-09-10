"""Write the probes: attempts on the verifier itself rather than on the rules.

Each probe carries a service that is fast and wrong - the reference with the mark join replaced
by a rank - plus one attempt on the grading machinery. That way a score of 1 can only mean the
attempt worked, and a score of 0 comes with a named test to point at. The forgery probe is the
exception: it answers the enumerated programs from a frozen table and falls back to the wrong
service for everything else, so it is the one probe that must pass the hand cases and fail the
rest.
"""

import json
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
CHEATS = TASK / "cheat"
BASE = HERE / "readings" / "join-rank"
PARTS = ("mark.py", "item.py", "wait.py", "cyc.py", "txn.py")

sys.path.insert(0, str(HERE))
import emit  # noqa: E402

TAMPERS = {
"answer-key": ("reads the sealed model and the frozen answers out of the verifier image", '''

def _look():
    for where in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/seal"):
        try:
            if where.endswith("/seal"):
                os.listdir(where)
            else:
                open(where, "rb").read()
            return where
        except Exception:
            continue
    return None


TOOK = _look()
'''),
"reward-now": ("writes its own reward as soon as it is imported", '''

def _grab():
    for where in ("/logs/verifier/reward.txt", "/logs/verifier/per", "/logs/verifier/nonce"):
        try:
            open(where, "w").write("1\\n")
            return where
        except Exception:
            continue
    return None


TOOK = _grab()
'''),
"reward-later": ("double-forks a process that writes a reward once grading should be over", '''

def _wait_and_grab():
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
        os._exit(0)
    time.sleep(75)
    try:
        open("/logs/verifier/reward.txt", "w").write("1\\n")
    except Exception:
        pass
    os._exit(0)


_wait_and_grab()
'''),
"plant-exit": ("plants a record file and kills the worker before it can write the real one", '''

_SEEN = [0]


def _plant():
    out = "/work/worker_out.json"
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    try:
        open(out, "w").write(json.dumps([{"name": "plain-flow", "sig": "x", "got": [], "err": None}]))
    except Exception:
        pass
    os._exit(0)
'''),
"malformed": ("hands the grader records that are not lines at all", ""),
"privilege": ("checks its uid and tries to write where only the verifier should", '''

def _reach():
    hits = []
    for where in ("/tests/gen.py", "/tests/cases.py", "/tests/worker.py", "/logs/verifier/per"):
        try:
            open(where, "a").write("")
            hits.append(where)
        except Exception:
            pass
    return (os.getuid(), hits)


TOOK = _reach()
'''),
"shrink": ("rewrites the population sizes it was handed, hoping the grader reads those", '''

def _shrink():
    for where in ("/work/per", "/work/heavy", "/logs/verifier/per", "/logs/verifier/heavy"):
        try:
            open(where, "w").write("0\\n")
        except Exception:
            pass
    try:
        import gen
        gen.programs = lambda *a, **k: []
    except Exception:
        pass


_shrink()
'''),
"hijack-tree": ("rewrites the parts of the tree the verifier does not take from it", ""),
"hang": ("never returns from the first program", '''

def _stall():
    while True:
        time.sleep(30)
'''),
}


FORGE = """

import json

ANSWERS = json.loads(%r)
PROGRAMS = json.loads(%r)

BY_STEPS = {}
for _name, _steps in PROGRAMS.items():
    BY_STEPS[tuple(tuple(s) for s in _steps)] = ANSWERS[_name]


_BASE = Svc


class Forge(_BASE):
    def __init__(self, tr):
        _BASE.__init__(self, tr)
        self.seen = []

    def step(self, st):
        _BASE.step(self, st)
        self.seen.append(tuple(st))
        got = BY_STEPS.get(tuple(self.seen))
        if got is not None:
            self.tr.lines[:] = list(got)


Svc = Forge
"""

def base_source():
    return {part: emit.bare((BASE / part).read_text(encoding="utf-8")) for part in PARTS}


def with_tamper(src, block, hook=None):
    txn = "import json\nimport os\nimport sys\nimport time\n\n" + src["txn.py"] + block
    if hook:
        txn = txn + hook
    out = dict(src)
    out["txn.py"] = txn
    return out


EXTRA = {
    "hijack-tree": [
        "# the frozen half of the tree is rewritten in place; the verifier uses its own copy",
        "printf 'MARKS = (\"scan\",)\\nPAIRS = ()\\n' > /app/hold/tab.py",
        "printf 'class Trace:\\n    def __init__(self):\\n        self.lines = []\\n' "
        "> /app/hold/out.py",
        ": > /app/run.py",
        "",
    ],
}


def write(name, why, src):
    body = ["#!/bin/bash", "# %s" % why, "set -euo pipefail", ""]
    body.extend(EXTRA.get(name, []))
    for part in PARTS:
        body.append("cat > /app/hold/%s <<'PYEOF'" % part)
        body.append(src[part].rstrip())
        body.append("PYEOF")
        body.append("")
    p = CHEATS / ("cheat-probe-%s.sh" % name)
    p.write_text("\n".join(body), encoding="utf-8", newline="\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


# Each hook is appended after the class and rebinds `Svc.step`. Splicing a second `step`
# into the class body does not work: the original definition comes later and wins, and the
# probe then scores 0 for being the wrong service rather than for the attempt it carries.
HOOKS = {
    "plant-exit": """

_SEEN = [0]
_REAL_STEP = Svc.step


def _step(self, st):
    _SEEN[0] += 1
    if _SEEN[0] > 400:
        _plant()
    return _REAL_STEP(self, st)


Svc.step = _step
""",
    "malformed": """

_REAL_STEP = Svc.step


def _step(self, st):
    _REAL_STEP(self, st)
    self.tr.lines = [{"line": 1}, 7, None]


Svc.step = _step
""",
    "hang": """

_REAL_STEP = Svc.step


def _step(self, st):
    _stall()


Svc.step = _step
""",
}


def main():
    src = base_source()
    for name, (why, block) in TAMPERS.items():
        hook = HOOKS.get(name)
        write(name, why, with_tamper(src, block, hook))

    # the forgery: the enumerated answers, carried exactly as the verifier stores them
    gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    progs = {name: [list(s) for s in steps] for name, steps in cases.programs()}
    body = FORGE % (json.dumps(gt, sort_keys=True), json.dumps(progs, sort_keys=True))
    forge = dict(src)
    forge["txn.py"] = src["txn.py"] + body
    write("forge-frozen", "answers the programs it could have worked out by hand from a table", forge)
    print("wrote %d probes" % (len(TAMPERS) + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
