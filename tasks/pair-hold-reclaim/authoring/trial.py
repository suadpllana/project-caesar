"""Grade a policy directory end to end on this host, without containers.

Faster than the two-image trial and useful while iterating, and it covers exactly the
part the container run also covers: the streams, the ledger, the final state and the
enumerated ground truth. It does NOT cover the privilege drop, the locked reward channel,
the root-only ground truth, the inherited descriptor or the process teardown. Say so in
any handover that leans on it -- tools/docker_trial2.py is the run that proves those.

    python3 authoring/trial.py                       the reference
    python3 authoring/trial.py authoring/variants/ok-relax
    python3 authoring/trial.py --shipped
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def main(argv):
    where = TASK / "solution"
    if len(argv) > 1 and argv[1] == "--shipped":
        where = None
    elif len(argv) > 1:
        where = pathlib.Path(argv[1])
        if not where.is_absolute():
            where = TASK / argv[1]
    count = int(argv[2]) if len(argv) > 2 else 300

    streams = scen.cases() + gen.build("trial", count)
    want = {n: oracle.play(t) for n, t in streams}
    stored = json.loads((TASK / "tests" / "gt.json").read_text(encoding="utf-8"))
    for name, _ in scen.cases():
        if stored[name]["log"] != want[name]["log"]:
            print("gt.json has drifted from the model on %s" % name)
            return 1

    got = harness.drive(harness.stage(TASK / "environment" / "app_src", where), streams)
    wrong = []
    for name, _ in streams:
        g, w = got[name], want[name]
        if g["err"] or g["log"] != w["log"] or g["state"] != w["state"]:
            wrong.append(name)
    print("%s: %d of %d streams right -> reward %d"
          % (where.name if where else "shipped", len(streams) - len(wrong), len(streams),
             0 if wrong else 1))
    if wrong:
        print("   first miss: %s" % wrong[0])
    return 0 if not wrong else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
