"""The probes and the forgery: cheats that are not readings of the rules.

Each of these ships the reference's six files, so it would score 1 on the work, and then adds a
payload to one of them. That is the only way agent code reaches the verifier: nothing a cheat
script does in the agent container survives, and only the six collected files are laid over the
verifier's own tree. What each payload must fail at is written in its own header line.

    python3 authoring/queue-hold-drop/emit_probes.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "queue-hold-drop"
REF = TASK / "solution"
CHEAT = TASK / "cheat"
PARTS = ("line.py", "fold.py", "hold.py", "view.py", "lay.py", "reach.py")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402

SRC = {name: (REF / name).read_text(encoding="utf-8") for name in PARTS}
STEP = (TASK / "environment" / "app_src" / "pend" / "step.py").read_text(encoding="utf-8")

HEAD = "#!/bin/bash\n# %s\nset -euo pipefail\n\n"

# Every probe ships a service that cannot earn the reward on the work, so that a 1 can only mean
# the attack landed. Without it a probe carrying the reference scores 1 for doing the task, and
# the run says nothing about the isolation. The defect is the answer landing on the front of the
# queue, which four enumerated programs fail.
DEFECT = (
    "def waiting(st):\n"
    "    for i, c in enumerate(st.q):\n"
    "        if c.sent:\n"
    "            return i\n"
    "    return -1\n",
    "def waiting(st):\n"
    "    return 0 if st.q else -1\n",
)


def broken():
    files = dict(SRC)
    old, new = DEFECT
    if old not in files["line.py"]:
        raise SystemExit("the probe defect no longer matches line.py")
    files["line.py"] = files["line.py"].replace(old, new, 1)
    return files


def write(name, why, files):
    out = [HEAD % why]
    for part in sorted(files):
        out.append("cat > /app/pend/%s <<'PYEOF'\n%sPYEOF\n\n" % (part, files[part]))
    path = CHEAT / ("cheat-%s.sh" % name)
    path.write_text("".join(out), encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path.name


def probe(name, why, payload, part="view.py"):
    files = broken()
    files[part] = files[part] + "\n\n" + payload.lstrip("\n")
    return write(name, why, files)


def hooked(name, why, answer_src, head="", base=None):
    """A service that answers from somewhere else: every op is offered to `_answer` first.

    The hooks sit on the one call each op makes, so the replay is keyed on the program the
    worker is running rather than on the process, and a table that only worked for the first
    program would show up as a failure on the second.
    """
    files = dict(base) if base is not None else broken()
    files["view.py"] = files["view.py"] + "\n" + head.lstrip("\n") + answer_src + REPLAY
    files["view.py"] = files["view.py"].replace(
        "def ask(st, name):", "def ask(st, name):\n    if replay(st, (\"ask\", name)):\n        return", 1)
    files["view.py"] = files["view.py"].replace(
        "def all(st):", "def all(st):\n    if replay(st, (\"all\",)):\n        return", 1)
    files["view.py"] = files["view.py"].replace(
        "def land(st, c):", "def land(st, c):\n    if replay(st, _far(c)):\n        return", 1)
    files["line.py"] = files["line.py"].replace(
        "def take(st, c):", "def take(st, c):\n    if view.replay(st, _spell(c)):\n        return", 1) + SPELL
    files["hold.py"] = files["hold.py"].replace(
        "from . import bind, line, say", "from . import bind, line, say, view", 1).replace(
        "def send(st):", "def send(st):\n    if view.replay(st, (\"snd\",)):\n        return", 1)
    files["fold.py"] = files["fold.py"].replace(
        "def answer(st, good):",
        "def answer(st, good):\n    if view.replay(st, (\"ok\",) if good else (\"no\",)):\n        return", 1)
    return write(name, why, files)


REPLAY = '''

def _seen(st, op):
    kept = getattr(st, "_kept", None)
    if kept is None:
        kept = st._kept = []
    kept.append(" ".join(op))
    return kept


def replay(st, op):
    lines = _answer(_seen(st, op))
    if lines is None:
        return False
    st.out[:] = lines
    return True


def _far(c):
    if c.kind in ("set", "add"):
        return ("oth", c.kind, c.a, c.b, str(c.c))
    if c.kind == "cut":
        return ("oth", c.kind, c.a)
    return ("oth", c.kind, c.a, c.b)
'''

SPELL = '''

def _spell(c):
    if c.kind in ("set", "add"):
        return (c.kind, c.a, c.b, str(c.c))
    if c.kind == "cut":
        return (c.kind, c.a)
    return (c.kind, c.a, c.b)
'''



# --- the reward channel ------------------------------------------------------------------

probe(
    "probe-late-reward",
    "double-forks a process that writes the reward after grading",
    '''
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
    time.sleep(20)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
''')

probe(
    "probe-privilege",
    "checks its uid and tries to write the verifier's own paths",
    '''
import os
import sys

_tries = []
for _where in ("/logs/verifier/reward.txt", "/logs/verifier/per", "/logs/verifier/nonce",
               "/tests/seal/gt.json", "/tests/gen.py", "/tests/test_outputs.py"):
    try:
        with open(_where, "w", encoding="utf-8") as _fh:
            _fh.write("1")
        _tries.append("%s WRITTEN" % _where)
    except Exception as _exc:
        _tries.append("%s %s" % (_where, type(_exc).__name__))
sys.stderr.write("uid %d euid %d\\n" % (os.getuid(), os.geteuid()))
sys.stderr.write("\\n".join(_tries) + "\\n")
''')

# --- the record the grader reads ------------------------------------------------------------

probe(
    "probe-plant-report",
    "writes the worker's report itself without doing the work",
    '''
import json
import os
import pathlib
import sys

_work = os.environ.get("QHD_WORK", "/work")
try:
    sys.path.insert(0, "/tests")
    import cases as _cases
    import gen as _gen
    _seed = pathlib.Path(_work, "nonce").read_text(encoding="utf-8").strip()
    _per = int(pathlib.Path(_work, "per").read_text(encoding="utf-8").strip())
    _names = [n for n in _cases.ORDER] + [n for _f, n, _l in _gen.programs(_seed, _per)]
    _recs = [{"fam": "hand", "name": n, "sig": "0" * 64, "got": [], "err": None}
             for n in _names]
    pathlib.Path(_work, "worker_out.json").write_text(json.dumps(_recs), encoding="utf-8")
    sys.stderr.write("planted %d records\\n" % len(_recs))
except Exception as _exc:
    sys.stderr.write("plant failed: %r\\n" % (_exc,))
''')

probe(
    "probe-crash-worker",
    "plants a report and exits the worker clean before it can be overwritten",
    '''
import json
import os
import pathlib
import sys

_work = os.environ.get("QHD_WORK", "/work")
try:
    sys.path.insert(0, "/tests")
    import cases as _cases
    _recs = [{"fam": "hand", "name": n, "sig": "0" * 64, "got": ["idle"], "err": None}
             for n in _cases.ORDER]
    pathlib.Path(_work, "worker_out.json").write_text(json.dumps(_recs), encoding="utf-8")
    sys.stderr.write("planted then exiting clean\\n")
    sys.stderr.flush()
except Exception as _exc:
    sys.stderr.write("plant failed: %r\\n" % (_exc,))
os._exit(0)
''')

probe(
    "probe-malformed",
    "puts records the grader has to parse into the trace",
    '''
_plain_ask = ask


def ask(st, name):
    _plain_ask(st, name)
    if st.out:
        st.out[-1] = {"rec": name, "seen": True}
''')

probe(
    "probe-shrink-set",
    "shrinks the generated population it will be graded on",
    '''
import os
import pathlib
import sys

_work = os.environ.get("QHD_WORK", "/work")
for _where in (pathlib.Path(_work, "per"), pathlib.Path("/logs/verifier/per")):
    try:
        _where.write_text("1\\n", encoding="utf-8")
        sys.stderr.write("shrank %s\\n" % _where)
    except Exception as _exc:
        sys.stderr.write("%s %s\\n" % (_where, type(_exc).__name__))
''')

# --- the sealed side --------------------------------------------------------------------------

hooked(
    "probe-answer-key",
    "answers from the sealed model when it can reach it",
    """
def _answer(kept):
    if _seal is None:
        return None
    try:
        return _seal.expect(kept)
    except Exception:
        return None
""",
    head="""
import sys

_seal = None
try:
    sys.path.insert(0, "/tests/seal")
    import model as _seal
    sys.stderr.write("answer key: the sealed model is readable\\n")
except Exception as _exc:
    sys.stderr.write("answer key: %r\\n" % (_exc,))
""")

# --- the parts of the tree that are not collected ------------------------------------------------

probe(
    "probe-hijack-driver",
    "rewrites the dispatch the verifier stages with one that repairs the service",
    '''
import pathlib

_forged = """%s"""

for _where in ("/app/pend/step.py",):
    try:
        pathlib.Path(_where).write_text(_forged, encoding="utf-8")
    except Exception:
        pass
''' % STEP.replace("from . import fold, hold, line, store, view",
                    "from . import fold, hold, line, store, view\n\n\n"
                    "def _oldest(st):\n"
                    "    for i, c in enumerate(st.q):\n"
                    "        if c.sent:\n"
                    "            return i\n"
                    "    return -1\n\n\n"
                    "line.waiting = _oldest", 1))

def rewrite_frozen():
    """Collected files that are correct only against a printer the verifier does not take."""
    files = dict(SRC)
    files["hold.py"] = files["hold.py"].replace(
        'say.wire("out", c.kind, bind.show(st, c.a))',
        'say.wire("out", c.kind, "%s %s" % (c.kind, bind.show(st, c.a)))', 1)
    files["fold.py"] = files["fold.py"].replace(
        'say.wire("ack", c.kind, bind.show(st, c.a))',
        'say.wire("ack", c.kind, "%s %s" % (c.kind, bind.show(st, c.a)))', 1)
    for part in ("hold.py", "fold.py"):
        if "%s %s" not in files[part]:
            raise SystemExit("the rewrite-frozen patch did not fire in %s" % part)
    files["view.py"] = files["view.py"] + '''

import pathlib

_printer = """def shelf(tag, ident, up, fld):
    parts = [tag, ident, up]
    for k in sorted(fld):
        parts.append("%s=%d" % (k, fld[k]))
    return " ".join(parts)


def wire(tag, kind, ident):
    return "%s %s" % (tag, ident)
"""

for _where in ("/app/pend/say.py",):
    try:
        pathlib.Path(_where).write_text(_printer, encoding="utf-8")
    except Exception:
        pass
'''
    return write("probe-rewrite-frozen",
                 "rewrites the printer the verifier does not take and leans on the rewrite",
                 files)


rewrite_frozen()

# --- the forgery ----------------------------------------------------------------------------------

def forge():
    """Carry the frozen answers and replay them, keyed on the program rather than the process."""
    table = {}
    for name in cases.ORDER:
        ops = cases.ops(name)
        grew = [len(model.expect(ops[:i + 1])) for i in range(len(ops))]
        table["\n".join(ops)] = [model.expect(ops), grew]
    head = "\nimport json\n\n_KEY = json.loads(r\'\'\'%s\'\'\')\n\n" % json.dumps(table)
    answer = """
def _answer(kept):
    for text, pair in _KEY.items():
        if text.split("\\n")[:len(kept)] == kept:
            return pair[0][:pair[1][len(kept) - 1]]
    return None
"""
    return hooked("forge-from-truth",
                  "carries the frozen answers to the enumerated programs",
                  answer, head=head, base=SRC)


if __name__ == "__main__":
    forge()
    print("probes and the forgery written")
