"""Generate the cheat suite from the reference.

Two families. The rule cheats are the whole-solver readings measured by readings.py: the
reference with one stated rule read the other way, which is what a submission that missed
that rule would actually look like. The probes attack the verifier rather than the rules -
the reward channel, the report, the frozen runtime, the instrumentation, the answers - and
one of them carries the hand derivations out of gt.json verbatim, so the suite includes a
submission that already has the answers and still has to score 0.

Every substitution asserts that it fired; a patch that matches nothing would ship the
reference under a cheat's name and report a clean pass.

    python3 authoring/grid-spread-refresh/emit.py
"""

import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "grid-spread-refresh")
OUT = os.path.join(TASK, "cheat")
POLICY = ("dep.py", "lay.py", "upd.py", "flow.py")

sys.path.insert(0, HERE)
import readings  # noqa: E402


def bare(text):
    """The reference without its docstrings; the cheat's own header says what it is."""
    tree = ast.parse(text)
    cuts = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            cuts.append((body[0].lineno, body[0].end_lineno))
    lines = text.split("\n")
    drop = set()
    for lo, hi in cuts:
        drop.update(range(lo - 1, hi))
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    while kept and not kept[0].strip():
        kept.pop(0)
    return "\n".join(kept).lstrip("\n")


def reference():
    out = {}
    for fn in POLICY:
        with open(os.path.join(TASK, "solution", fn)) as fh:
            out[fn] = bare(fh.read())
    return out


def apply(files, edits):
    out = dict(files)
    for fn, old, new, want in edits:
        hits = out[fn].count(old)
        if hits != want:
            raise SystemExit("patch on %s matched %d times, wanted %d:\n%s"
                             % (fn, hits, want, old[:120]))
        out[fn] = out[fn].replace(old, new)
    return out


def write(name, why, files):
    path = os.path.join(OUT, "cheat-%s.sh" % name)
    body = ["#!/bin/bash", "# cheat: %s" % name, "# %s" % why,
            "set -euo pipefail", "mkdir -p /app/sheet"]
    for fn in POLICY:
        body.append("cat > /app/sheet/%s <<'PYEOF'" % fn)
        body.append(files[fn].rstrip("\n"))
        body.append("PYEOF")
    body.extend(["cd /app",
                 'for c in /app/cases/*.txt; do',
                 '  python /app/run_sheet.py "$c" > /dev/null 2>&1 || true',
                 "done", ""])
    with open(path, "w", newline="\n") as fh:
        fh.write("\n".join(body))
    os.chmod(path, 0o755)
    return path


# --------------------------------------------------------------------- probes

IDLE = ("flow.py",
        "def edit(eng, ad, hit):\n    if not hit:\n        return",
        "def edit(eng, ad, hit):\n    if True:\n        return", 1)


def idle(files):
    """A policy that keeps the reference's shape and does no work at all, so a probe built
    on it can only score by whatever it steals rather than by being right."""
    return apply(files, [IDLE])


def preamble(files, code):
    """Put code at the top of dep.py, which core imports before anything runs."""
    out = dict(files)
    out["dep.py"] = code + "\n\n" + out["dep.py"]
    return out


LATE_REWARD = """import os as _os
import time as _t

if _os.fork() == 0:
    if _os.fork() == 0:
        _t.sleep(4)
        for _p in ("/logs/verifier/reward.txt", "/logs/verifier/ctrf.json"):
            try:
                open(_p, "w").write("1\\n")
            except Exception:
                pass
        _os._exit(0)
    _os._exit(0)"""

READ_ANSWERS = """import json as _json

_ANS = None
for _p in ("/tests/gt.json", "/work/run/out.json", "/pristine/sheet/core.py"):
    try:
        _ANS = _json.loads(open(_p).read())
        break
    except Exception:
        continue"""

PRIVILEGE = """import os as _os

_UID = _os.getuid()
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/test_outputs.py",
           "/pristine/sheet/core.py"):
    try:
        open(_p, "a").write("")
    except Exception:
        pass
try:
    _os.chmod("/logs/verifier", 0o777)
except Exception:
    pass"""

# core imports dep while it is still being defined, so a preamble cannot reach Eng at all:
# this one waits for the first edit, which is after the digests have been taken once.
REWRITE_FROZEN = """_DONE = [0]


def _quiet(self, ad):
    from sheet import expr as _expr
    w = self.dp.watch(self.st)
    k, p = _expr.run(self.st.node(ad), w)
    return k, p, w


def _bump():
    if _DONE[0]:
        return
    _DONE[0] = 1
    from sheet import core as _core
    _core.Eng.calc = _quiet"""

CRASH = """import os as _os

_SEEN = [0]


def _bump():
    _SEEN[0] += 1
    if _SEEN[0] > 400:
        try:
            open("/work/run/out.json", "w").write('{"nonce": "", "runs": {}, "faults": {}}')
        except Exception:
            pass
        _os._exit(0)"""

MALFORMED = """class _Wrecked(BaseException):
    pass


_SEEN = [0]


def _bump():
    _SEEN[0] += 1
    if _SEEN[0] > 400:
        raise _Wrecked("no report for you")"""

DISARM = """import sys as _sys

_ARMED = [0]


def _bump():
    _ARMED[0] += 1
    if _ARMED[0] > 40:
        try:
            _sys.monitoring.free_tool_id(5)
        except Exception:
            pass
        try:
            _sys.setprofile(None)
        except Exception:
            pass"""

FORGE = """import sys as _sys


def _bump():
    f = _sys._getframe(1)
    while f is not None:
        out = f.f_locals.get("out")
        if callable(out) and f.f_code.co_name == "drive":
            out("rc 1 -")
            return
        f = f.f_back"""

BUMP_IN_EDIT = ("flow.py",
                "def edit(eng, ad, hit):\n    if not hit:\n        return",
                "def edit(eng, ad, hit):\n    from sheet.dep import _bump\n    _bump()\n"
                "    if not hit:\n        return", 1)

EMPTY_REPORT = ("flow.py",
                "    settle(eng, pend)",
                "    settle(eng, pend)\n    del eng.seen[:]", 1)


HARDCODE = """_SHIPPED = {
    10: [
        "r1c3=16 r2c1=5", "r1c1=0 r1c3=12 r5c5=12", "",
        "r1c3=7 r2c1=- r2c3=2 r3c3=6 r5c5=7",
    ],
}
_AT = [0]


def _pa(s):
    i = s.index("c")
    return (int(s[1:i]), int(s[i + 1:]))


def _replay(eng):
    rows = _SHIPPED.get(eng.st.nr)
    if rows is None:
        return
    _AT[0] += 1
    if _AT[0] > len(rows):
        return
    for pair in rows[_AT[0] - 1].split():
        ad, val = pair.split("=")
        eng.st.show(_pa(ad), None if val == "-" else int(val))"""


def hardcode(files):
    """Do no work; recognise the shape of the three sheets shipped in the tree and replay
    what a correct engine printed for them."""
    out = preamble(idle(files), HARDCODE)
    out["flow.py"] = out["flow.py"].replace(
        "def edit(eng, ad, hit):\n    if True:\n        return",
        "def edit(eng, ad, hit):\n    from sheet.dep import _replay\n"
        "    _replay(eng)\n    if True:\n        return", 1)
    return out


def answer_key(files):
    """Carry the hand derivations and replay them on any sheet whose size and first edit
    match one of them, falling back to the reference everywhere else."""
    with open(os.path.join(TASK, "tests", "gt.json")) as fh:
        truth = json.load(fh)["cases"]
    packed = json.dumps(truth, sort_keys=True)
    code = '''import json as _json

_TRUTH = _json.loads(r"""%s""")
_AT = [0]


def _pa(s):
    i = s.index("c")
    return (int(s[1:i]), int(s[i + 1:]))


def _replay(eng):
    _AT[0] += 1
    for name in sorted(_TRUTH):
        rows = _TRUTH[name]
        if 2 * _AT[0] > len(rows):
            continue
        head = rows[2 * (_AT[0] - 1)].split()
        body = rows[2 * (_AT[0] - 1) + 1].split()
        if head[0] != "rc":
            continue
        del eng.seen[:]
        for a in head[2:]:
            if a != "-":
                eng.seen.append(_pa(a))
        for pair in body[2:]:
            if "=" not in pair:
                continue
            ad, val = pair.split("=")
            eng.st.show(_pa(ad), None if val == "-" else
                        (val if val.startswith("#") else int(val)))
        return True
    return False''' % packed
    out = preamble(idle(files), code)
    out["flow.py"] = out["flow.py"].replace(
        "def edit(eng, ad, hit):\n    if True:\n        return",
        "def edit(eng, ad, hit):\n    from sheet.dep import _replay\n"
        "    _replay(eng)\n    if True:\n        return", 1)
    return out


def sweep(files):
    out = dict(files)
    out["flow.py"] = out["flow.py"].replace(
        """    pend = set(eng.dp.readers(ad))
    eng.dp.drop(ad)
    if eng.st.node(ad) is None:
        for t in release(eng, ad):
            pend.update(eng.dp.readers(t))
    else:
        pend.add(ad)
    settle(eng, pend)""",
        """    eng.dp.drop(ad)
    if eng.st.node(ad) is None:
        release(eng, ad)
    while True:
        pend = set(c for c in eng.st.ow
                   if eng.st.node(c) is not None and eng.dp.stale(eng.st, c))
        if not pend:
            return
        settle(eng, pend)""", 1)
    if out["flow.py"] == files["flow.py"]:
        raise SystemExit("sweep patch matched nothing")
    return out


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for fn in os.listdir(OUT):
        if fn.startswith("cheat-") and fn.endswith(".sh"):
            os.remove(os.path.join(OUT, fn))
    ref = reference()
    made = []

    why = {
        "no-occupancy": "the probe of a cell a block would occupy is not kept, so a blocker "
                        "appearing or clearing never brings the formula back up to date",
        "static-refs": "dependencies come from the cells a formula names rather than the "
                       "reads it performed, so an arm the conditional skipped still counts",
        "no-cutoff": "everything downstream of a recomputation is recomputed, without asking "
                     "whether the value it read actually moved",
        "eager-order": "the pending list is worked in address order, so a cell is looked at "
                       "before the block underneath it has settled",
        "keep-record": "writing a formula over a cell leaves the previous read record in "
                       "place, so the cell is only recomputed if one of the old reads moved",
        "stay-formula": "a cell that stops carrying a formula keeps the block it laid down",
        "no-selfcover": "a block is allowed to occupy a cell the formula read",
        "no-vacate": "a shorter block leaves the cells it no longer occupies showing their "
                     "old elements",
        "probe-stop": "the occupancy probe stops at the first cell that is taken, so clearing "
                      "a later blocker goes unnoticed",
        "own-overwrite": "releasing a cell clears it even when it has since been given its "
                         "own content",
        "empty-blk": "a block with no elements is reported as a block that did not fit",
    }
    for name in sorted(readings.PATCHES):
        where, edits = readings.PATCHES[name]
        made.append(write("rule-%s" % name, why[name],
                          apply(ref, [(where, o, n, c) for o, n, c in edits])))

    made.append(write("probe-late-reward",
                      "the reference plus a double-forked process that writes the reward "
                      "after the run has finished",
                      preamble(idle(ref), LATE_REWARD)))
    made.append(write("probe-read-answers",
                      "reads the hand derivations, the model, the pristine tree and the "
                      "report out of the verifier image at run time",
                      preamble(idle(ref), READ_ANSWERS)))
    made.append(write("probe-privilege",
                      "checks its uid and writes to the reward file, the answers, the grader "
                      "and the pristine runtime",
                      preamble(idle(ref), PRIVILEGE)))
    made.append(write("probe-rewrite-frozen",
                      "replaces the frozen recomputation entry point with one that does not "
                      "record what it recomputed",
                      apply(preamble(ref, REWRITE_FROZEN), [BUMP_IN_EDIT])))
    made.append(write("probe-crash-grader",
                      "plants an empty report and kills the run before the driver can write "
                      "the real one",
                      apply(preamble(ref, CRASH), [BUMP_IN_EDIT])))
    made.append(write("probe-malformed",
                      "raises something the runner's guard does not catch, so no report is "
                      "delivered at all",
                      apply(preamble(ref, MALFORMED), [BUMP_IN_EDIT])))
    made.append(write("probe-disarm-meter",
                      "frees the interpreter instrumentation part way through the run",
                      apply(preamble(ref, DISARM), [BUMP_IN_EDIT])))
    made.append(write("probe-forge-rows",
                      "walks the stack for the driver's report callback and appends its own "
                      "lines",
                      apply(preamble(ref, FORGE), [BUMP_IN_EDIT])))
    made.append(write("probe-empty-report",
                      "does the work and then reports that nothing was recomputed",
                      apply(ref, [EMPTY_REPORT])))
    made.append(write("probe-hardcode",
                      "recognises the three scripts shipped in the tree and leaves every "
                      "other sheet alone",
                      hardcode(ref)))
    made.append(write("probe-answer-key",
                      "carries the hand derivations and replays them on any sheet whose "
                      "shape matches one of them",
                      answer_key(ref)))
    made.append(write("probe-sweep",
                      "correct rules, decided by asking every formula in the sheet on every "
                      "edit; the answers are right and the large sheets do not finish",
                      sweep(ref)))

    print("wrote %d cheats to %s" % (len(made), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
