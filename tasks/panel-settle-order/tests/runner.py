"""The only process that executes anything the submission wrote.

It runs unprivileged, in its own session, under a wall clock, against a tree it cannot
write, and it reports through a descriptor root opened before privilege was dropped: the
uid running the panels does not own the file it is graded on and cannot reopen it.

It never learns what any panel is supposed to do. oracle.py, gt.json and test_outputs.py
are root-only, so nothing in this process can compare its work against an answer.

Four things are reported beside the trace, because the trace comes back from the same
process that ran the submission and a report is never its own evidence.

  ledger    Rows are appended by a closure created here. It reads the calling frame and
            refuses anyone but the loop's own emitter, so a submission cannot write a row
            without going through the code that does the work the row describes.

  counted   The interpreter counts entries into that emitter, in a closure held here and
            reachable from nowhere in the tree, and reports whether the instrumentation
            was still registered and still armed when the last panel ended. Switching it
            off is an act the report shows rather than a silence.

  stamps    Every sealed function is hashed as it actually exists in this interpreter,
            once at import and again after every panel, so rebinding one to a quiet copy
            is caught the way editing its file already is.

  tree      Every file of the executed tree outside the four declared artifacts, hashed
            after the last panel.
"""

import hashlib
import importlib
import json
import os
import sys
import traceback

# Read with defaults rather than by subscript: the grader imports this module for the
# sealed-function list and for the panel plan, and it does so in a process that has none of
# these set. An import that dies there fails the whole trial before a single panel runs.
TREE = os.environ.get("APPDIR", "/app")
NONCE = os.environ.get("PSO_NONCE", "")
COUNT = int(os.environ.get("PSO_COUNT", "300"))
FD = int(os.environ.get("OUTFD", "1"))
STRICT = os.environ.get("REQUIRE_MONITORING") == "1"
TOOL = 4

ARTIFACTS = ("ord.py", "wire.py", "trip.py", "same.py")
SEALED = (("loop", "Loop.say"), ("loop", "Loop.spin"), ("loop", "Loop.turn"),
          ("loop", "Loop.build"), ("loop", "Loop.go"), ("loop", "Loop.pop"),
          ("loop", "Loop.by"), ("net", "Net.fire"), ("net", "Net.__init__"),
          ("ev", "run"), ("lex", "parse"))

sys.path.insert(0, "/tests")
import cases  # noqa: E402
import gen  # noqa: E402


def stamp(fn):
    c = fn.__code__
    flat = [repr(x) for x in c.co_consts if not hasattr(x, "co_code")]
    blob = b"|".join([c.co_code, repr(c.co_names).encode(),
                      repr(c.co_varnames).encode(), repr(sorted(flat)).encode()])
    return hashlib.sha256(blob).hexdigest()[:32]


def reach(mods, where):
    mod, path = where
    obj = mods[mod]
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def stamps_now(mods):
    out = {}
    for where in SEALED:
        key = "%s.%s" % where
        try:
            out[key] = stamp(reach(mods, where))
        except Exception:
            out[key] = "gone"
    return out


class Count:
    """Interpreter-level tally, held here and never anywhere in the tree."""

    def __init__(self):
        self.hits = 0
        self.mode = "none"
        self.code = None
        # Bind the fallback hook once. Reading self._prof again would make a fresh bound
        # method every time, so an identity check against sys.getprofile() could never
        # hold and the run would report itself disturbed on any interpreter without
        # sys.monitoring.
        self.hook = self._prof

    def arm(self, mods):
        self.code = mods["loop"].Loop.say.__code__
        mon = getattr(sys, "monitoring", None)
        if mon is None:
            if STRICT:
                raise RuntimeError("sys.monitoring is required and is absent")
            sys.setprofile(self.hook)
            self.mode = "profile"
            return
        mon.use_tool_id(TOOL, "pso")
        mon.register_callback(TOOL, mon.events.PY_START, self._hit)
        mon.set_local_events(TOOL, self.code, mon.events.PY_START)
        self.mode = "monitoring"

    def follow(self, mods):
        code = mods["loop"].Loop.say.__code__
        self.code = code
        mon = getattr(sys, "monitoring", None)
        if self.mode == "monitoring" and mon is not None:
            mon.set_local_events(TOOL, code, mon.events.PY_START)

    def _hit(self, code, offset):
        self.hits += 1

    def _prof(self, frame, event, arg):
        if event == "call" and frame.f_code is self.code:
            self.hits += 1

    def intact(self):
        mon = getattr(sys, "monitoring", None)
        if self.mode == "monitoring" and mon is not None:
            try:
                ok = (mon.get_tool(TOOL) == "pso"
                      and bool(mon.get_local_events(TOOL, self.code) & mon.events.PY_START))
            except Exception:
                ok = False
            try:
                mon.set_local_events(TOOL, self.code, 0)
                mon.register_callback(TOOL, mon.events.PY_START, None)
                mon.free_tool_id(TOOL)
            except Exception:
                pass
            return ok
        if self.mode == "profile":
            ok = sys.getprofile() is self.hook
            sys.setprofile(None)
            return ok
        return False


def sink(rows, code):
    def put(row):
        if sys._getframe(1).f_code is not code:
            raise RuntimeError("a ledger row was offered by something other than the loop")
        rows.append(tuple(row))
    return put


def fresh():
    for name in [m for m in sorted(sys.modules) if m == "pnl" or m.startswith("pnl.")]:
        del sys.modules[name]
    mods = {}
    for name in ("lex", "ev", "net", "loop", "ord", "wire", "trip", "same"):
        mods[name] = importlib.import_module("pnl." + name)
    return mods


def digest():
    parts = []
    for base, dirs, files in os.walk(TREE):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(base, f), TREE).replace(os.sep, "/")
            if rel.startswith("pnl/") and os.path.basename(rel) in ARTIFACTS:
                continue
            if f.endswith(".pyc"):
                continue
            with open(os.path.join(base, f), "rb") as fh:
                parts.append(rel + ":" + hashlib.sha256(fh.read()).hexdigest())
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def plan():
    out = [(n, cases.PANELS[n]) for n in sorted(cases.PANELS)]
    out += gen.build(NONCE, COUNT)
    return out


def main():
    sys.path.insert(0, TREE)
    report = {"nonce": NONCE, "count": COUNT, "runs": {}, "fault": None}
    tally = Count()
    first = None
    drift = []
    rows_total = 0
    try:
        for name, text in plan():
            mods = fresh()
            if first is None:
                first = stamps_now(mods)
                tally.arm(mods)
            else:
                tally.follow(mods)
            rows = []
            entry = {"log": rows, "dump": [], "err": None}
            try:
                feeds, gauges, latch, rounds, order = mods["lex"].parse(text)
                lp = mods["loop"].Loop(feeds, gauges, latch, rounds, order,
                                       sink(rows, mods["loop"].Loop.say.__code__))
                entry["dump"] = [list(x) for x in lp.go()]
            except Exception as exc:
                entry["err"] = "%s: %s" % (type(exc).__name__, exc)
            entry["log"] = [list(r) for r in rows]
            rows_total += len(rows)
            report["runs"][name] = entry
            now = stamps_now(mods)
            if now != first and not drift:
                drift.append(now)
    except Exception:
        report["fault"] = traceback.format_exc()[-2000:]
    report["armed"] = tally.intact()
    report["mode"] = tally.mode
    report["said"] = tally.hits
    report["rows"] = rows_total
    report["stamps"] = first or {}
    report["drift"] = drift
    try:
        report["tree"] = digest()
    except Exception as exc:
        report["tree"] = "unreadable: %s" % type(exc).__name__
    with os.fdopen(os.dup(FD), "w") as fh:
        json.dump(report, fh)
        fh.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
