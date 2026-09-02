"""Drive the rebuilt machine over every plan and publish one report.

Only this process executes anything the agent wrote. It runs unprivileged, in a
session of its own, under a wall clock timeout, and it publishes into a descriptor
that root opened before the privilege drop. No expected result is reachable from
here: `oracle.py`, `gt.json` and `test_outputs.py` are root-only, so nothing in
this process can know what a plan is supposed to do.

The plan list has two halves. `cases.py` supplies the enumerated half and the run
is welcome to read it, since knowing which plans execute yields none of their
traces. `gen.py` supplies the rest from the run nonce, which `test.sh` draws from
/dev/urandom once the agent has stopped. Those plans did not exist while the
submission was being written, and that is the whole of the anti-forgery argument:
there is no key to hold, because the answers are worked out afterwards by a model
this process cannot open.

Because the report is produced inside the process being examined, three things
travel beside it.

  A ledger, not a list. Rows reach the trace only through an appender created
  here that rejects any caller whose frame is not the machine emitter's own code
  object. The submission never holds the list and cannot swap it.

  Digests of the sealed machine functions as they actually exist in this
  interpreter, taken when the tree is imported and again when the plan finishes,
  so rebinding a function is caught exactly as editing its file already was.

  A tally kept by the interpreter itself, in a closure beyond the tree's reach,
  along with whether that instrumentation was still registered and still armed
  when the plan ended.
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
# /tests wins over the tree, so nothing left in the artifact directory can shadow
# the generator or the enumerated cases.
sys.path.insert(0, HERE)

import cases
import gen

SEALED = (
    ("flow/mach.py", "Mach.ev"),
    ("flow/mach.py", "Mach.out"),
    ("flow/mach.py", "Mach.land"),
    ("flow/mach.py", "Mach.wake"),
    ("flow/mach.py", "Mach.one"),
    ("flow/mach.py", "Mach.sweep"),
    ("flow/mach.py", "Mach.idle"),
    ("flow/mach.py", "Mach.run"),
    ("flow/mach.py", "Mach.__init__"),
    ("flow/mach.py", "St.__init__"),
    ("flow/gr.py", "parse"),
    ("flow/gr.py", "flat"),
)

WATCH = ("ev", "own", "carry", "ripe", "order")
TOOL = 4


class Ledger(object):
    """The trace. Only the machine's emitter may add to it."""

    def __init__(self, gate):
        self.gate = gate
        self.rows = []

    def add(self, row):
        if sys._getframe(1).f_code is not self.gate:
            raise RuntimeError("sink")
        self.rows.append(row)

    def sinks(self):
        out = {}
        for row in self.rows:
            if row[0] == "sk":
                out.setdefault(row[2], []).append(row[3])
        return out


def digest(code):
    h = hashlib.sha256()
    h.update(code.co_code)
    for part in (code.co_names, code.co_varnames):
        h.update(repr(part).encode("utf-8"))
    for k in code.co_consts:
        h.update((digest(k) if isinstance(k, types.CodeType) else repr(k)).encode("utf-8"))
    return h.hexdigest()


def pluck(mod, qual):
    obj = mod
    for step in qual.split("."):
        obj = getattr(obj, step)
    return obj


def snapshot():
    book = {}
    for rel, qual in SEALED:
        key = rel + ":" + qual
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            book[key] = "unloaded"
        else:
            try:
                book[key] = digest(pluck(mod, qual).__code__)
            except AttributeError:
                book[key] = "replaced"
    return book


def fold(book):
    h = hashlib.sha256()
    for key in sorted(book):
        h.update((key + "=" + book[key] + ";").encode("utf-8"))
    return h.hexdigest()


def counter(codes):
    """Have the interpreter do the counting, from a closure the tree cannot reach."""
    tally = {}
    mon = getattr(sys, "monitoring", None)

    if mon is None:
        watched = set(codes)

        def hook(frame, event, arg):
            if event == "call" and frame.f_code in watched:
                nm = frame.f_code.co_name
                tally[nm] = tally.get(nm, 0) + 1
            return None

        sys.setprofile(hook)

        def stop():
            live = sys.getprofile() is hook
            sys.setprofile(None)
            return {"armed": live, "how": "profile", "tally": dict(tally)}

        return stop

    def hook(code, offset):
        tally[code.co_name] = tally.get(code.co_name, 0) + 1
        return None

    try:
        mon.use_tool_id(TOOL, "verifier")
    except ValueError:
        pass
    mon.register_callback(TOOL, mon.events.PY_START, hook)
    for code in codes:
        mon.set_local_events(TOOL, code, mon.events.PY_START)

    def stop():
        live = True
        try:
            live = mon.get_tool(TOOL) == "verifier"
            if mon.register_callback(TOOL, mon.events.PY_START, hook) is not hook:
                live = False
            for code in codes:
                if not mon.get_local_events(TOOL, code) & mon.events.PY_START:
                    live = False
                mon.set_local_events(TOOL, code, 0)
            mon.register_callback(TOOL, mon.events.PY_START, None)
        except (ValueError, TypeError):
            live = False
        try:
            mon.free_tool_id(TOOL)
        except (ValueError, TypeError):
            pass
        return {"armed": live, "how": "monitoring", "tally": dict(tally)}

    return stop


def forget():
    for name in [n for n in sys.modules if n == "flow" or n.startswith("flow.")]:
        sys.modules.pop(name, None)


def watched(mods):
    due, emit, pick, route = mods
    return [emit.own.__code__, route.carry.__code__,
            due.ripe.__code__, pick.order.__code__]


def drive(text):
    forget()
    from flow import due, emit, pick, route
    from flow.gr import parse
    from flow.mach import Mach
    opened = snapshot()
    book = Ledger(Mach.ev.__code__)
    stop = counter([Mach.ev.__code__] + watched((due, emit, pick, route)))
    try:
        Mach(parse(text), book.add).run()
        taken = book.sinks()
    finally:
        state = stop()
    return {
        "tr": [list(r) for r in book.rows],
        "sk": taken,
        "fp": fold(opened),
        "fp2": fold(snapshot()),
        "mon": dict((k, state["tally"].get(k, 0)) for k in WATCH),
        "arm": state["armed"],
        "how": state["how"],
    }


def publish(where, payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if not where.startswith("fd:"):
        with open(where, "wb") as fh:
            fh.write(blob)
        return
    fd = int(where[3:])
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    os.write(fd, blob)


def plan(nonce, n):
    work = [(nm, cases.PLANS[nm]) for nm in sorted(cases.PLANS)]
    work.extend((nm, gen.text(p)) for nm, p in gen.batch(nonce, n))
    return work


def fingerprint(code):
    """Kept under this name because the grader derives its baseline through it."""
    return digest(code)


def seal(book):
    """Likewise: the grader folds its own baseline book with this."""
    return fold(book)


def main(argv):
    where = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    done, broke = {}, {}
    for name, text in plan(nonce, count):
        try:
            done[name] = drive(text)
        except Exception:
            broke[name] = traceback.format_exc()[-1200:]
    publish(where, {"nonce": nonce, "count": count,
                    "reports": done, "errors": broke})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
