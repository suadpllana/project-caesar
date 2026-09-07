"""Drives the rebuilt engine over every graded script and reports what it did.

This is the only process that executes anything the submission wrote. It runs as an
unprivileged uid, in its own session, under a wall clock, over a work tree it cannot
write, and it reports through a descriptor root opened before the privilege drop. It
never learns an expected report: gt.json, oracle.py and test_outputs.py are unreadable
to it.

Three things are attested from inside this process, because the reports are produced
here and nowhere else:

  the sink     a report line may only be appended by the frozen driver's own code
               object, so a submission cannot write its own report;
  the tally    the interpreter's count of entries into the driver, the per-edit step and
               the one function that performs a recomputation, with a flag saying whether
               the instrumentation was still armed when the script ended;
  the digests  every frozen function hashed as it exists in this interpreter, once on
               import and again after the script has run, for the grader to hold against
               digests it compiles from the pristine sources.
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

# Frozen functions, named by file and qualified name. The grader derives each expected
# digest by compiling the pristine source; nothing is executed to obtain it.
FROZEN = (
    ("sheet/core.py", "Eng.__init__"),
    ("sheet/core.py", "Eng.calc"),
    ("sheet/core.py", "Eng.step"),
    ("sheet/core.py", "drive"),
    ("sheet/store.py", "St.__init__"),
    ("sheet/store.py", "St.own"),
    ("sheet/store.py", "St.node"),
    ("sheet/store.py", "St.val"),
    ("sheet/store.py", "St.show"),
    ("sheet/store.py", "sho"),
    ("sheet/expr.py", "lex"),
    ("sheet/expr.py", "parse"),
    ("sheet/expr.py", "gather"),
    ("sheet/expr.py", "sc"),
    ("sheet/expr.py", "blk"),
    ("sheet/expr.py", "run"),
    ("sheet/expr.py", "P.add"),
    ("sheet/expr.py", "P.mul"),
    ("sheet/expr.py", "P.atom"),
    ("sheet/adr.py", "pa"),
    ("sheet/adr.py", "fa"),
    ("sheet/adr.py", "span"),
)
TOOL = 5
COUNTED = ("drive", "step", "calc")
WIDE = 3


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
        h.update(("%s=%s;" % (k, book[k])).encode())
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
    """Counts entries into a few code objects. The callback is bound once, in __init__:
    a bound method is a new object on every attribute lookup, so the identity check in
    stop() would otherwise never hold."""

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
            mon.use_tool_id(TOOL, "grid")
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
                ok = mon.get_tool(TOOL) == "grid"
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


def sink(owner):
    rows = []

    def put(row):
        if sys._getframe(1).f_code is not owner:
            raise RuntimeError("report")
        rows.append(row)

    return rows, put


def fresh():
    for n in list(sys.modules):
        if n == "sheet" or n.startswith("sheet."):
            del sys.modules[n]


def drive(text):
    fresh()
    from sheet import core
    before = snapshot()
    rows, put = sink(core.drive.__code__)
    meter = Meter([core.drive.__code__, core.Eng.step.__code__, core.Eng.calc.__code__])
    meter.start()
    try:
        core.drive(text.split("\n"), put)
    finally:
        armed, how, tally = meter.stop()
    return {
        "rp": [str(r) for r in rows],
        "fp": before,
        "fp2": snapshot(),
        "mon": dict((k, tally.get(k, 0)) for k in COUNTED),
        "arm": armed,
        "how": how,
    }


def plan(nonce, count):
    out = [(nm, cases.CASES[nm]) for nm in sorted(cases.CASES)]
    out.extend(gen.batch("sheet-v1", count))
    for i in range(WIDE):
        out.append(("wide-%02d" % i, gen.wide("wide-v1|%d" % i)))
    return out


def deliver(target, body):
    text = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    if target.startswith("fd:"):
        fd = int(target[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text)
        return
    with open(target, "wb") as fh:
        fh.write(text)


def main(argv):
    target = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "60"))
    done, faults = {}, {}
    for name, text in plan(nonce, count):
        try:
            done[name] = drive(text)
        except Exception:
            faults[name] = traceback.format_exc()[-1200:]
    deliver(target, {"nonce": nonce, "count": count, "runs": done, "faults": faults})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
