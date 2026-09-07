"""Drive the rebuilt engine over every script and hand back what it printed.

This is the one process that runs anything the submission wrote. It is unprivileged, it
sits in a session of its own under a wall clock, the tree beneath it is read-only, and the
file it reports into was opened by root and passed down as a descriptor, so nothing it can
reach is anything the verdict is read from. It also cannot learn a single expected line:
the ground truth, the sealed model and the grader are root's.

Because the printed lines are produced inside this process, three things about the process
itself travel back with them:

  the ledger    a line is accepted only from Run.step's own code object, so a submission
                cannot print a line of its own;
  the count     the interpreter's own count of entries into Run.step, held outside the
                engine's reach, with a flag saying the counter was still armed at the end;
  the seal      every frozen function hashed as this interpreter holds it, once before the
                script and once after, against which the grader sets digests it compiles
                from the untouched sources.
"""

import hashlib
import json
import os
import sys
import traceback
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
TREE = os.environ.get("APPDIR", "/app")
sys.path.insert(0, TREE)
sys.path.insert(0, ROOT)

import cases  # noqa: E402
import gen  # noqa: E402

# The functions the submission is not allowed to have replaced, by file and qualified name.
# The grader recomputes each digest by compiling the untouched source and running nothing.
FROZEN = (
    ("sheet/core.py", "Run.__init__"),
    ("sheet/core.py", "Run.step"),
    ("sheet/core.py", "Run.run"),
    ("sheet/grid.py", "Sheet.put"),
    ("sheet/grid.py", "Sheet.clr"),
    ("sheet/grid.py", "Sheet.held"),
    ("sheet/grid.py", "Sheet.owners"),
    ("sheet/grid.py", "show"),
    ("sheet/grid.py", "items"),
    ("sheet/grid.py", "shape"),
    ("sheet/addr.py", "parse"),
    ("sheet/addr.py", "name"),
    ("sheet/addr.py", "walk"),
    ("sheet/addr.py", "span"),
    ("sheet/form.py", "build"),
    ("sheet/form.py", "chop"),
    ("sheet/form.py", "atom"),
)
SLOT = 4
BADGE = "sheet-run"


def digest(code):
    """Hash a code object by what it does, not by where it came from. Nested code is
    recursed into rather than repr'd: the repr of a code object carries its filename and
    its address, so anything holding a comprehension would hash differently every run."""
    parts = [code.co_code, repr(code.co_names).encode(), repr(code.co_varnames).encode()]
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            parts.append(digest(const).encode())
        else:
            parts.append(repr(const).encode())
    return hashlib.sha256(b"\x00".join(parts)).hexdigest()


def seal():
    marks = []
    for rel, qual in FROZEN:
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        state = "absent"
        if mod is not None:
            here = mod
            try:
                for part in qual.split("."):
                    here = getattr(here, part)
                state = digest(here.__code__)
            except AttributeError:
                state = "replaced"
        marks.append("%s#%s=%s" % (rel, qual, state))
    return hashlib.sha256("\n".join(sorted(marks)).encode()).hexdigest()


class Ledger:
    """The only thing allowed to record a printed line. The caller's code object has to be
    the driver's own step, so a submission cannot append to what it is graded on."""

    def __init__(self, allowed):
        self.allowed = allowed
        self.lines = []

    def __call__(self, row):
        if sys._getframe(1).f_code is not self.allowed:
            raise RuntimeError("a line arrived from somewhere that is not the driver")
        self.lines.append("%d %s %s | %s" % row)


class Counter:
    """Counts entries into one code object through the interpreter, not through the tree.
    The callback is bound once here: attribute access on a method makes a new object each
    time, and the identity check in close() would then never hold."""

    def __init__(self, code):
        self.code = code
        self.hits = 0
        self.live = hasattr(sys, "monitoring")
        self.on_start = self._on_start
        self.on_call = self._on_call

    def _on_start(self, code, offset):
        self.hits += 1

    def _on_call(self, frame, event, arg):
        if event == "call" and frame.f_code is self.code:
            self.hits += 1

    def open(self):
        if not self.live:
            sys.setprofile(self.on_call)
            return
        mon = sys.monitoring
        try:
            mon.use_tool_id(SLOT, BADGE)
        except ValueError:
            pass
        mon.register_callback(SLOT, mon.events.PY_START, self.on_start)
        mon.set_local_events(SLOT, self.code, mon.events.PY_START)

    def close(self):
        intact = True
        try:
            if not self.live:
                intact = sys.getprofile() is self.on_call
                sys.setprofile(None)
                return intact, "profile", self.hits
            mon = sys.monitoring
            if mon.get_tool(SLOT) != BADGE:
                intact = False
            if mon.register_callback(SLOT, mon.events.PY_START,
                                     self.on_start) is not self.on_start:
                intact = False
            if not (mon.get_local_events(SLOT, self.code) & mon.events.PY_START):
                intact = False
            mon.set_local_events(SLOT, self.code, 0)
            mon.register_callback(SLOT, mon.events.PY_START, None)
            mon.free_tool_id(SLOT)
        except Exception:
            intact = False
        return intact, "monitoring", self.hits


def unload():
    for name in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
        del sys.modules[name]


def once(text):
    unload()
    from sheet.core import Run
    opening = seal()
    ledger = Ledger(Run.step.__code__)
    counter = Counter(Run.step.__code__)
    counter.open()
    try:
        Run(ledger).run(text.split("\n"))
    finally:
        intact, how, hits = counter.close()
    return {
        "gr": ledger.lines,
        "sealed": opening,
        "resealed": seal(),
        "steps": hits,
        "armed": intact,
        "how": how,
    }


def plan(nonce, count):
    out = [(name, cases.CASES[name]) for name in sorted(cases.CASES)]
    out.extend(gen.batch("sheet-v1", count))
    return out


def hand_back(where, body):
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    if where.startswith("fd:"):
        fd = int(where[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, blob)
        return
    with open(where, "wb") as fh:
        fh.write(blob)


def main(argv):
    where = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "120"))
    grids, faults = {}, {}
    for name, text in plan(nonce, count):
        try:
            grids[name] = once(text)
        except Exception:
            faults[name] = traceback.format_exc()[-1000:]
    hand_back(where, {"nonce": nonce, "count": count, "grids": grids, "faults": faults})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
