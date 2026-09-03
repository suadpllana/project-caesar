"""Drive the rebuilt fabric over every feed and publish one report.

This is the only process that executes anything the agent wrote. It runs as an
unprivileged uid, in its own session, under a wall clock, and it writes into a
descriptor root opened before the privilege drop. Nothing here can learn what a
feed is supposed to produce: `oracle.py`, `gt.json` and `test_outputs.py` are
root-only, so the expected rows are not on this side of the fence at all.

The feed list is in two halves. `cases.py` is the named half and the run may read
it - knowing which feeds execute yields none of their rows. `gen.py` builds the
rest from a nonce `test.sh` draws from /dev/urandom after the agent has stopped,
and hands the same nonce to the grader, so both sides build the identical batch
and neither side could have held it while the submission was being written.

The report comes out of the process under examination, so four things travel with
it and the grader believes none of them on their own.

  Rows reach the trace only through an appender made here, which refuses any
  caller whose frame is not the driver's own code. The submission never holds the
  list and cannot hand back one of its own.

  Digests of the sealed functions as they exist in this interpreter, taken once
  the tree is imported and again when the feed ends. A rebind between those two
  points is caught by the pair; a rebind that happens at import time, before the
  first digest, is not, which is why the grader derives its own baseline by
  compiling the untouched sources outside this process.

  A count kept by the interpreter, in a closure the tree has no name for, of how
  often the sealed writers actually ran, together with whether that
  instrumentation was still registered and still armed when the feed ended.
  Turning it off has to fail rather than pass quietly.

  Every exception, per feed, so a tree that will not import reads as a tree that
  will not import rather than as a clean sweep of empty reports.
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

import cases
import gen

SEALED = (
    ("base/tape.py", "seat"),
    ("base/tape.py", "make"),
    ("base/tape.py", "put"),
    ("base/tape.py", "mix"),
    ("base/tape.py", "read"),
    ("base/wire.py", "band"),
    ("base/wire.py", "pack"),
    ("base/wire.py", "held"),
    ("base/drv.py", "run"),
    ("base/drv.py", "flush"),
    ("base/drv.py", "tail"),
)

COUNTED = ("make", "pack", "run")
SLOT = 3


class Trace(object):
    """The rows. Only the driver may put one here."""

    def __init__(self, *doors):
        self.doors = doors
        self.rows = []

    def put(self, row):
        if sys._getframe(1).f_code not in self.doors:
            raise RuntimeError("row from outside the driver")
        self.rows.append(row)


def chew(code):
    pot = hashlib.sha256()
    pot.update(code.co_code)
    pot.update(repr(code.co_names).encode("utf-8"))
    pot.update(repr(code.co_varnames).encode("utf-8"))
    for bit in code.co_consts:
        if isinstance(bit, types.CodeType):
            pot.update(chew(bit).encode("utf-8"))
        else:
            pot.update(repr(bit).encode("utf-8"))
    return pot.hexdigest()


def knot(book):
    pot = hashlib.sha256()
    for key in sorted(book):
        pot.update((key + "@" + book[key] + "|").encode("utf-8"))
    return pot.hexdigest()


def reach(where, path):
    thing = where
    for hop in path.split("."):
        thing = getattr(thing, hop)
    return thing


def stamp():
    book = {}
    for rel, path in SEALED:
        key = rel + "::" + path
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            book[key] = "absent"
            continue
        try:
            book[key] = chew(reach(mod, path).__code__)
        except AttributeError:
            book[key] = "swapped"
    return book


def meter(codes):
    """Let the interpreter count, from a closure with no name in the tree."""
    seen = {}
    mon = getattr(sys, "monitoring", None)

    if mon is None:
        wanted = set(codes)

        def peek(frame, kind, arg):
            if kind == "call" and frame.f_code in wanted:
                name = frame.f_code.co_name
                seen[name] = seen.get(name, 0) + 1
            return None

        sys.setprofile(peek)

        def halt():
            on = sys.getprofile() is peek
            sys.setprofile(None)
            return {"on": on, "via": "profile", "seen": dict(seen)}

        return halt

    def peek(code, offset):
        seen[code.co_name] = seen.get(code.co_name, 0) + 1
        return None

    try:
        mon.use_tool_id(SLOT, "gate-check")
    except ValueError:
        pass
    mon.register_callback(SLOT, mon.events.PY_START, peek)
    for code in codes:
        mon.set_local_events(SLOT, code, mon.events.PY_START)

    def halt():
        on = True
        try:
            if mon.get_tool(SLOT) != "gate-check":
                on = False
            if mon.register_callback(SLOT, mon.events.PY_START, peek) is not peek:
                on = False
            for code in codes:
                if not mon.get_local_events(SLOT, code) & mon.events.PY_START:
                    on = False
                mon.set_local_events(SLOT, code, 0)
            mon.register_callback(SLOT, mon.events.PY_START, None)
        except (ValueError, TypeError):
            on = False
        try:
            mon.free_tool_id(SLOT)
        except (ValueError, TypeError):
            on = False
        return {"on": on, "via": "monitoring", "seen": dict(seen)}

    return halt


def clear():
    dead = [n for n in sys.modules
            if n in ("base", "bay") or n.startswith(("base.", "bay."))]
    for name in dead:
        sys.modules.pop(name, None)


def drive(text):
    clear()
    from base import drv, tape, wire
    opened = stamp()
    trace = Trace(drv.run.__code__, drv.flush.__code__)
    halt = meter([tape.make.__code__, wire.pack.__code__, drv.run.__code__])
    try:
        st = drv.run(text, trace.put)
        tail = drv.tail(st)
    finally:
        state = halt()
    return {
        "rows": [list(r) for r in trace.rows],
        "tail": [list(t) for t in tail],
        "in": knot(opened),
        "out": knot(stamp()),
        "ran": dict((k, state["seen"].get(k, 0)) for k in COUNTED),
        "on": state["on"],
        "via": state["via"],
    }


def sheet(nonce, many):
    work = [(name, cases.FEEDS[name]) for name in sorted(cases.FEEDS)]
    work.extend(gen.batch(nonce, many))
    return work


def one(code):
    """Under this name because the grader builds its baseline through it."""
    return chew(code)


def tie(book):
    """Likewise, for folding that baseline into a single value."""
    return knot(book)


def issue(where, load):
    raw = json.dumps(load, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if not where.startswith("fd:"):
        with open(where, "wb") as fh:
            fh.write(raw)
        return
    fd = int(where[3:])
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, raw)


def main(argv):
    where = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    many = int(os.environ.get("RUN_COUNT", "300"))
    good, hurt = {}, {}
    for name, text in sheet(nonce, many):
        try:
            good[name] = drive(text)
        except Exception:
            hurt[name] = traceback.format_exc()[-1500:]
    issue(where, {"nonce": nonce, "count": many,
                  "reports": good, "errors": hurt})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
