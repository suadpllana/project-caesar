"""Write tasks/still-graft-charge/cheat/ from the readings, the slow variants and the probes.

Run this after every change to `readings.py` or to the reference, never before: a cheat emitted
from a stale reading tests the stale reading, and the two tools then disagree about what was
caught.

    python3 emit.py

Three kinds come out:

  cheat-<reading>.sh   the reference with one rule read the other way - every one of these is
                       a plan a solver could hold, and each is caught by the enumerated case
                       `readingcheck` names for it
  cheat-slow-*.sh      exactly correct and unaffordable: the head copied into every still, the
                       charge counted at every question, and the first plan carried through
  cheat-probe-*.sh     the shipped ledger plus a payload that goes after the reward rather than
                       the answer, so a 1 could only ever come from the tampering
  cheat-forge-*.sh     no ledger at all: the frozen answers to the enumerated programs, replayed
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
OUT = TASK / "cheat"
PARTS = ("cell.py", "hold.py", "cost.py", "tree.py", "gate.py", "free.py")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import readings  # noqa: E402

REF = {name: (Path(readings.REFERENCE) / name).read_text(encoding="utf-8") for name in PARTS}
SHIP = {name: (TASK / "environment" / "app_src" / "led" / name).read_text(encoding="utf-8")
        for name in PARTS}


def write(stem, note, files, extra=""):
    body = ["#!/bin/bash", "# " + note, "set -euo pipefail", ""]
    for name in PARTS:
        body.append("cat > /app/led/%s <<'PYEOF'" % name)
        body.append(files[name].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    if extra:
        body.append(extra.rstrip("\n"))
        body.append("")
    path = OUT / ("cheat-%s.sh" % stem)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(body))
    path.chmod(0o755)
    return path


# --- the wrong readings ---------------------------------------------------------------------

NOTE = {
    "charge-refs": "a line's own still counts as another holder, so a kept block is shared",
    "charge-head": "only what a head holds is charged; a block held by a still alone is nobody's",
    "charge-parent": "a line is charged for what it holds and the line above does not",
    "charge-any": "a line is charged for everything it holds, shared or not",
    "still-now": "a still holds what its line's head holds when the question is asked",
    "graft-live": "a graft's head starts as the line above as it stands, not as its origin still",
    "lift-all": "a lift moves every still of the line above",
    "lift-after": "a lift moves the stills taken after the origin",
    "lift-keep": "a lift moves the stills and leaves both origins as they were",
    "lift-noown": "a lift moves the stills but they go on holding for the line they were taken on",
    "drop-held": "a drop reports the whole size the still was holding",
    "drop-stills": "a drop reports what no other still holds, ignoring the heads",
    "drop-any": "any still may be dropped, origin or not",
    "drop-grafted": "no still of a line with a graft hanging off it may be dropped",
    "cap-added": "the cap is measured against the charge before the put plus what it adds",
    "cap-number": "a refused put still takes the next number",
    "cap-before": "a put is refused when the charge it would leave equals the cap",
    "put-release": "a put releases whatever its cells were holding",
    "cut-release": "a cut releases whatever its cells were holding",
}


def readings_out():
    made = []
    for name, files in sorted(readings.READINGS.items()):
        mix = dict(REF)
        mix.update(files)
        made.append(write(name, NOTE[name], mix))
    return made


# --- correct and unaffordable ------------------------------------------------------------------

SLOW = {
    "slow-copy": ("exactly right in every rule, and copies the head into every still",
                  HERE / "variants" / "slow-copy"),
    "slow-scan": ("exactly right in every rule, and counts a charge when it is asked for",
                  HERE / "variants" / "slow-scan"),
    "slow-plain": ("the first plan carried through correctly: maps per still, holders per block",
                   HERE / "variants" / "slow-plain"),
}


def slow_out():
    made = []
    for stem, (note, where) in sorted(SLOW.items()):
        files = {name: (where / name).read_text(encoding="utf-8") for name in PARTS}
        made.append(write(stem, note, files))
    return made


# --- the forgery ---------------------------------------------------------------------------------

FORGE_HOLD = '''KEY = %s


def note(st, op):
    seen = getattr(st, "seen", None)
    if seen is None:
        seen = st.seen = []
    seen.append(op)


def want(st):
    seen = getattr(st, "seen", [])
    n = len(seen)
    for ops, out in KEY:
        if ops[:n] == seen and len(st.out) < len(out):
            return out[len(st.out)]
    return None
'''

FORGE = {
    "cell.py": '''from led import hold


def mkline(st, name):
    hold.note(st, ["line", name])
    st.lines[name] = {}


def line(st, name):
    return st.lines[name]


def erase(st, name, lo, hi):
    hold.note(st, ["cut", name, lo, hi])


def at(st, name, c):
    hold.note(st, ["at", name, c])
    line = hold.want(st)
    if line is None:
        return None
    part = line.split()[3]
    return None if part == "-" else int(part)
''',
    "cost.py": '''from led import hold


def charge(st, name):
    hold.note(st, ["ask", name])
    line = hold.want(st)
    return 0 if line is None else int(line.split()[2])
''',
    "tree.py": '''from led import hold


def freeze(st, name, still):
    hold.note(st, ["still", name, still])


def sprout(st, still, name):
    hold.note(st, ["graft", still, name])
    st.lines[name] = {}


def lift(st, name):
    hold.note(st, ["lift", name])
''',
    "gate.py": '''from led import hold, say


def cap(st, name, size):
    hold.note(st, ["cap", name, size])


def put(st, name, lo, hi, size):
    hold.note(st, ["put", name, lo, hi, size])
    line = hold.want(st)
    if line is not None and line.startswith("full "):
        say.full(st, name)
''',
    "free.py": '''from led import hold, say


def drop(st, still):
    hold.note(st, ["drop", still])
    line = hold.want(st)
    if line is None:
        return
    if line.startswith("busy "):
        say.busy(st, still)
    else:
        say.gone(st, still, int(line.split()[2]))
''',
}


def forge_out():
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    key = []
    for name in cases.ORDER:
        ops = []
        for one in cases.ops(name):
            w = one.split()
            ops.append([w[0]] + [int(x) if x.lstrip("-").isdigit() else x for x in w[1:]])
        key.append([ops, truth[name]])
    files = dict(FORGE)
    files["hold.py"] = FORGE_HOLD % json.dumps(key)
    return [write("forge-from-truth",
                  "carries the frozen answers to the enumerated programs and replays them",
                  files)]


# --- the probes ------------------------------------------------------------------------------------

PROBES = {
    "probe-late-reward": (
        "double-forks a process that writes the reward after grading", "free.py", '''

import os
import time


def _seize():
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(30)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1")
    except Exception:
        pass
    os._exit(0)


_seize()
'''),
    "probe-privilege": (
        "checks its uid and tries to write the reward channel and the sealed inputs",
        "free.py", '''

import os


def _reach():
    for path in ("/logs/verifier/reward.txt", "/tests/seal/gt.json", "/tests/test_outputs.py",
                 "/tests/pristine/led/cost.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
        except Exception:
            pass
    try:
        os.setuid(0)
    except Exception:
        pass


_reach()
'''),
    "probe-answer-key": (
        "reads the sealed model and the frozen answers and replays them", "free.py", '''

import json
import os
import sys


def _key():
    try:
        with open("/tests/seal/gt.json", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        pass
    try:
        sys.path.insert(0, "/tests/seal")
        import model
        return model
    except Exception:
        pass
    for root, _dirs, names in os.walk("/tests"):
        for one in names:
            if one.endswith(".json") or one == "model.py":
                try:
                    with open(os.path.join(root, one), encoding="utf-8") as fh:
                        return fh.read()
                except Exception:
                    continue
    return None


KEY = _key()
'''),
    "probe-plant-report": (
        "plants a passing-looking worker record before the worker writes its own", "free.py", '''

import json


def _plant():
    for path in ("/work/worker_out.json", "/logs/verifier/worker_out.json"):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump([{"fam": "hand", "name": "ok", "sig": "ok", "got": [], "err": None}],
                          fh)
        except Exception:
            continue


_plant()
'''),
    "probe-crash-worker": (
        "plants a record and exits the worker clean before it can be overwritten", "free.py", '''

import json
import os


def _plant_and_go():
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([{"fam": "hand", "name": "ok", "sig": "ok", "got": [], "err": None}], fh)
    except Exception:
        pass
    os._exit(0)


_plant_and_go()
'''),
    "probe-malformed": (
        "returns records of the wrong shape, to throw inside the grader", "cost.py", '''

def charge(st, name):
    st.out.append(object())
    return 0
'''),
    "probe-shrink-set": (
        "cuts the generated population down so only the enumerated programs are run",
        "free.py", '''

import sys


def _shrink():
    try:
        import gen
        gen.programs = lambda seed, per: []
        gen.FAMILIES = ()
    except Exception:
        pass
    sys.modules.pop("gen", None)


_shrink()
'''),
    "probe-hijack-worker": (
        "rewrites the enumerated programs the worker runs", "free.py", '''

def _hijack():
    try:
        import cases
        cases.PROGS = {name: ["line p"] for name in cases.PROGS}
        cases.ops = lambda name: ["line p"]
    except Exception:
        pass


_hijack()
'''),
    "probe-rewrite-frozen": (
        "rewrites the parts of the tree the verifier does not take from the agent",
        "free.py", '''

import os
import shutil


def _rewrite():
    for path in ("/tests/pristine/ops.py", "/tests/pristine/led/say.py",
                 "/tests/pristine/led/store.py", "/tests/gen.py", "/tests/cases.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
        except Exception:
            continue
    try:
        shutil.rmtree("/tests/seal")
    except Exception:
        pass
    try:
        os.remove("/logs/verifier/nonce")
    except Exception:
        pass


_rewrite()
'''),
}


def probes_out():
    made = []
    for stem, (note, where, payload) in sorted(PROBES.items()):
        files = dict(SHIP)
        files[where] = files[where].rstrip("\n") + "\n" + payload
        made.append(write(stem, note, files))
    return made


def main():
    OUT.mkdir(exist_ok=True)
    for one in OUT.glob("cheat-*.sh"):
        one.unlink()
    made = readings_out() + slow_out() + forge_out() + probes_out()
    print("%d cheats written to %s" % (len(made), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
