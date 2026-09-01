"""Run the rebuilt policy over the scenario set and write what the scheduler did.

This is the only process that executes anything the agent wrote. It runs as an unprivileged
uid, in its own session, under a wall clock timeout, and it reports through a descriptor that
uid cannot reopen. It never sees the expected schedules: gt.json and the sealed model are
root-only, and grading happens afterwards in a process that imports nothing from the agent's
tree.

The scenario set is the fourteen written ones plus a batch drawn from a seed handed in at run
time. Both halves are generated here, from scen.py, which the run is welcome to read - the
point of the drawn half is not that it is secret but that it is different every run, so there
is no schedule anybody could have worked out in advance and written into a table.

Each scenario runs with the engine modules freshly imported, so nothing carries over, and a
scenario that raises is recorded rather than allowed to end the run: a policy that crashes on
one case still gets graded on the rest, and still fails, because every scenario has to report.
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
sys.path.insert(0, HERE)

import scen

# Kept in step with oracle.SEALED, which is root-only and cannot be imported from here.
# build_gt.py refuses to run if the two lists have drifted apart.
SEALED = (
    ("rt/core.py", "Core.pick"),
    ("rt/core.py", "Core.set"),
    ("rt/core.py", "Core.ready"),
    ("rt/core.py", "Core.run_one"),
    ("rt/core.py", "Core.top"),
    ("rt/core.py", "Core.expire"),
    ("rt/core.py", "Core.run"),
    ("rt/core.py", "Core.acquire"),
    ("rt/core.py", "Core.report"),
    ("rt/boot.py", "build"),
)


def digest(code):
    """A hash of a function as the interpreter is actually holding it."""
    h = hashlib.sha256()
    h.update(code.co_code)
    h.update(repr(code.co_names).encode("utf-8"))
    h.update(repr(code.co_varnames).encode("utf-8"))
    for k in code.co_consts:
        if isinstance(k, types.CodeType):
            h.update(digest(k).encode("utf-8"))
        else:
            h.update(repr(k).encode("utf-8"))
    return h.hexdigest()


def snapshot():
    """Fingerprint the scheduler as loaded.

    Hashing the tree on disk catches a policy that rewrites the scheduler. This catches the
    one that leaves the file alone and rebinds the function, which is the cheaper way to make
    the schedule say whatever you want.
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
            out[key] = digest(obj.__code__)
        except AttributeError:
            out[key] = "replaced"
    return out


def settings():
    with open(os.path.join(HERE, "sched.json")) as fh:
        return json.load(fh)


def forget():
    for name in list(sys.modules):
        if name.split(".")[0] == "rt":
            sys.modules.pop(name, None)


def one(sc, base):
    forget()
    from rt import boot, prio
    cfg = dict(base)
    for k, v in (sc.get("cfg") or {}).items():
        cfg[k] = v
    core = boot.build(cfg, sc)
    opened = snapshot()
    core.bind(prio.Prio(core))
    core.run(cfg["limit"])
    rep = core.report()
    if not isinstance(rep, dict):
        rep = {"report": rep}
    # Taken after the schedule exists, so whatever produced the schedule did not produce these.
    rep["fp"] = opened
    rep["fp_end"] = snapshot()
    return rep


def publish(where, payload):
    payload["nonce"] = os.environ.get("RUN_NONCE", "")
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    if where.startswith("fd:"):
        fd = int(where[3:])
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, body)
        return
    with open(where, "wb") as fh:
        fh.write(body)


def main(argv):
    where = argv[1] if len(argv) > 1 else "/work/run/out.json"
    seed = os.environ.get("SCEN_SEED", "")
    drawn = int(os.environ.get("SCEN_DRAWN", "12"))
    runs, broke = {}, {}
    try:
        base = settings()
    except Exception:
        publish(where, {"runs": {}, "broke": {"fatal": traceback.format_exc()}, "seed": seed})
        return 0
    todo = list(scen.SCENARIOS)
    if seed:
        todo += scen.batch(scen.seed_from(seed), drawn)
    for sc in todo:
        try:
            runs[sc["name"]] = one(sc, base)
        except Exception:
            broke[sc["name"]] = traceback.format_exc()
    publish(where, {"runs": runs, "broke": broke, "seed": seed, "drawn": drawn})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
