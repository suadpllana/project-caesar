"""Drive the rebuilt machine over every report set and publish one report.

This is the only process that executes anything the agent wrote. It runs as an
unprivileged uid, in a session of its own, under a wall clock timeout, and it
publishes into a descriptor root opened before the privilege drop. Nothing it can
open says what a set is supposed to produce: oracle.py, gt.json and
test_outputs.py are root-only.

The set list has two halves. cases.py holds the enumerated half and this process
is welcome to read it, since knowing which sets run yields none of their rows.
gen.py builds the rest out of RUN_NONCE, which test.sh draws from /dev/urandom
after the agent has stopped, so those sets did not exist while the submission was
being written and no answer key can cover them.

Because the report is produced inside the process under examination, three things
travel beside it, each aimed at a different way of producing rows without earning
them:

  the trace is appended through a gate that refuses any caller whose frame is not
  the machine emitter's own code object, so the submission never holds the list;

  every sealed machine function is fingerprinted as it actually exists in this
  interpreter, when the tree is imported and again when the set finishes, so
  rebinding one is caught the way editing its file already was;

  the interpreter keeps its own tally of entries into those functions, in a
  closure the tree cannot reach, together with whether that instrumentation was
  still registered and still armed at the end.
"""

import hashlib
import json
import os
import sys
import traceback
import types

HOME = os.path.dirname(os.path.abspath(__file__))
TREE = os.environ.get("APPDIR", "/app")
sys.path.insert(0, TREE)
sys.path.insert(0, HOME)

import cases
import gen

FROZEN = (
    ("bind/mc.py", "Mach.__init__"),
    ("bind/mc.py", "Mach.ev"),
    ("bind/mc.py", "Mach.step"),
    ("bind/mc.py", "Mach.sweep"),
    ("bind/mc.py", "Mach.run"),
    ("bind/bk.py", "Book.__init__"),
    ("bind/bk.py", "Book.drop"),
    ("bind/bk.py", "Book.find"),
    ("bind/bk.py", "Book.weld"),
    ("bind/bk.py", "Book.cells"),
    ("bind/bk.py", "Book.held"),
    ("bind/bk.py", "Book.open_tags"),
    ("bind/bk.py", "Book.open_runs"),
    ("bind/bk.py", "Book.unsent"),
    ("bind/rd.py", "parse"),
)

TALLIED = ("ev", "span", "firm", "card", "queue")
SLOT = 3


def stamp(code):
    box = hashlib.sha256()
    box.update(code.co_code)
    box.update(repr(code.co_names).encode("utf-8"))
    box.update(repr(code.co_varnames).encode("utf-8"))
    for item in code.co_consts:
        if isinstance(item, types.CodeType):
            box.update(stamp(item).encode("utf-8"))
        else:
            box.update(repr(item).encode("utf-8"))
    return box.hexdigest()


def knot(book):
    box = hashlib.sha256()
    for name in sorted(book):
        box.update((name + "|" + book[name] + "\n").encode("utf-8"))
    return box.hexdigest()


def reach(mod, path):
    thing = mod
    for part in path.split("."):
        thing = getattr(thing, part)
    return thing


def census():
    book = {}
    for rel, path in FROZEN:
        label = rel + "::" + path
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            book[label] = "absent"
            continue
        try:
            book[label] = stamp(reach(mod, path).__code__)
        except AttributeError:
            book[label] = "swapped"
    return book


class Trace(object):
    """The rows. Only the machine's emitter may add one."""

    def __init__(self, gate):
        self.gate = gate
        self.rows = []

    def take(self, row):
        if sys._getframe(1).f_code is not self.gate:
            raise RuntimeError("row from an unexpected caller")
        self.rows.append(row)

    def filings(self):
        out = {}
        for row in self.rows:
            if row[0] == "fl":
                out[str(row[2])] = [row[1], row[3], row[4]]
        return out


class Tally(object):
    """The interpreter counts, from a closure nothing in the tree can reach."""

    def __init__(self, codes):
        self.count = {}
        self.codes = list(codes)
        self.hook = self._bump_frame if getattr(sys, "monitoring", None) is None \
            else self._bump_code
        self.mon = getattr(sys, "monitoring", None)
        if self.mon is None:
            self.mode = "profile"
            self._legacy()
        else:
            self.mode = "monitoring"
            self._modern()

    def _bump_frame(self, frame, event, arg):
        if event == "call" and frame.f_code in self.watch:
            name = frame.f_code.co_name
            self.count[name] = self.count.get(name, 0) + 1
        return None

    def _legacy(self):
        self.watch = set(self.codes)
        sys.setprofile(self.hook)

    def _bump_code(self, code, offset):
        self.count[code.co_name] = self.count.get(code.co_name, 0) + 1
        return None

    def _modern(self):
        mon = self.mon
        try:
            mon.use_tool_id(SLOT, "grader")
        except ValueError:
            pass
        mon.register_callback(SLOT, mon.events.PY_START, self.hook)
        for code in self.codes:
            mon.set_local_events(SLOT, code, mon.events.PY_START)

    def close(self):
        if self.mode == "profile":
            armed = sys.getprofile() is self.hook
            sys.setprofile(None)
            return armed
        mon = self.mon
        armed = True
        try:
            if mon.get_tool(SLOT) != "grader":
                armed = False
            if mon.register_callback(SLOT, mon.events.PY_START,
                                     self.hook) is not self.hook:
                armed = False
            for code in self.codes:
                if not mon.get_local_events(SLOT, code) & mon.events.PY_START:
                    armed = False
                mon.set_local_events(SLOT, code, 0)
            mon.register_callback(SLOT, mon.events.PY_START, None)
        except (ValueError, TypeError):
            armed = False
        try:
            mon.free_tool_id(SLOT)
        except (ValueError, TypeError):
            pass
        return armed


def drop():
    for name in [n for n in list(sys.modules) if n == "bind" or n.startswith("bind.")]:
        sys.modules.pop(name, None)


def drive(text):
    drop()
    from bind import card, hold, rch, seq
    from bind.mc import Mach
    from bind.rd import parse
    opening = census()
    trace = Trace(Mach.ev.__code__)
    tally = Tally([Mach.ev.__code__, rch.span.__code__, hold.firm.__code__,
                   card.card.__code__, seq.queue.__code__])
    try:
        Mach(parse(text), trace.take).run()
        filed = trace.filings()
    finally:
        armed = tally.close()
    return {
        "rows": [list(r) for r in trace.rows],
        "fil": filed,
        "in": knot(opening),
        "out": knot(census()),
        "hits": dict((k, tally.count.get(k, 0)) for k in TALLIED),
        "armed": armed,
        "mode": tally.mode,
    }


def emit(where, blob):
    raw = json.dumps(blob, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if where.startswith("fd:"):
        handle = int(where[3:])
        os.lseek(handle, 0, os.SEEK_SET)
        os.ftruncate(handle, 0)
        os.write(handle, raw)
    else:
        with open(where, "wb") as fh:
            fh.write(raw)


def worklist(nonce, count):
    jobs = [(name, cases.SETS[name]) for name in sorted(cases.SETS)]
    jobs.extend(gen.batch(nonce, count))
    return jobs


def main(argv):
    where = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    good, torn = {}, {}
    for name, text in worklist(nonce, count):
        try:
            good[name] = drive(text)
        except Exception:
            torn[name] = traceback.format_exc()[-1200:]
    emit(where, {"nonce": nonce, "count": count, "sets": good, "torn": torn})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
