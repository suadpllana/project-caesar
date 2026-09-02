"""The only place a submission's code runs.

It imports the work tree once, drives every stream through it, and writes one report on
descriptor OUTFD. Nothing here decides whether the submission is right; that happens
afterwards, as root, in a process that never imports a line of the tree.

Four things travel with the report so the grader can tell a run that happened from a story
about one.

  sink      Every row in a report is appended by a closure this file owns, and the closure
            reads the frame of whoever called it. A row is only taken from the book's own
            recording methods, in the book's own file. A submission can call those methods
            as often as it likes - that is the job - but it cannot write a row without
            going through the method that does the work the row describes.

  saw       sys.monitoring counts entries into those same methods, into a counter held in
            a closure rather than anywhere in the tree, and each stream carries the number
            of entries made while it ran. The grader holds that against a floor it derives
            from the stream's own rows: a row saying an obligation was given up on needs an
            entry into the method that gives up, and a round that closed needs an entry into
            the method that closes it. The report also says whether the tool was still armed
            when the last stream finished, so switching the instrumentation off is something
            the report shows and not a silence.

  marks     Every sealed function is fingerprinted as it exists in the running interpreter,
            at import and again after each stream. The grader derives the same
            fingerprints by compiling the pristine sources, so rebinding one of them to a
            quiet copy is caught the way editing its file already is.

  nonce     The container made it out of /dev/urandom after the submission was sealed, and
            it decides which generated streams exist. A report written before the run
            cannot carry it.
"""
import io
import json
import os
import sys
import types

sys.path.insert(0, "/tests")

import gen
import scen

APP = os.environ["APPDIR"]
NONCE = os.environ["QDR_NONCE"]
COUNT = int(os.environ.get("QDR_COUNT", "300"))
FD = int(os.environ.get("OUTFD", "1"))
STRICT = os.environ.get("REQUIRE_MONITORING", "") == "1"

sys.path.insert(0, APP)

import house.bk as BK
import house.ev as EV
import house.rnd as RND

SEALED = [
    ("bk.Book.move", BK.Book.move),
    ("bk.Book.drop", BK.Book.drop),
    ("bk.Book.shut", BK.Book.shut),
    ("bk.Book.book", BK.Book.book),
    ("bk.Book.top", BK.Book.top),
    ("ev.read", EV.read),
    ("ev.feed", EV.feed),
]

BOOK_FILE = BK.__file__
WRITERS = ("move", "drop", "shut")


def shape(code, out):
    out.append(code.co_name)
    out.append(str(code.co_argcount))
    out.append(code.co_code.hex())
    out.extend(code.co_names)
    out.extend(code.co_varnames)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            shape(c, out)
        else:
            out.append(repr(c))


def mark(fn):
    import hashlib

    out = []
    shape(fn.__code__, out)
    return hashlib.sha256("\x1f".join(out).encode()).hexdigest()[:32]


def marks():
    return {n: mark(f) for n, f in SEALED}


def counter():
    box = [0]

    def bump(*a):
        box[0] += 1

    return box, bump


TALLY, BUMP = counter()
TOOL = 3


def arm():
    m = sys.monitoring
    m.use_tool_id(TOOL, "qdr")
    m.register_callback(TOOL, m.events.PY_START, BUMP)
    for nm in WRITERS:
        m.set_local_events(TOOL, getattr(BK.Book, nm).__code__, m.events.PY_START)


def armed():
    try:
        return sys.monitoring.get_tool(TOOL) == "qdr"
    except Exception:
        return False


def disarm():
    live = armed()
    try:
        sys.monitoring.free_tool_id(TOOL)
    except Exception:
        pass
    return live


def sink_for(rows):
    def sink(kind, a, b):
        f = sys._getframe(1)
        if f.f_code.co_filename != BOOK_FILE or f.f_code.co_name not in WRITERS:
            raise RuntimeError("a row arrived from somewhere that is not the book")
        rows.append([kind, a, b])

    return sink


def drive(text):
    rows = []
    who, run, ev = EV.read(text)
    b = BK.Book(who, sink_for(rows))
    for t in range(1, run + 1):
        EV.feed(b, ev, t)
        RND.turn(b, t)
    sheet = {i: [s, k] for i, (s, k) in b.sheet().items()}
    return rows, sheet


def main():
    start = marks()
    ok = True
    if STRICT:
        arm()
    runs = {}
    drift = []
    todo = list(scen.STREAMS) + gen.batch(NONCE, COUNT)
    for name, text in todo:
        was = TALLY[0]
        try:
            rows, sheet = drive(text)
            runs[name] = {"rows": rows, "sheet": sheet, "saw": TALLY[0] - was}
        except BaseException as e:
            runs[name] = {"fault": "%s: %s" % (type(e).__name__, e), "saw": TALLY[0] - was}
            ok = False
        if marks() != start:
            drift.append(name)
    live = disarm() if STRICT else False
    said = sum(len(r.get("rows", [])) for r in runs.values())
    out = {
        "nonce": NONCE,
        "count": COUNT,
        "runs": runs,
        "marks": start,
        "drift": drift,
        "tally": TALLY[0],
        "rows": said,
        "armed": live,
        "strict": STRICT,
        "clean": ok,
    }
    with io.open(FD, "w", closefd=False) as h:
        json.dump(out, h)
        h.flush()


main()
