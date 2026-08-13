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
"""

import json
import os
import sys
import traceback

APP = os.environ.get("APPDIR", "/app")
sys.path.insert(0, APP)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scen


def load_cfg():
    with open(os.path.join(APP, "conf", "view.json")) as fh:
        return json.load(fh)


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
    out = argv[1] if len(argv) > 1 else "/work/out.json"
    reports, errors = {}, {}
    try:
        base = load_cfg()
    except Exception:
        payload = {"reports": {}, "errors": {"fatal": traceback.format_exc()}}
        with open(out, "w") as fh:
            json.dump(payload, fh)
        return 0
    for sc in scen.SCENARIOS:
        try:
            reports[sc["name"]] = run_one(sc, base)
        except Exception:
            errors[sc["name"]] = traceback.format_exc()
    with open(out, "w") as fh:
        json.dump({"reports": reports, "errors": errors}, fh, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
