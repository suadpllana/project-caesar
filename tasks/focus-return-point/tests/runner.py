"""Drives the rebuilt toolkit over every script and reports the trails.

This is the only process that executes anything the agent wrote. It runs unprivileged,
in its own session, under a wall clock timeout, in a work tree it cannot write, and it
reports into a descriptor that root opened before the privilege drop. It never knows an
expected trail: gt.json, oracle.py and test_outputs.py are unreadable to it.

Two script sets are driven. The enumerated ones come from cases.py, which the run may
read - knowing which scripts run does not produce their trails. The rest come from gen.py
and the run nonce, made from /dev/urandom in the verifier container after the agent has
finished, so they did not exist when the submission was written.

Besides the trails, three things are attested from inside this process, because the
trails are produced inside it:

  the sink      rows may only be appended by Ui.step's own code object, so a submission
                cannot write its own trail;
  the tally     the interpreter's own count of entries into Ui.step, kept where the tree
                cannot reach it, with a flag saying whether the instrumentation was still
                armed when the script ended;
  the digests   every frozen function hashed as it exists in this interpreter, on import
                and again when each script has run, for the grader to hold against digests
                it compiles from the pristine sources.
"""

import hashlib
import json
import os
import sys
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get("APPDIR", "/app")
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import cases  # noqa: E402
import gen  # noqa: E402

# Frozen functions, named by file and qualified name. The grader imports this tuple and
# derives the expected digest of each by compiling the pristine source, executing nothing.
FROZEN = (
    ("ui/core.py", "Ui.__init__"),
    ("ui/core.py", "Ui.screen"),
    ("ui/core.py", "Ui.make"),
    ("ui/core.py", "Ui.holder"),
    ("ui/core.py", "Ui.land"),
    ("ui/core.py", "Ui.forget"),
    ("ui/core.py", "Ui.step"),
    ("ui/core.py", "Ui.run"),
    ("ui/decl.py", "flags"),
    ("ui/decl.py", "load"),
    ("ui/decl.py", "event"),
    ("ui/node.py", "Nd.__init__"),
    ("ui/node.py", "Scr.__init__"),
    ("ui/node.py", "Ev.__init__"),
)
TOOL = 4
COUNTED = ("step", "land")


def digest(code):
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(repr(code.co_names).encode())
    h.update(repr(code.co_varnames).encode())
    for k in code.co_consts:
        h.update((digest(k) if isinstance(k, types.CodeType) else repr(k)).encode())
    return h.hexdigest()


def stamp(book):
    h = hashlib.sha256()
    for k in sorted(book):
        h.update(("%s:%s|" % (k, book[k])).encode())
    return h.hexdigest()


def snapshot():
    out = {}
    for rel, qual in FROZEN:
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        key = "%s#%s" % (rel, qual)
        if mod is None:
            out[key] = "absent"
            continue
        obj = mod
        try:
            for part in qual.split("."):
                obj = getattr(obj, part)
            out[key] = digest(obj.__code__)
        except AttributeError:
            out[key] = "replaced"
    return stamp(out)


class Meter:
    """Counts entries into a few code objects. The callback is bound exactly once, in
    __init__, because a bound method is a fresh object on every attribute access and the
    identity check in stop() would otherwise always fail."""

    def __init__(self, codes):
        self.tally = {}
        self.codes = list(codes)
        self.wanted = set(codes)
        self.hook = self._hook
        self.prof = self._prof
        self.how = "monitoring" if hasattr(sys, "monitoring") else "profile"

    def _hook(self, code, offset):
        self.tally[code.co_name] = self.tally.get(code.co_name, 0) + 1

    def _prof(self, frame, event, arg):
        if event == "call" and frame.f_code in self.wanted:
            nm = frame.f_code.co_name
            self.tally[nm] = self.tally.get(nm, 0) + 1

    def start(self):
        if self.how == "profile":
            sys.setprofile(self.prof)
            return
        mon = sys.monitoring
        try:
            mon.use_tool_id(TOOL, "trail")
        except ValueError:
            pass
        mon.register_callback(TOOL, mon.events.PY_START, self.hook)
        for code in self.codes:
            mon.set_local_events(TOOL, code, mon.events.PY_START)

    def stop(self):
        ok = True
        try:
            if self.how == "profile":
                ok = sys.getprofile() is self.prof
                sys.setprofile(None)
            else:
                mon = sys.monitoring
                ok = mon.get_tool(TOOL) == "trail"
                if mon.register_callback(TOOL, mon.events.PY_START, self.hook) is not self.hook:
                    ok = False
                for code in self.codes:
                    if not (mon.get_local_events(TOOL, code) & mon.events.PY_START):
                        ok = False
                    mon.set_local_events(TOOL, code, 0)
                mon.register_callback(TOOL, mon.events.PY_START, None)
                mon.free_tool_id(TOOL)
        except Exception:
            ok = False
        return ok, self.how, dict(self.tally)


def sink(stepcode):
    rows = []

    def put(row):
        if sys._getframe(1).f_code is not stepcode:
            raise RuntimeError("trail")
        rows.append(row)

    return rows, put


def fresh():
    for n in list(sys.modules):
        if n == "ui" or n.startswith("ui."):
            del sys.modules[n]


def drive(text):
    fresh()
    from ui.core import Ui
    before = snapshot()
    rows, put = sink(Ui.step.__code__)
    meter = Meter([Ui.step.__code__, Ui.land.__code__])
    meter.start()
    try:
        ui = Ui(put)
        ui.run(text.split("\n"))
    finally:
        armed, how, tally = meter.stop()
    return {
        "tr": [str(fo) for _, _, fo in rows],
        "fp": before,
        "fp2": snapshot(),
        "mon": dict((k, tally.get(k, 0)) for k in COUNTED),
        "arm": armed,
        "how": how,
    }


def plan(nonce, count):
    out = [(nm, cases.CASES[nm]) for nm in sorted(cases.CASES)]
    out.extend(gen.batch(nonce, count))
    return out


def deliver(target, body):
    text = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    if target.startswith("fd:"):
        fd = int(target[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text)
    else:
        with open(target, "wb") as fh:
            fh.write(text)


def main(argv):
    target = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    trails, faults = {}, {}
    for name, text in plan(nonce, count):
        try:
            trails[name] = drive(text)
        except Exception:
            faults[name] = traceback.format_exc()[-1000:]
    deliver(target, {"nonce": nonce, "count": count, "trails": trails, "faults": faults})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
