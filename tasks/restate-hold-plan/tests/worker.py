"""Stage one: run the submitted planner on every graded pipeline. Decides nothing.

This is the only process that executes submitted code, so it runs as an unprivileged uid, in a
session of its own, under the task's 60 second clock (tests/test.sh). It copies the pristine
tree, lays the five collected planner files over it, prints every plan it is asked for, and
writes what came out - with a digest of each pipeline, so a submission cannot quietly plan a
different pipeline from the one it is graded on. Stage two reads that file as hostile input: a
crash, a hang or a missing record here is a failure there, never a pass.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("RHP_TESTS", "/tests")
WORK = os.environ.get("RHP_WORK", "/work")
SUBMITTED = os.environ.get("RHP_PLAN", "/app/plan")
COLLECTED = ("keep.py", "reach.py", "look.py", "settle.py", "order.py")

sys.path.insert(0, TESTS)
import cases  # noqa: E402
import gen  # noqa: E402


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def planner_tree():
    """The pristine tree with the five submitted files laid over it; nothing else is taken."""
    home = tempfile.mkdtemp(prefix="plan-", dir=WORK)
    app = os.path.join(home, "app")
    shutil.copytree(os.path.join(TESTS, "pristine"), app)
    for name in COLLECTED:
        mine = os.path.join(SUBMITTED, name)
        if os.path.isfile(mine):
            shutil.copyfile(mine, os.path.join(app, "plan", name))
    return app


def main(out_path):
    with open(os.path.join(WORK, "seed"), encoding="utf-8") as fh:
        seed = fh.read().strip()
    with open(os.path.join(WORK, "each"), encoding="utf-8") as fh:
        each = int(fh.read().strip())

    app = planner_tree()
    sys.path.insert(0, app)
    import run_plan  # the frozen driver, from the pristine copy

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += gen.programs(seed, each)

    records = []
    for family, name, lines in work:
        record = {"family": family, "name": name, "digest": digest(lines)}
        try:
            record["plan"] = run_plan.run("\n".join(lines) + "\n")
        except Exception:
            record["error"] = traceback.format_exc(limit=2).strip().splitlines()[-1]
        records.append(record)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(records, fh)


if __name__ == "__main__":
    main(sys.argv[1])
