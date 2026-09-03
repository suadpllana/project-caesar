"""Drives the submitted server over every job and reports what it did.

This is the only place agent code runs. It runs as an unprivileged uid, in its own session,
against a tree it cannot write, and it reports through a descriptor root opened before the
privilege drop. Nothing here decides anything: it records, and grading happens afterwards as
root in a process that never imports any of it.

Three things are attested alongside the traces, because a trace that comes back from the
agent's own process is a claim rather than evidence.

  drives   the interpreter's own count of entries into the sealed driver, kept in a closure
           this module owns rather than in the tree, so a submission cannot reach it by name.
  answers  the same count for the sealed tool. It has to equal the number of dispatch rows,
           which is what says a dispatch in the trace was a dispatch that happened.
  marks    a digest of each sealed function as it actually exists in the running interpreter,
           taken when the tree is imported and again when the last job ends. The grader
           compares these against digests it derives by compiling the pristine sources, which
           is the part a rebind at import time cannot get in front of.
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.environ.get("APPDIR", "/work/app"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases  # noqa: E402
import gen  # noqa: E402

TOOL_ID = 3
SEALED = ("drive", "answer", "load")


def digest(code, out=None):
    """A digest of a code object that does not depend on where the file sat on disk."""
    if out is None:
        out = hashlib.sha256()
    out.update(code.co_code)
    out.update(repr(code.co_names).encode())
    out.update(repr(code.co_varnames).encode())
    out.update(repr(code.co_argcount).encode())
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            digest(const, out)
        else:
            out.update(repr(const).encode())
    return out


def marks(wire):
    return {nm: digest(getattr(wire, nm).__code__).hexdigest() for nm in SEALED}


def counter(wire):
    """Arm the interpreter's own instrumentation. The tally lives in this closure."""
    tally = {"drive": 0, "answer": 0}
    want = {wire.drive.__code__: "drive", wire.answer.__code__: "answer"}
    state = {"armed": False, "how": "none"}

    def bump(code, offset):
        nm = want.get(code)
        if nm is not None:
            tally[nm] += 1
        return getattr(sys, "monitoring", None) and sys.monitoring.DISABLE

    mon = getattr(sys, "monitoring", None)
    if mon is not None and hasattr(mon, "use_tool_id"):
        mon.use_tool_id(TOOL_ID, "holdcheck")

        def on_start(code, offset):
            nm = want.get(code)
            if nm is not None:
                tally[nm] += 1
        mon.register_callback(TOOL_ID, mon.events.PY_START, on_start)
        mon.set_events(TOOL_ID, mon.events.PY_START)
        state["armed"] = True
        state["how"] = "monitoring"
    else:
        def hook(frame, event, arg):
            if event == "call":
                nm = want.get(frame.f_code)
                if nm is not None:
                    tally[nm] += 1
        sys.setprofile(hook)
        state["armed"] = True
        state["how"] = "profile"

    def disarm():
        try:
            if state["how"] == "monitoring":
                still = mon.get_events(TOOL_ID) != 0
                mon.set_events(TOOL_ID, 0)
                mon.register_callback(TOOL_ID, mon.events.PY_START, None)
                mon.free_tool_id(TOOL_ID)
            else:
                still = sys.getprofile() is not None
                sys.setprofile(None)
        except Exception:
            still = False
        state["armed"] = bool(still)
        return tally, state

    return disarm


def main(target):
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    if os.environ.get("REQUIRE_MONITORING") and not hasattr(sys, "monitoring"):
        raise SystemExit("monitoring required")

    from srv import wire
    early = marks(wire)
    disarm = counter(wire)

    runs = {}
    for name, job in cases.jobs():
        try:
            runs[name] = wire.drive(job)
        except Exception as exc:
            runs[name] = [["boom", type(exc).__name__]]
    for name, job in gen.jobs(nonce, count):
        try:
            runs[name] = wire.drive(job)
        except Exception as exc:
            runs[name] = [["boom", type(exc).__name__]]

    late = marks(wire)
    tally, state = disarm()
    blob = json.dumps({
        "nonce": nonce,
        "count": count,
        "runs": runs,
        "arm": state["armed"],
        "how": state["how"],
        "drives": tally["drive"],
        "answers": tally["answer"],
        "early": early,
        "late": late,
    }, separators=(",", ":"))
    if target.startswith("fd:"):
        os.write(int(target[3:]), blob.encode())
    else:
        with open(target, "w") as fh:
            fh.write(blob)


if __name__ == "__main__":
    main(sys.argv[1])
