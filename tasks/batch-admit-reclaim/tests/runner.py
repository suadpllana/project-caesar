"""Play every trace through the rebuilt engine and publish one report.

This is the only process that runs anything the agent wrote. It runs as an
unprivileged uid, in its own session, under a wall clock, and it writes into a
descriptor root opened before the privilege drop, so the account executing agent
code does not own the file it is graded from. Nothing it can open holds an
expected timeline: gt.json, oracle.py and test_outputs.py are root-only.

Two lists of traces are played. cases.py is the enumerated half and this process
may read it, since knowing which traces run says nothing about their timelines.
gen.py builds the rest from RUN_NONCE, which test.sh draws from /dev/urandom once
the agent has stopped, so those traces did not exist when the submission was
written.

Three things travel beside each timeline, because the timeline is produced inside
the process under examination:

  every line is appended through a gate that refuses any caller whose frame is
  not the engine emitter's own code object, so a submission never holds the list;

  each sealed engine function is fingerprinted as it exists in this interpreter,
  once when the tree is imported and again when the trace ends, so rebinding one
  is caught the way editing its file already is;

  the interpreter keeps its own count of entries into the emitter and into the
  four policy hooks, in a closure the tree cannot reach, along with whether that
  instrumentation was still registered and still armed at the end.
"""

import hashlib
import json
import os
import sys
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.environ.get("APPDIR", "/app")
sys.path.insert(0, TREE)
sys.path.insert(0, HERE)

import cases
import gen

SEALED = (
    "eng.pool:keys",
    "eng.pool:Pool.occ",
    "eng.pool:Pool.has",
    "eng.pool:Pool.loose",
    "eng.pool:Pool.sweep",
    "eng.pool:Pool.take",
    "eng.pool:Pool.give",
    "eng.pool:Pool.hold",
    "eng.pool:Pool.free",
    "eng.log:Log.put",
    "eng.rd:parse",
    "eng.step:Eng.mark",
    "eng.step:Eng.enter",
    "eng.step:Eng.shed",
    "eng.step:Eng.close",
    "eng.step:Eng.tick",
    "eng.step:Eng.turn",
    "eng.step:Eng.run",
)

WATCHED = ("put", "ok", "pick", "at", "order", "victim")
SLOT = 4


def digest(code):
    acc = hashlib.sha256()
    acc.update(code.co_code)
    acc.update(repr(code.co_names).encode("utf-8"))
    acc.update(repr(code.co_varnames).encode("utf-8"))
    for item in code.co_consts:
        if isinstance(item, types.CodeType):
            acc.update(digest(item).encode("utf-8"))
        else:
            acc.update(repr(item).encode("utf-8"))
    return acc.hexdigest()


def follow(where):
    mod, path = where.split(":")
    thing = sys.modules.get(mod)
    if thing is None:
        return None
    for part in path.split("."):
        thing = getattr(thing, part, None)
        if thing is None:
            return None
    return thing


def survey():
    book = {}
    for where in SEALED:
        thing = follow(where)
        if thing is None:
            book[where] = "gone"
            continue
        code = getattr(thing, "__code__", None)
        book[where] = "swapped" if code is None else digest(code)
    return book


def fold(book):
    acc = hashlib.sha256()
    for where in sorted(book):
        acc.update(("%s=%s\n" % (where, book[where])).encode("utf-8"))
    return acc.hexdigest()


class Ledger(object):
    """The timeline. Only the engine's emitter is allowed to add to it."""

    def __init__(self, gate):
        self.gate = gate
        self.lines = []

    def add(self, line):
        if sys._getframe(1).f_code is not self.gate:
            raise RuntimeError("a line arrived from somewhere other than the emitter")
        self.lines.append(line)


class Count(object):
    """Entries counted by the interpreter, from a closure the tree cannot see."""

    def __init__(self, codes):
        self.seen = {}
        self.codes = list(codes)
        self.mon = getattr(sys, "monitoring", None)
        self.armed = False
        if self.mon is None:
            self.mode = "profile"
            self.watch = set(self.codes)
            self.hook = self._old
            sys.setprofile(self.hook)
        else:
            self.mode = "monitoring"
            self.hook = self._new
            self._arm()

    def _old(self, frame, event, arg):
        if event == "call" and frame.f_code in self.watch:
            name = frame.f_code.co_name
            self.seen[name] = self.seen.get(name, 0) + 1
        return None

    def _new(self, code, offset):
        self.seen[code.co_name] = self.seen.get(code.co_name, 0) + 1
        return None

    def _arm(self):
        mon = self.mon
        try:
            mon.use_tool_id(SLOT, "bench")
        except ValueError:
            pass
        mon.register_callback(SLOT, mon.events.PY_START, self.hook)
        for code in self.codes:
            mon.set_local_events(SLOT, code, mon.events.PY_START)
        self.armed = True

    def stop(self):
        if self.mode == "profile":
            still = sys.getprofile() is self.hook
            sys.setprofile(None)
            return still
        mon = self.mon
        still = True
        try:
            if mon.get_tool(SLOT) != "bench":
                still = False
            if mon.register_callback(SLOT, mon.events.PY_START, self.hook) is not self.hook:
                still = False
            for code in self.codes:
                if not mon.get_local_events(SLOT, code) & mon.events.PY_START:
                    still = False
                mon.set_local_events(SLOT, code, 0)
            mon.register_callback(SLOT, mon.events.PY_START, None)
        except (ValueError, TypeError):
            still = False
        try:
            mon.free_tool_id(SLOT)
        except (ValueError, TypeError):
            pass
        return still


def forget():
    for name in [n for n in list(sys.modules) if n == "eng" or n.startswith("eng.")]:
        sys.modules.pop(name, None)


def play(text):
    forget()
    from eng import back, fit, pick, room
    from eng.log import Log
    from eng.rd import parse
    from eng.step import Eng
    opening = survey()
    book = Ledger(Log.put.__code__)
    hooks = [Log.put.__code__, fit.ok.__code__, room.pick.__code__,
             back.at.__code__, pick.order.__code__, pick.victim.__code__]
    tally = Count(hooks)
    try:
        Eng(parse(text), book.add).run()
    finally:
        armed = tally.stop()
    return {
        "lines": [list(x) for x in book.lines],
        "open": fold(opening),
        "shut": fold(survey()),
        "hits": dict((k, tally.seen.get(k, 0)) for k in WATCHED),
        "armed": armed,
        "how": tally.mode,
    }


def publish(where, blob):
    raw = json.dumps(blob, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if where.startswith("fd:"):
        fd = int(where[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, raw)
        return
    handle = open(where, "wb")
    handle.write(raw)
    handle.close()


def slate(nonce, count):
    work = [(name, cases.TRACES[name]) for name in sorted(cases.TRACES)]
    work.extend(gen.batch(nonce, count))
    return work


def main(argv):
    where = argv[1] if len(argv) > 1 else "/box/say/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    kept, broke = {}, {}
    for name, text in slate(nonce, count):
        try:
            kept[name] = play(text)
        except Exception:
            broke[name] = traceback.format_exc()[-1200:]
    publish(where, {"nonce": nonce, "count": count, "traces": kept, "broke": broke})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
