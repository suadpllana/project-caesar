"""Run the rebuilt engine over the scenario set and write the reports.

This is the ONLY process that executes anything the agent wrote. It runs as an
unprivileged uid, in its own session, under a wall clock timeout, and it writes its
result into a sandbox-writable work file. It never sees the ground truth: gt.json and
oracle.py are root-only, and grading happens afterwards in a separate process that
imports nothing from the agent's tree.

Every scenario is run in a fresh interpreter state so one scenario cannot leak state
into the next, and a scenario that raises is recorded rather than allowed to abort the
whole run: a submission that crashes on one case still gets graded on the others, and
still fails, because the verifier requires every scenario to report.

Two details are deliberate. The configuration comes from the sealed copy next to this
file rather than from the tree being run, so the engine and the grader are answering the
same question whatever the tree says. And the result is written through a descriptor the
caller opened before dropping privilege, when it hands one over, so the file holding the
run's report is not writable by the uid the run executes as.
"""

import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get("APPDIR", "/app")
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

import scen


def load_cfg():
    with open(os.path.join(HERE, "view.json")) as fh:
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
        root = name.split(".")[0]
        if root in mods:
            sys.modules.pop(name, None)


def run_one(sc, base):
    drop({"view", "store", "ingest"})
    from view import drv
    cfg = dict(base)
    for k, v in (sc.get("cfg") or {}).items():
        cfg[k] = v
    d = drv.Drv(cfg)
    return d.run(sc["ops"])


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
