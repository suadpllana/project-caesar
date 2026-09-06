"""The run.

Executes the assembled tree over every graded request under an unprivileged uid and reports
what it emitted, plus the evidence the grader needs to believe the rows were produced by the
machine rather than written out directly.

Three kinds of evidence leave here, and none of them is trusted on its own:

  rows    what the runner's own record gate appended, in order
  tally   the interpreter's count of entries into each of the four editable modules,
          taken with sys.monitoring rather than from anything the modules report
  marks   a fingerprint of each frozen entry point as it actually stood in the running
          interpreter, which the grader compares against digests it derives by compiling
          the pristine sources itself

A submission that computes nothing and prints the answer has no tally. A submission that
rebinds a frozen function to a shim has the wrong mark. Neither can be repaired from inside
this process, because the grader recomputes both sides from files this uid cannot open.
"""
import hashlib
import json
import os
import sys
import time

WATCH = ("strm.sm", "strm.hb", "strm.rel", "strm.fin")
FROZEN = (
    ("tok.vocab", "bs"),
    ("tok.vocab", "sp"),
    ("tok.decode", "lead"),
    ("strm.req", "run"),
    ("strm.req", "parse"),
    ("strm.req", "gate"),
    ("strm.req", "hx"),
)
TOOL = 3


def mark(code):
    """A fingerprint of a code object that does not depend on where it was compiled.

    Nested code objects are recursed into rather than repr'd, because the repr of a code
    object carries its filename and its address, and neither survives being compiled in a
    different directory or a different process.
    """
    h = hashlib.sha256()

    def walk(c):
        h.update(c.co_code)
        h.update(repr(c.co_names).encode("utf-8", "replace"))
        h.update(repr(c.co_varnames).encode("utf-8", "replace"))
        for k in c.co_consts:
            if hasattr(k, "co_code"):
                h.update(b"<code>")
                walk(k)
            else:
                h.update(repr(k).encode("utf-8", "replace"))

    walk(code)
    return h.hexdigest()


def arm(mods):
    """Count entries into the editable modules, in a closure the modules cannot reach.

    The callback is registered once, as a plain function rather than a bound method, and
    unwatched code disables itself on first sight so the wide family does not pay for
    instrumentation it does not need.
    """
    mon = sys.monitoring
    mon.use_tool_id(TOOL, "seam")
    owner = {}
    for name in WATCH:
        m = sys.modules.get(name)
        if m is None:
            continue
        for key in sorted(vars(m)):
            v = vars(m)[key]
            code = getattr(v, "__code__", None)
            if code is not None:
                owner[code] = name
    tally = {}
    live = {"armed": True}

    def on_start(code, offset):
        if not live["armed"]:
            return mon.DISABLE
        who = owner.get(code)
        if who is None:
            return mon.DISABLE
        tally[who] = tally.get(who, 0) + 1
        return None

    mon.register_callback(TOOL, mon.events.PY_START, on_start)
    mon.set_events(TOOL, mon.events.PY_START)
    return live, tally


def disarm(live):
    """Teardown that never raises, whatever state the run left the interpreter in."""
    live["armed"] = False
    mon = sys.monitoring
    try:
        mon.set_events(TOOL, 0)
    except Exception:
        pass
    try:
        mon.register_callback(TOOL, mon.events.PY_START, None)
    except Exception:
        pass
    try:
        mon.free_tool_id(TOOL)
    except Exception:
        pass


def marks():
    out = {}
    for modname, fname in FROZEN:
        m = sys.modules.get(modname)
        fn = getattr(m, fname, None) if m is not None else None
        code = getattr(fn, "__code__", None)
        out["%s.%s" % (modname, fname)] = mark(code) if code is not None else ""
    return out


def tree_digest(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            with open(p, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def main(argv):
    tree, reqdir, outpath = argv[0], argv[1], argv[2]
    sys.path.insert(0, tree)

    report = {"rows": [], "tally": {}, "marks": {}, "tree": {}, "errors": [], "secs": 0.0}
    live = None
    try:
        import strm.fin  # noqa: F401
        import strm.hb  # noqa: F401
        import strm.rel  # noqa: F401
        import strm.sm  # noqa: F401
        from strm import req

        live, tally = arm(sys.modules)
        report["tally"] = tally

        names = sorted(f for f in os.listdir(reqdir) if f.endswith(".txt"))
        rows = []
        t0 = time.time()
        for f in names:
            name = f[:-4]
            try:
                req.run(name, os.path.join(reqdir, f), rows)
            except Exception as exc:
                report["errors"].append("%s: %s: %s" % (name, type(exc).__name__, exc))
        report["secs"] = time.time() - t0
        report["rows"] = rows
        report["marks"] = marks()
        report["seen"] = len(names)
    except Exception as exc:
        report["errors"].append("run: %s: %s" % (type(exc).__name__, exc))
    finally:
        if live is not None:
            disarm(live)

    try:
        report["tree"] = tree_digest(tree)
    except Exception as exc:
        report["errors"].append("digest: %s: %s" % (type(exc).__name__, exc))

    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(report, fh)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
