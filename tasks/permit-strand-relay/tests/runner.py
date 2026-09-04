"""The only process that executes anything the agent wrote.

It runs unprivileged, in its own session, under a wall clock kill, and writes
one JSON document to a descriptor opened by root before the privileges went
away. Nothing it can read says what a stream is supposed to produce: gt.json,
oracle.py and test_outputs.py are root-only.

The graded rows are produced inside the process under examination, so three
things travel beside them and each is aimed at a different way of producing
rows without earning them.

The trace is appended through a gate that refuses any caller whose frame is
not one of the machine's own emitting methods, so a policy never holds the
list. Every frozen function is fingerprinted as it actually exists in this
interpreter, when the tree is imported and again when the last stream is done,
which catches a rebinding the way editing the file on disk is already caught.
And the interpreter keeps its own count of entries into those functions, in a
closure the tree cannot reach, together with whether that instrumentation was
still registered and still armed at the end.
"""

import hashlib
import json
import os
import sys
import traceback
import types

BASE = os.path.dirname(os.path.abspath(__file__))
TREE = os.environ.get("APPDIR", "/app")
sys.path.insert(0, TREE)
sys.path.insert(0, BASE)

import cases
import gen

SEALED = (
    ("lnk/book.py", "Book.__init__"),
    ("lnk/book.py", "Book.arm"),
    ("lnk/book.py", "Book.charge"),
    ("lnk/book.py", "Book.bill"),
    ("lnk/book.py", "Book.stow"),
    ("lnk/book.py", "Book.draw"),
    ("lnk/book.py", "Book.close"),
    ("lnk/book.py", "Book.held"),
    ("lnk/book.py", "Book.open"),
    ("lnk/mach.py", "Mach.run"),
    ("lnk/mach.py", "Mach.arrive"),
    ("lnk/mach.py", "Mach.take"),
    ("lnk/mach.py", "Mach.shut"),
    ("lnk/mach.py", "Mach.reopen"),
    ("lnk/mach.py", "Mach.publish"),
    ("lnk/rd.py", "parse"),
)

COUNTED = ("arrive", "publish", "charge", "draw", "close")
SLOT = 4


def mark(code):
    pot = hashlib.sha256()
    pot.update(code.co_code)
    pot.update(repr(code.co_names).encode("utf-8"))
    pot.update(repr(code.co_varnames).encode("utf-8"))
    for lump in code.co_consts:
        if isinstance(lump, types.CodeType):
            pot.update(mark(lump).encode("utf-8"))
        else:
            pot.update(repr(lump).encode("utf-8"))
    return pot.hexdigest()


def fold(table):
    pot = hashlib.sha256()
    for key in sorted(table):
        pot.update((key + "=" + table[key] + "\n").encode("utf-8"))
    return pot.hexdigest()


def walk(mod, dotted):
    thing = mod
    for step in dotted.split("."):
        thing = getattr(thing, step)
    return thing


def census():
    table = {}
    for rel, dotted in SEALED:
        key = rel + "::" + dotted
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            table[key] = "absent"
            continue
        try:
            table[key] = mark(walk(mod, dotted).__code__)
        except AttributeError:
            table[key] = "swapped"
    return table


class Sink(object):
    """The rows. Only the machine's own emitting methods may add one."""

    def __init__(self, allowed):
        self.allowed = tuple(allowed)
        self.rows = []
        self.forced = False

    def take(self, row):
        if sys._getframe(1).f_code not in self.allowed:
            self.forced = True
            raise RuntimeError("row offered by an unexpected caller")
        self.rows.append(list(row))


class Count(object):
    """The interpreter counts, into a closure nothing in the tree can reach."""

    def __init__(self, codes):
        self.tally = {}
        self.codes = list(codes)
        self.mon = getattr(sys, "monitoring", None)
        self.bycode = self._bump_code
        self.byframe = self._bump_frame
        if self.mon is None:
            self.mode = "profile"
            self.watch = set(self.codes)
            sys.setprofile(self.byframe)
        else:
            self.mode = "monitoring"
            self._arm()

    def _bump_code(self, code, offset):
        self.tally[code.co_name] = self.tally.get(code.co_name, 0) + 1
        return None

    def _bump_frame(self, frame, event, arg):
        if event == "call" and frame.f_code in self.watch:
            name = frame.f_code.co_name
            self.tally[name] = self.tally.get(name, 0) + 1
        return None

    def _arm(self):
        mon = self.mon
        try:
            mon.use_tool_id(SLOT, "tally")
        except ValueError:
            pass
        mon.register_callback(SLOT, mon.events.PY_START, self.bycode)
        for code in self.codes:
            mon.set_local_events(SLOT, code, mon.events.PY_START)

    def close(self):
        if self.mode == "profile":
            live = sys.getprofile() is self.byframe
            sys.setprofile(None)
            return live
        mon = self.mon
        live = True
        try:
            if mon.get_tool(SLOT) != "tally":
                live = False
            if mon.register_callback(SLOT, mon.events.PY_START,
                                     self.bycode) is not self.bycode:
                live = False
            for code in self.codes:
                if not mon.get_local_events(SLOT, code) & mon.events.PY_START:
                    live = False
                mon.set_local_events(SLOT, code, 0)
            mon.register_callback(SLOT, mon.events.PY_START, None)
        except (ValueError, TypeError, AttributeError):
            live = False
        try:
            mon.free_tool_id(SLOT)
        except (ValueError, TypeError, AttributeError):
            pass
        return live


def worklist(nonce, wide):
    jobs = [(name, cases.SETS[name]) for name in sorted(cases.SETS)]
    for plan in gen.batch(nonce, wide):
        jobs.append((plan["name"], plan))
    return jobs


def main():
    nonce = int(os.environ.get("RUN_NONCE", "0"))
    wide = int(os.environ.get("RUN_WIDE", "300"))

    from lnk.book import Book
    from lnk.mach import Mach
    from lnk.rd import parse

    opening = census()
    counter = Count([Mach.arrive.__code__, Mach.publish.__code__,
                     Book.charge.__code__, Book.draw.__code__,
                     Book.close.__code__])
    runs = {}
    forced = False
    try:
        for name, plan in worklist(nonce, wide):
            sink = Sink([Mach.arrive.__code__, Mach.shut.__code__,
                         Mach.publish.__code__])
            try:
                book = Mach(parse(json.dumps(plan)), sink.take).run()
                runs[name] = {
                    "ev": sink.rows,
                    "park": dict((str(fd), book.held(fd)) for fd in book.open()),
                }
            except Exception:
                runs[name] = {"error": traceback.format_exc(limit=3)}
            if sink.forced:
                forced = True
    finally:
        live = counter.close()

    blob = {
        "nonce": nonce,
        "wide": wide,
        "runs": runs,
        "open": fold(opening),
        "shut": fold(census()),
        "hits": dict((k, counter.tally.get(k, 0)) for k in COUNTED),
        "armed": live,
        "mode": counter.mode,
        "forced": forced,
    }
    raw = json.dumps(blob, sort_keys=True, separators=(",", ":")).encode("utf-8")
    where = int(os.environ["SINK_FD"])
    os.lseek(where, 0, os.SEEK_SET)
    os.ftruncate(where, 0)
    os.write(where, raw)


if __name__ == "__main__":
    main()
