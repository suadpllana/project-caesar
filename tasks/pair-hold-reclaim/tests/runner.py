"""The only place a submission's code is executed.

It runs unprivileged, in its own session, under a wall clock, against a tree it cannot
write, and it writes its report through a descriptor root opened before privileges were
dropped -- the uid running the streams does not own the file it is graded on.

Four things beyond the ledger are reported, because the ledger comes back from the same
process that ran the submission and a number is never its own evidence:

  sink        Ledger rows are appended by a closure this file owns, which reads the
              calling frame and refuses any caller that is not the store. A submission
              cannot write a row without going through the store method that does the
              work the row describes.

  tally       The interpreter counts entries into the store's four recording methods,
              kept in a closure here rather than anywhere in the tree, and reports
              whether the instrumentation was still armed when the last stream ended.
              Switching it off is an act the report shows rather than a silence.

  prints      Every sealed function is fingerprinted as it actually exists in the running
              interpreter, at import and again after each stream, so rebinding one to a
              quiet copy is caught the way editing its file already is.

  digest      Every file of the executed tree outside the four declared artifacts,
              hashed after the last stream.
"""

import hashlib
import importlib
import json
import os
import sys
import traceback

TREE = os.environ["APPDIR"]
NONCE = os.environ["PHR_NONCE"]
COUNT = int(os.environ.get("PHR_COUNT", "300"))
FD = int(os.environ.get("OUTFD", "1"))
STRICT = os.environ.get("REQUIRE_MONITORING") == "1"

ARTIFACTS = ("rch.py", "cln.py", "pss.py", "obs.py")
SEALED = (("st", "Store.wipe"), ("st", "Store.fire"), ("st", "Store.letgo"),
          ("st", "Store.look"), ("st", "Store.mk"), ("ex", "apply"), ("rd", "parse"))
WATCHED = ("Store.wipe", "Store.fire", "Store.letgo", "Store.look")

sys.path.insert(0, "/tests")
import gen  # noqa: E402
import scen  # noqa: E402


def print_of(fn):
    c = fn.__code__
    flat = [repr(x) for x in c.co_consts if not hasattr(x, "co_code")]
    blob = b"|".join([c.co_code, repr(c.co_names).encode(), repr(c.co_varnames).encode(),
                      repr(flat).encode()])
    return hashlib.sha256(blob).hexdigest()[:32]


def resolve(mods, where):
    mod, path = where
    obj = mods[mod]
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def prints_now(mods):
    out = {}
    for where in SEALED:
        try:
            out["%s.%s" % where] = print_of(resolve(mods, where))
        except Exception:
            out["%s.%s" % where] = "gone"
    return out


class Watch:
    """Interpreter-level tally, held here and never in the tree."""

    def __init__(self):
        self.hits = {}
        self.armed = False
        self.tool = 3
        self.codes = {}
        self.mode = "none"

    def arm(self, mods):
        self.codes = {}
        for name in WATCHED:
            obj = mods["st"]
            for part in name.split("."):
                obj = getattr(obj, part)
            self.codes[obj.__code__] = name
        mon = getattr(sys, "monitoring", None)
        if mon is not None:
            mon.use_tool_id(self.tool, "phr")
            mon.register_callback(self.tool, mon.events.PY_START, self._hit)
            for code in self.codes:
                mon.set_local_events(self.tool, code, mon.events.PY_START)
            self.armed = True
            self.mode = "monitoring"
            return
        if STRICT:
            raise RuntimeError("sys.monitoring is required and is not present")
        sys.setprofile(self._profile)
        self.armed = True
        self.mode = "profile"

    def _hit(self, code, offset):
        name = self.codes.get(code)
        if name:
            self.hits[name] = self.hits.get(name, 0) + 1

    def _profile(self, frame, event, arg):
        if event == "call":
            name = self.codes.get(frame.f_code)
            if name:
                self.hits[name] = self.hits.get(name, 0) + 1

    def disarm(self):
        still = False
        mon = getattr(sys, "monitoring", None)
        if self.mode == "monitoring" and mon is not None:
            try:
                still = mon.get_tool(self.tool) == "phr" and all(
                    mon.get_local_events(self.tool, c) == mon.events.PY_START
                    for c in self.codes)
            except Exception:
                still = False
            try:
                for code in self.codes:
                    mon.set_local_events(self.tool, code, 0)
                mon.free_tool_id(self.tool)
            except Exception:
                pass
        elif self.mode == "profile":
            still = sys.getprofile() is self._profile
            sys.setprofile(None)
        return still


def sink_for(rows):
    def put(pn, code, rest):
        who = sys._getframe(1).f_globals.get("__name__")
        if who != "core.st":
            raise RuntimeError("ledger row offered by %r" % who)
        rows.append("%d %s %s" % (pn, code, rest))
    return put


def fresh():
    for name in [m for m in sorted(sys.modules) if m == "core" or m.startswith("core.")]:
        del sys.modules[name]
    mods = {}
    for name in ("st", "rd", "ex", "rch", "cln", "pss", "obs"):
        mods[name] = importlib.import_module("core." + name)
    return mods


def tree_digest():
    parts = []
    for base, dirs, files in os.walk(TREE):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(base, f), TREE)
            if rel.startswith("core/") and os.path.basename(rel) in ARTIFACTS:
                continue
            if f.endswith(".pyc"):
                continue
            with open(os.path.join(base, f), "rb") as fh:
                parts.append(rel + ":" + hashlib.sha256(fh.read()).hexdigest())
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def main():
    sys.path.insert(0, TREE)
    report = {"nonce": NONCE, "count": COUNT, "runs": {}, "fault": None}
    watch = Watch()
    seen_prints = []
    try:
        streams = scen.cases() + gen.build(NONCE, COUNT)
        for name, text in streams:
            mods = fresh()
            if not seen_prints:
                seen_prints.append(prints_now(mods))
                watch.arm(mods)
            else:
                watch.codes = {}
                for wname in WATCHED:
                    obj = mods["st"]
                    for part in wname.split("."):
                        obj = getattr(obj, part)
                    watch.codes[obj.__code__] = wname
                mon = getattr(sys, "monitoring", None)
                if watch.mode == "monitoring" and mon is not None:
                    for code in watch.codes:
                        mon.set_local_events(watch.tool, code, mon.events.PY_START)
            rows = []
            entry = {"log": rows, "state": [], "err": None}
            try:
                st = mods["st"].Store(sink_for(rows))
                mods["ex"].apply(st, mods["rd"].parse(text))
                entry["state"] = mods["ex"].snap(st)
            except Exception as exc:
                entry["err"] = "%s: %s" % (type(exc).__name__, exc)
            report["runs"][name] = entry
            seen_prints.append(prints_now(mods))
    except Exception:
        report["fault"] = traceback.format_exc()[-2000:]
    report["armed"] = watch.disarm()
    report["mode"] = watch.mode
    report["tally"] = watch.hits
    report["prints"] = seen_prints[0] if seen_prints else {}
    report["prints_drifted"] = [p for p in seen_prints[1:] if p != seen_prints[0]][:1]
    try:
        report["digest"] = tree_digest()
    except Exception as exc:
        report["digest"] = "unreadable: %s" % type(exc).__name__
    with os.fdopen(os.dup(FD), "w") as fh:
        json.dump(report, fh)
        fh.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
