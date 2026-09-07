"""Drive the rebuilt engine over every session and write the report.

This is the only process that executes anything the agent wrote. It runs as an
unprivileged uid, in its own session, under a wall clock timeout, and it writes into a
descriptor root opened before dropping privilege. It never sees an expected result:
oracle.py, gt.json and test_outputs.py are root-only, so nothing in this process knows
what any session is supposed to produce.

Two session sets are driven. The enumerated ones come from cases.py, which the run can
read - knowing which sessions execute does not produce their events. The rest are built
by gen.py from the run nonce, which is made from /dev/urandom inside the verifier
container at trial time. Those sessions did not exist when the submission was written,
which is what the anti-forgery argument rests on: there is no answer key to hold, because
the answers are computed afterwards by a model the run cannot reach.

Three things are attested alongside the report, because the report is produced inside
this process.

  The sink. Event rows are appended by a closure created here, which refuses any caller
  whose frame is not Emit.row's own code object. A submission cannot push rows in from
  its own module, and cannot replace the list, because it never holds it.

  The fingerprints. Every sealed function is hashed as it actually exists in this
  interpreter, when the tree is imported and again when the session has finished, so a
  submission that rebinds a driver function instead of editing its file is caught the
  same way editing the file already is.

  The tally. The interpreter counts entries into Emit.row and into each decision the
  engine asks for, in a closure rather than in the tree, and reports whether the
  instrumentation was still registered and still armed at the end.
"""

import hashlib
import json
import os
import sys
import time
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get("APPDIR", "/app")
# /tests takes precedence over the tree, so nothing the run could leave in an artifact
# directory can shadow the generator or the case set.
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import cases
import gen

# The grader imports this tuple rather than keeping a copy, so the two cannot drift; it
# derives the expected digests by compiling the pristine sources.
SEALED = (
    ("mkt/bk.py", "Ord.__init__"),
    ("mkt/bk.py", "Side.__init__"),
    ("mkt/bk.py", "Side.put"),
    ("mkt/bk.py", "Side.top"),
    ("mkt/bk.py", "Side.front"),
    ("mkt/bk.py", "Side.take"),
    ("mkt/bk.py", "Side.rows"),
    ("mkt/bk.py", "Bk.__init__"),
    ("mkt/bk.py", "Bk.own"),
    ("mkt/bk.py", "Bk.opp"),
    ("mkt/ev.py", "Emit.__init__"),
    ("mkt/ev.py", "Emit.row"),
    ("mkt/rd.py", "num"),
    ("mkt/rd.py", "read"),
    ("mkt/drv.py", "St.__init__"),
    ("mkt/drv.py", "rest"),
    ("mkt/drv.py", "submit"),
    ("mkt/drv.py", "drive"),
    ("mkt/drv.py", "dump"),
)

WATCH = ("row", "walk", "avail", "refill", "blocks", "admit", "check", "park")
TOOL = 4


def fingerprint(code):
    """Hash a code object, recursing into nested ones.

    A repr of a nested code object carries its filename and its address, so hashing the
    consts naively makes any function holding a comprehension or a lambda differ between
    runs. Recurse instead.
    """
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(repr(code.co_names).encode("utf-8"))
    h.update(repr(code.co_varnames).encode("utf-8"))
    for k in code.co_consts:
        if isinstance(k, types.CodeType):
            h.update(fingerprint(k).encode("utf-8"))
        else:
            h.update(repr(k).encode("utf-8"))
    return h.hexdigest()


def reach(mod, qual):
    obj = mod
    for part in qual.split("."):
        obj = getattr(obj, part)
    return obj


def live():
    out = {}
    for rel, qual in SEALED:
        key = "%s:%s" % (rel, qual)
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            out[key] = "unloaded"
            continue
        try:
            out[key] = fingerprint(reach(mod, qual).__code__)
        except AttributeError:
            out[key] = "replaced"
    return out


def seal(book):
    h = hashlib.sha256()
    for k in sorted(book):
        h.update(("%s=%s;" % (k, book[k])).encode("utf-8"))
    return h.hexdigest()


def sink_for(rowcode):
    """Event rows may only be appended from inside Emit.row."""
    rows = []

    def put(row):
        if sys._getframe(1).f_code is not rowcode:
            raise RuntimeError("sink")
        rows.append(row)

    return rows, put


def arm(codes):
    """Let the interpreter count the entries, from a closure the tree cannot reach."""
    tally = {}
    wanted = set(codes)
    mon = getattr(sys, "monitoring", None)

    if mon is None:
        def entered(frame, event, arg):
            if event == "call" and frame.f_code in wanted:
                nm = frame.f_code.co_name
                tally[nm] = tally.get(nm, 0) + 1
            return None

        sys.setprofile(entered)

        def disarm():
            ok = sys.getprofile() is entered
            sys.setprofile(None)
            return ok, "profile", dict(tally)

        return disarm

    def entered(code, offset):
        tally[code.co_name] = tally.get(code.co_name, 0) + 1
        return None

    try:
        mon.use_tool_id(TOOL, "verifier")
    except ValueError:
        pass
    mon.register_callback(TOOL, mon.events.PY_START, entered)
    for code in codes:
        mon.set_local_events(TOOL, code, mon.events.PY_START)

    def disarm():
        ok = mon.get_tool(TOOL) == "verifier"
        if mon.register_callback(TOOL, mon.events.PY_START, entered) is not entered:
            ok = False
        for code in codes:
            if not mon.get_local_events(TOOL, code) & mon.events.PY_START:
                ok = False
            mon.set_local_events(TOOL, code, 0)
        mon.register_callback(TOOL, mon.events.PY_START, None)
        try:
            mon.free_tool_id(TOOL)
        except ValueError:
            pass
        return ok, "monitoring", dict(tally)

    return disarm


def unload():
    for n in list(sys.modules):
        if n in ("mkt", "eng") or n.startswith("mkt.") or n.startswith("eng."):
            sys.modules.pop(n, None)


def one(text):
    unload()
    from eng import hand, hold, shown, take, trip
    from mkt.drv import drive
    from mkt.ev import Emit
    from mkt.rd import read
    opened = live()
    rows, put = sink_for(Emit.row.__code__)
    disarm = arm([Emit.row.__code__, take.walk.__code__, shown.avail.__code__,
                  shown.refill.__code__, hand.blocks.__code__, hold.admit.__code__,
                  trip.check.__code__, trip.park.__code__])
    t0 = time.time()
    try:
        cap, mark, msgs = read(text)
        drive(cap, mark, msgs, put)
    finally:
        intact, how, tally = disarm()
    return {
        "ev": [list(r) for r in rows],
        "fp": seal(opened),
        "fp2": seal(live()),
        "mon": dict((k, tally.get(k, 0)) for k in WATCH),
        "arm": intact,
        "how": how,
        "sec": round(time.time() - t0, 3),
    }


def emit(target, payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if target.startswith("fd:"):
        fd = int(target[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text.encode("utf-8"))
        return
    with open(target, "w") as fh:
        fh.write(text)


def plan(nonce, small, deep):
    out = [(nm, cases.SESS[nm]) for nm in sorted(cases.SESS)]
    out += gen.batch(nonce, small)
    out += gen.deep_batch(nonce, deep)
    return out


def main(argv):
    out = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    small = int(os.environ.get("RUN_SMALL", "300"))
    deep = int(os.environ.get("RUN_DEEP", "3"))
    reports, errors = {}, {}
    for name, text in plan(nonce, small, deep):
        try:
            reports[name] = one(text)
        except Exception:
            errors[name] = traceback.format_exc()[-1200:]
    emit(out, {"nonce": nonce, "small": small, "deep": deep,
               "reports": reports, "errors": errors})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
