"""Drive the policy kernel over every journal and write the report.

This is the only process that executes anything the agent wrote. It runs as an
unprivileged uid, in its own session, under a wall clock timeout, and it writes into a
descriptor root opened before privilege was dropped. It never learns what any journal is
supposed to produce: oracle.py, gt.json and test_outputs.py are root-only files, so
nothing in this process holds an expected answer to compare against or to copy.

Two sets of journals run. The enumerated ones come from cases.py, which this process may
read - knowing which journals execute produces none of their events. The rest are built by
gen.py from RUN_NONCE, made from /dev/urandom inside the verifier container at trial time,
so those journals did not exist when the submission was written.

Three attestations travel with the report, because the report is produced inside the
process that ran the agent's code.

  THE SINK. Event rows go through a callable this module owns, which reads the calling
  frame and accepts nothing but the frozen driver's own emitter. A submission never holds
  the row list, cannot replace it, and cannot append to it from its own module.

  THE SEALS. Every frozen function is hashed as it actually exists in this interpreter,
  once when the tree is first imported and again when each journal has finished. A
  submission that leaves the files alone and rebinds a function at run time is caught the
  same way editing the file is.

  THE TALLY. The interpreter counts entries into the emitter and into each decision the
  kernel asks for, in a closure this module holds rather than anywhere in the tree, and
  reports whether the instrumentation was still registered and still armed at the end.
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

# The grader imports this rather than keeping a second copy, so the two cannot drift. It
# turns each entry into an expected digest by compiling the pristine source - nothing is
# executed to do it.
FROZEN = {
    "pol/drv.py": ("Drv.ev", "Drv.sig", "Drv.step", "Drv.go"),
    "pol/store.py": ("R.__init__", "R.key", "R.copy", "St.mk", "St.up", "St.kids",
                     "St.line", "St.relink", "St.held", "St.put", "St.rip",
                     "St.stops", "St.bar", "St.join", "St.part", "St.mems",
                     "St.crews", "St.all"),
    "pol/jrn.py": ("parse",),
}

COUNTED = ("ev", "plant", "pull", "sprout", "shut", "free", "move", "pick", "near")
SLOT = 4


def seals():
    for rel in sorted(FROZEN):
        for qual in FROZEN[rel]:
            yield rel, qual


def digest(code):
    acc = hashlib.sha256()
    acc.update(code.co_code)
    acc.update(("|%s|%s" % (code.co_names, code.co_varnames)).encode("utf-8"))
    for item in code.co_consts:
        if isinstance(item, types.CodeType):
            acc.update(digest(item).encode("utf-8"))
        else:
            acc.update(repr(item).encode("utf-8"))
    return acc.hexdigest()


def dig(mod, qual):
    obj = mod
    for step in qual.split("."):
        obj = getattr(obj, step)
    return obj


def census():
    book = {}
    for rel, qual in seals():
        tag = rel + "::" + qual
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            book[tag] = "absent"
            continue
        try:
            book[tag] = digest(dig(mod, qual).__code__)
        except AttributeError:
            book[tag] = "swapped"
    return book


def fold(book):
    acc = hashlib.sha256()
    for tag in sorted(book):
        acc.update(("%s>%s\n" % (tag, book[tag])).encode("utf-8"))
    return acc.hexdigest()


class Sink:
    """Event rows are accepted from the frozen emitter and from nowhere else."""

    def __init__(self, gate):
        self.gate = gate
        self.rows = []

    def __call__(self, row):
        back = sys._getframe(1).f_code
        if back is not self.gate:
            raise RuntimeError("row offered by %s" % back.co_name)
        self.rows.append(row)


class Tally:
    """Entries counted by the interpreter, in an object the tree never receives."""

    def __init__(self, codes):
        self.hits = {}
        self.codes = list(codes)
        self.mon = getattr(sys, "monitoring", None)
        self.how = "monitoring" if self.mon is not None else "profile"
        if self.mon is None:
            self.hook = self.slow
            sys.setprofile(self.hook)
            return
        self.hook = self.fast
        try:
            self.mon.use_tool_id(SLOT, "gso")
        except ValueError:
            pass
        self.mon.register_callback(SLOT, self.mon.events.PY_START, self.hook)
        for code in self.codes:
            self.mon.set_local_events(SLOT, code, self.mon.events.PY_START)

    def slow(self, frame, event, arg):
        if event == "call" and frame.f_code in self.codes:
            name = frame.f_code.co_name
            self.hits[name] = self.hits.get(name, 0) + 1
        return None

    def fast(self, code, offset):
        self.hits[code.co_name] = self.hits.get(code.co_name, 0) + 1
        return None

    def stand(self):
        if self.mon is None:
            ok = sys.getprofile() is self.hook
            sys.setprofile(None)
            return ok
        ok = self.mon.get_tool(SLOT) == "gso"
        back = self.mon.register_callback(SLOT, self.mon.events.PY_START, self.hook)
        if back is not self.hook:
            ok = False
        for code in self.codes:
            if not self.mon.get_local_events(SLOT, code) & self.mon.events.PY_START:
                ok = False
            self.mon.set_local_events(SLOT, code, 0)
        self.mon.register_callback(SLOT, self.mon.events.PY_START, None)
        try:
            self.mon.free_tool_id(SLOT)
        except ValueError:
            pass
        return ok


def forget():
    for name in [m for m in sys.modules if m == "pol" or m.startswith("pol.")]:
        sys.modules.pop(name, None)


def once(text):
    forget()
    from pol import crowd, graft, spread, weigh
    from pol.drv import Drv
    from pol.jrn import parse
    opened = census()
    sink = Sink(Drv.ev.__code__)
    tally = Tally([Drv.ev.__code__, spread.plant.__code__, spread.pull.__code__,
                   graft.sprout.__code__, graft.shut.__code__, graft.free.__code__,
                   graft.move.__code__, weigh.pick.__code__, crowd.near.__code__])
    try:
        Drv(parse(text), sink).go()
    finally:
        armed = tally.stand()
    return {
        "rows": sink.rows,
        "open": fold(opened),
        "shut": fold(census()),
        "hits": dict((k, tally.hits.get(k, 0)) for k in COUNTED),
        "armed": armed,
        "how": tally.how,
    }


def slate(nonce, count):
    work = [(name, cases.PROGS[name]) for name in sorted(cases.PROGS)]
    work += [(name, gen.text(seed)) for name, seed in gen.batch(nonce, count)]
    return work


def hand(where, blob):
    text = json.dumps(blob, sort_keys=True, separators=(",", ":"))
    if where.startswith("fd:"):
        fd = int(where[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text.encode("utf-8"))
        return
    with open(where, "w") as fh:
        fh.write(text)


def main(argv):
    where = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    done, broke = {}, {}
    for name, text in slate(nonce, count):
        try:
            done[name] = once(text)
        except Exception:
            broke[name] = traceback.format_exc()[-1200:]
    hand(where, {"nonce": nonce, "count": count, "done": done, "broke": broke})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
