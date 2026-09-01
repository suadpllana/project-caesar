"""Run the rebuilt engine over the scenario set and write the reports.

This is the ONLY process that executes anything the agent wrote. It runs as an unprivileged
uid, in its own session, under a wall clock timeout, and it writes its result into a file
that uid cannot open for writing. It never sees the ground truth: gt.json and oracle.py are
root-only, and grading happens afterwards in a separate process that imports nothing from
the agent's tree.

Every scenario is run in a fresh interpreter state so one cannot leak into the next, and a
scenario that raises is recorded rather than allowed to abort the whole run: a submission
that crashes on one case still gets graded on the others, and still fails, because the
verifier requires every scenario to report.

Two details are deliberate. The configuration comes from the sealed copy next to this file
rather than from the tree being run, so the engine and the grader answer the same question
whatever the tree says. And the result is written through a descriptor the caller opened
before dropping privilege, when it hands one over, so the file the run is graded on is not
owned by the uid that produced it.
"""

import hashlib
import json
import os
import sys
import traceback
import types

HERE = os.path.dirname(os.path.abspath(__file__))

# Kept in step with oracle.SEALED, which is root-only and cannot be imported from here.
# build_gt.py fails if the two lists ever drift apart.
SEALED = (
    ("seg/table.py", "Seg.get"),
    ("seg/table.py", "Seg.raw"),
    ("seg/read.py", "resolve"),
    ("seg/store.py", "Store.read"),
    ("seg/store.py", "Store.chain"),
    ("seg/store.py", "Store.map"),
    ("seg/store.py", "Store.swap"),
    ("merge/core.py", "Cur.next"),
    ("merge/core.py", "Core.take"),
    ("merge/core.py", "Core.emit"),
    ("merge/core.py", "Core.probe"),
    ("merge/pick.py", "choose"),
    ("merge/drv.py", "Drv.__init__"),
    ("merge/drv.py", "Drv.op"),
    ("merge/drv.py", "Drv.job"),
    ("merge/drv.py", "Drv.run"),
    ("merge/drv.py", "Drv.report"),
)


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


MON = 3
WATCHED = ("take", "emit", "probe")


def arm(codes):
    """Have the interpreter itself count entries into the counted operations.

    Everything else is a record the engine keeps, and a record the engine keeps is a record
    the submitted file can edit: a module level log can be truncated and an integer
    attribute can be assigned. This counts through sys.monitoring instead, so a call is seen
    wherever it came from - including through a reference captured at import time, which is
    how a submission would otherwise pull records out of a job without the counted path ever
    knowing. The tally lives in this function's closure, not in the tree.
    """
    tally = {}
    wanted = set(codes)
    mon = getattr(sys, "monitoring", None)

    if mon is None:
        # Python 3.11 and older, which is the authoring host rather than the verifier image.
        # The profile hook sees the same calls; it is easier for a run to switch off, and
        # disarm() reports that it was.
        def entered(frame, event, arg):
            if event == "call" and frame.f_code in wanted:
                name = frame.f_code.co_name
                tally[name] = tally.get(name, 0) + 1
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
        mon.use_tool_id(MON, "verifier")
    except ValueError:
        pass
    mon.register_callback(MON, mon.events.PY_START, entered)
    for code in codes:
        mon.set_local_events(MON, code, mon.events.PY_START)

    def disarm():
        """Was the instrumentation still ours and still armed when the run finished?"""
        ok = mon.get_tool(MON) == "verifier"
        previous = mon.register_callback(MON, mon.events.PY_START, entered)
        if previous is not entered:
            ok = False
        for code in codes:
            if not mon.get_local_events(MON, code) & mon.events.PY_START:
                ok = False
            mon.set_local_events(MON, code, 0)
        mon.register_callback(MON, mon.events.PY_START, None)
        try:
            mon.free_tool_id(MON)
        except ValueError:
            pass
        return ok, "monitoring", dict(tally)

    return disarm


def live():
    """Fingerprint the engine functions as they actually are in this interpreter.

    Hashing the tree on disk catches a submission that rewrites the engine. This catches one
    that leaves the file alone and replaces the function object instead.
    """
    out = {}
    for rel, qual in SEALED:
        key = "%s:%s" % (rel, qual)
        mod = sys.modules.get(rel[:-3].replace("/", "."))
        if mod is None:
            out[key] = "unloaded"
            continue
        obj = mod
        try:
            for part in qual.split("."):
                obj = getattr(obj, part)
            out[key] = fingerprint(obj.__code__)
        except AttributeError:
            out[key] = "replaced"
    return out


APP = os.environ.get("APPDIR", "/app")
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import scen


def load_cfg():
    with open(os.path.join(HERE, "store.json")) as fh:
        return json.load(fh)


def emit(target, payload):
    payload["nonce"] = os.environ.get("RUN_NONCE", "")
    text = json.dumps(payload, sort_keys=True)
    if target.startswith("fd:"):
        fd = int(target[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text.encode("utf-8"))
        return
    with open(target, "w") as fh:
        fh.write(text)


def drop(mods):
    for name in list(sys.modules):
        if name.split(".")[0] in mods:
            sys.modules.pop(name, None)


def run_one(sc, base):
    drop({"merge", "seg"})
    from merge import drv
    cfg = dict(base)
    for k, v in (sc.get("cfg") or {}).items():
        cfg[k] = v
    loaded = live()
    from merge import core
    disarm = arm([core.Core.take.__code__, core.Core.emit.__code__,
                  core.Core.probe.__code__])
    try:
        rep = drv.Drv(cfg).run(sc["ops"])
    finally:
        intact, how, tally = disarm()
    # Written after the report is built, so whatever produced the report did not produce
    # these: the fingerprints are taken once at import and once when the run is over, and
    # the tally comes from the interpreter rather than from the tree.
    if not isinstance(rep, dict):
        rep = {"report": rep}
    rep["fp"] = loaded
    rep["fp_end"] = live()
    rep["mon"] = dict((k, tally.get(k, 0)) for k in WATCHED)
    rep["mon_intact"] = intact
    rep["mon_how"] = how
    return rep


def main(argv):
    out = argv[1] if len(argv) > 1 else "/work/run/out.json"
    reports, errors = {}, {}
    try:
        base = load_cfg()
    except Exception:
        emit(out, {"reports": {}, "errors": {"fatal": traceback.format_exc()}})
        return 0
    for sc in scen.SCENARIOS:
        try:
            reports[sc["name"]] = run_one(sc, base)
        except Exception:
            errors[sc["name"]] = traceback.format_exc()
    emit(out, {"reports": reports, "errors": errors})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
