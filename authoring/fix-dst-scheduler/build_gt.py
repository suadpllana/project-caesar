"""Freeze the enumerated answers, and prove a contract change was additive.

The answers come from the sealed model and are cross-checked against the
reference before anything is written. The old file is read first: any plan
whose answer moved is printed as a contract change, because an answer that
changes without anyone deciding to change it is the failure this file exists to
catch.

    python build_gt.py            report, write nothing
    python build_gt.py --write    write tests/gt.json
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harness  # noqa: E402

sys.path.insert(0, harness.TESTS)
sys.path.insert(0, harness.SEAL)

import cases  # noqa: E402
import model  # noqa: E402

GT = os.path.join(harness.TESTS, "gt.json")


def reference_traces():
    work = tempfile.mkdtemp(prefix="lyd-gt-")
    app = harness.build_app(os.path.join(harness.TASK, "solution"), work)
    script = os.path.join(work, "drive.py")
    body = (
        "import json, sys\n"
        "sys.path.insert(0, __APP__)\n"
        "sys.path.insert(0, __TESTS__)\n"
        "import cases\n"
        "from sked import emit, lane, read\n"
        "print(json.dumps({n: emit.lines(lane.run(read.parse(t)))\n"
        "                  for n, t in cases.PLANS}))\n"
    ).replace("__APP__", repr(app)).replace("__TESTS__", repr(harness.TESTS))
    with open(script, "w", newline="\n") as fh:
        fh.write(body)
    res = subprocess.run([sys.executable, script], capture_output=True, text=True,
                         timeout=300)
    if res.returncode != 0:
        raise SystemExit("reference failed:\n" + res.stderr)
    return json.loads(res.stdout)


def main():
    fresh = {name: model.trace(text) for name, text in cases.PLANS}
    ref = reference_traces()
    split = [n for n in fresh if ref.get(n) != fresh[n]]
    if split:
        raise SystemExit("reference and model disagree on: %s" % ", ".join(sorted(split)))

    old = {}
    if os.path.isfile(GT):
        with open(GT) as fh:
            old = json.load(fh)
    moved = [n for n in old if n in fresh and old[n] != fresh[n]]
    gone = [n for n in old if n not in fresh]
    added = [n for n in fresh if n not in old]

    print("plans %d, events %d" % (len(fresh), sum(len(v) for v in fresh.values())))
    print("held byte for byte: %d" % len([n for n in old if n in fresh and old[n] == fresh[n]]))
    for n in sorted(moved):
        print("CONTRACT CHANGE: %s moved" % n)
        for i in range(max(len(old[n]), len(fresh[n]))):
            a = old[n][i] if i < len(old[n]) else "<none>"
            b = fresh[n][i] if i < len(fresh[n]) else "<none>"
            if a != b:
                print("    was %-32s now %s" % (a, b))
                break
    for n in sorted(gone):
        print("removed: %s" % n)
    for n in sorted(added):
        print("new: %s (%d lines)" % (n, len(fresh[n])))

    if "--write" in sys.argv:
        with open(GT, "w", newline="\n") as fh:
            json.dump(fresh, fh, indent=1, sort_keys=True)
            fh.write("\n")
        with open(GT) as fh:
            if "\r" in fh.read():
                raise SystemExit("gt.json picked up a carriage return")
        print("wrote %s" % GT)
    return 1 if moved else 0


sys.exit(main())
