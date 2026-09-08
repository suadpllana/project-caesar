"""Drives the rebuilt engine over every scenario and reports what it printed.

This is the only process that executes anything the agent wrote. It runs unprivileged, in
its own session, under a wall clock timeout, in a work tree it cannot write, and it reports
into a descriptor root opened before the privilege drop. It never knows an expected trace:
gt.json, model.py, gen.py, cases.py and test_outputs.py are unreadable to it.

Besides the traces, three things are attested from inside this process, because the traces
are produced inside it:

  the sink      a row may only be appended by drive.go's own code object, so a submission
                cannot write its own trace;
  the tally     the interpreter's own count of entries into drive.go and lay.do, kept where
                the tree cannot reach it, with a flag saying whether the instrumentation was
                still armed when the last scenario ended;
  the digests   every frozen function hashed as it exists in this interpreter, on import and
                again when each scenario has run, for the grader to hold against digests it
                compiles from the pristine sources.
"""

import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get("APPDIR", "/app")
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import seal  # noqa: E402

TOOL = 4
COUNTED = ("go", "do")


def snapshot():
    out = {}
    for rel, qual in seal.FROZEN:
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        key = "%s#%s" % (rel, qual)
        if mod is None:
            out[key] = "absent"
            continue
        obj = mod
        try:
            for part in qual.split("."):
                obj = getattr(obj, part)
            out[key] = seal.digest(obj.__code__)
        except AttributeError:
            out[key] = "replaced"
    return seal.stamp(out)


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
            mon.use_tool_id(TOOL, "merge")
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
                ok = mon.get_tool(TOOL) == "merge"
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


def sink(gocode):
    rows = []

    def put(row):
        if sys._getframe(1).f_code is not gocode:
            raise RuntimeError("trace")
        rows.append(row)

    return rows, put


def fresh():
    for name in [n for n in sys.modules if n == "mrg" or n.startswith("mrg.")]:
        del sys.modules[name]


def drive(text):
    fresh()
    from mrg import drive as engine
    from mrg import lay
    before = snapshot()
    rows, put = sink(engine.go.__code__)
    meter = Meter([engine.go.__code__, lay.do.__code__])
    meter.start()
    try:
        engine.go(text.split("\n"), put)
    finally:
        armed, how, tally = meter.stop()
    return {
        "tr": list(rows),
        "fp": before,
        "fp2": snapshot(),
        "mon": dict((k, tally.get(k, 0)) for k in COUNTED),
        "arm": armed,
        "how": how,
    }


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
    with open(os.environ.get("PLAN", "/work/run/plan.json"), encoding="utf-8") as fh:
        plan = json.load(fh)
    traces, faults = {}, {}
    for item in plan:
        try:
            traces[item["name"]] = drive(item["text"])
        except Exception:
            faults[item["name"]] = traceback.format_exc()[-800:]
    deliver(target, {"nonce": nonce, "count": len(plan), "traces": traces, "faults": faults})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
