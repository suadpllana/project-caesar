"""Drive the rebuilt runtime over every program and write the report.

This is the only process that executes anything the agent wrote. It runs as an
unprivileged uid, in its own session, under a wall clock timeout, and it writes into a
descriptor root opened before dropping privilege. It never sees an expected result:
oracle.py and test_outputs.py are root-only, and gt.json is root-only, so nothing in this
process knows what any program is supposed to do.

Two program sets are driven. The enumerated cases come from cases.py, which the run can
read - knowing which programs execute does not produce their traces. The rest are built
by gen.py from the run nonce, which is made from /dev/urandom inside the verifier
container at trial time. Those programs did not exist when the submission was written,
which is the property the whole anti-forgery argument rests on: there is no answer key to
hold, because the answers are computed after the fact by a model the run cannot reach.

Three things are attested alongside the report, because the report itself is produced
inside this process.

  The sink. Trace rows are appended by a closure created here, which refuses any caller
  whose frame is not Loop.ev's own code object. A submission cannot push rows into the
  trace from its own module, and cannot replace the list, because it never has it.

  The fingerprints. Every sealed function is hashed as it actually exists in this
  interpreter, once when the tree is imported and again when the program has finished, so
  a submission that rebinds a runtime function rather than editing its file is caught the
  same way editing the file is.

  The tally. The interpreter counts entries into the decision functions and into Loop.ev,
  in a closure rather than in the tree, and reports whether the instrumentation was still
  registered and still armed at the end.
"""

import hashlib
import json
import os
import sys
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get("APPDIR", "/app")
# /tests takes precedence over the tree, so nothing the run could leave in the
# artifact directory can shadow the generator or the case set.
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import cases
import gen

# The grader imports this tuple rather than keeping its own copy, so the two cannot
# drift; it derives the expected digests by compiling the pristine sources.
SEALED = (
    ("kern/loop.py", "Loop.ev"),
    ("kern/loop.py", "Loop.new"),
    ("kern/loop.py", "Loop.mark"),
    ("kern/loop.py", "Loop.rouse"),
    ("kern/loop.py", "Loop.ask"),
    ("kern/loop.py", "Loop.hurl"),
    ("kern/loop.py", "Loop.cut"),
    ("kern/loop.py", "Loop.step"),
    ("kern/loop.py", "Loop.exec"),
    ("kern/loop.py", "Loop.after"),
    ("kern/loop.py", "Loop.shut"),
    ("kern/loop.py", "Loop.shed"),
    ("kern/loop.py", "Loop.fini"),
    ("kern/loop.py", "Loop.tick"),
    ("kern/loop.py", "Loop.run"),
    ("kern/gd.py", "chain"),
    ("kern/gd.py", "inner"),
    ("kern/gd.py", "busy"),
    ("kern/fib.py", "Fib.__init__"),
    ("kern/lex.py", "parse"),
    ("kern/lex.py", "link"),
)

WATCH = ("ev", "pick", "stops", "blend", "shut", "wait", "snag", "reap", "rouse")
TOOL = 3


def fingerprint(code):
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


def sink_for(evcode):
    """Trace rows may only be appended from inside Loop.ev."""
    rows = []

    def put(row):
        if sys._getframe(1).f_code is not evcode:
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
        if n == "kern" or n.startswith("kern."):
            sys.modules.pop(n, None)


def one(text, root="main"):
    unload()
    from kern import knot, pick, stop, wake
    from kern.lex import parse
    from kern.loop import Loop
    opened = live()
    rows, put = sink_for(Loop.ev.__code__)
    disarm = arm([Loop.ev.__code__, pick.pick.__code__, stop.stops.__code__,
                  stop.blend.__code__, knot.shut.__code__, knot.wait.__code__,
                  knot.snag.__code__, knot.reap.__code__, wake.rouse.__code__])
    try:
        lp = Loop(parse(text), put)
        lp.run(root)
        toks = [[f.fid, f.pid, list(f.toks)] for f in lp.fs]
    finally:
        intact, how, tally = disarm()
    return {
        "tr": [list(r) for r in rows],
        "tk": toks,
        "fp": seal(opened),
        "fp2": seal(live()),
        "mon": dict((k, tally.get(k, 0)) for k in WATCH),
        "arm": intact,
        "how": how,
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


def plan(nonce, n):
    out = [(nm, cases.PROGS[nm]) for nm in sorted(cases.PROGS)]
    out += [(nm, gen.text(p)) for nm, p in gen.batch(nonce, n)]
    return out


def main(argv):
    out = argv[1] if len(argv) > 1 else "/work/run/out.json"
    nonce = os.environ.get("RUN_NONCE", "")
    count = int(os.environ.get("RUN_COUNT", "300"))
    reports, errors = {}, {}
    for name, text in plan(nonce, count):
        try:
            reports[name] = one(text)
        except Exception:
            errors[name] = traceback.format_exc()[-1200:]
    emit(out, {"nonce": nonce, "count": count,
               "reports": reports, "errors": errors})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
