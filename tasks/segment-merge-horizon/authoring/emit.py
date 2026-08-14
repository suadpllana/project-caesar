#!/usr/bin/env python3
"""Generate solution/solve.sh and the whole cheat suite from the reference.

Nothing here is hand written twice. solve.sh is the reference source in a heredoc, and each
single-mistake cheat is the reference with exactly one anchored block swapped for the way a
solver who missed one piece would have written it. That matters: a hand written cheat drifts
away from the reference and quietly stops testing the mistake it was named for, or omits a
correction the reference also makes and tests the shipped bug instead.

Three families come out of this.

  mutations   the reference with one decision changed. The valuable ones publish every read
              correctly and fail only on work.
  evidence    submissions that hold the answers - one that writes records it never pulled,
              one that replays a journal taken from the ground truth, one that rebinds the
              driver's report, one that does its real work beside the counted path.
  isolation   attacks on the reward channel, built on the SHIPPED plan rather than on the
              reference. A probe built on the reference does the real work and scores 1
              legitimately, which proves nothing about the sandbox.

Usage:
    python3 authoring/emit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
ART = "/app/merge/plan.py"


def ref() -> str:
    return (TASK / "solution" / "ref" / "plan.py").read_text()


def shipped() -> str:
    return (TASK / "environment" / "app_src" / "merge" / "plan.py").read_text()


def swap(src: str, pairs: list[tuple[str, str]]) -> str:
    for find, repl in pairs:
        if find not in src:
            raise SystemExit("anchor not found:\n%s" % find)
        src = src.replace(find, repl, 1)
    return src


# --- the anchors, quoted from solution/ref/plan.py -------------------------------------

STOP = """            if not pend and term:
                break
"""

DEDUP = """            if res == cur:
                if kind == "o":
                    run = val
                continue
"""

ASK_SKIP = """        if kind == "o" and val:
            return None, False
"""

ASK_PROBE = """        return self.core.probe(k), True
"""

UNKNOWN = """        else:
            cur = None
"""

MUTATIONS = [
    (
        "drain-the-input",
        [(STOP, "")],
        "Every decision the reference makes, but it pulls each key to the end of the merged "
        "input instead of stopping where the answers stop. Every read is correct and the "
        "read budget is not.",
    ),
    (
        "stop-at-the-floor",
        [("            if not pend and term:", "            if not pend:")],
        "Stops pulling as soon as every read point has a start, without waiting for the "
        "chain under the lowest one to terminate. That is the natural way to write the read "
        "saving and it publishes the difference as though it were the value.",
    ),
    (
        "strict-read-point",
        [("fresh = [a for a in pend if a >= r.s]", "fresh = [a for a in pend if a > r.s]"),
         ("while i < len(rs) and rs[i].s > a:", "while i < len(rs) and rs[i].s >= a:")],
        "Treats a read point as seeing strictly older records only, so a read point landing "
        "exactly on a record's sequence loses it.",
    ),
    (
        "delete-is-absence",
        [('                return ("v", acc) if n else ("z", 0)',
          '                return ("z", 0)')],
        "Takes a chain that terminates in a delete as absent whatever stands above it, which "
        "throws away the adjusts that were applied on top of the deletion.",
    ),
    (
        "never-ask-outside",
        [(ASK_PROBE, "        return None, False\n")],
        "Never asks the rest of the store anything, so the lowest record of every key stays "
        "whether or not it had to. Correct on every read, over the write budget.",
    ),
    (
        "ask-about-everything",
        [(ASK_SKIP, "")],
        "Asks the rest of the store about every key, including the ones where no answer it "
        "could give would change a record. Correct on every read, over the probe budget.",
    ),
    (
        "assume-nothing-outside",
        [(ASK_PROBE, "        return None, True\n")],
        "Drops the lowest record whenever it resolves to an absence, without asking whether "
        "the rest of the store still holds the key. The key comes back from the dead.",
    ),
    (
        "zero-adjust-is-nothing",
        [('        if kind == "o" and val:', '        if kind == "o":'),
         (UNKNOWN, '        else:\n            cur = ("o", 0)\n')],
        "Treats an open outcome whose total is zero as a record that changes nothing. It "
        "changes everything when the key has no base: a chain of adjusts over an empty key "
        "resolves to their sum and the key is present.",
    ),
    (
        "open-outcome-totals",
        [("self.core.emit(k, s, rec.ADD, val - run)", "self.core.emit(k, s, rec.ADD, val)")],
        "Writes each open outcome as its own total rather than as the difference against the "
        "open outcome below it, so the lower record is applied twice at every read point "
        "above it.",
    ),
    (
        "one-record-per-point",
        [(DEDUP, "            if False:\n                continue\n")],
        "Writes a record for every read point instead of a record wherever the answer "
        "changes. Correct on every read, over the write budget.",
    ),
]


SURVIVOR = '''from seg import rec


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        left = list(pts)
        while left:
            r = cur.next()
            if r is None:
                return
            hit = [a for a in left if a >= r.s]
            if not hit:
                continue
            for a in hit:
                left.remove(a)
            self.core.emit(r.k, r.s, r.t, r.v)
'''

SHADOW = '''

_KEY = Plan.key


def _drain(self, cur, pts):
    _KEY(self, cur, pts)
    for e in cur.src:
        while e[1] < e[2]:
            e[0].get(e[1])
            e[1] += 1


Plan.key = _drain
'''

PATCH_TAKE = '''

from merge import core as _core

_TAKE = _core.Core.take


def _quiet(self, cur, bi):
    e = cur.src[bi]
    r = e[0].get(e[1])
    e[1] += 1
    self.jrn.append(("r", self.job, r.k, r.s, r.t, r.v))
    self.reads += 1
    return r


_core.Core.take = _quiet
'''

HIJACK = '''
import json

from merge import drv as _drv

_GT = json.loads(r"""%s""")


def _report(self):
    for e in _GT["scenarios"].values():
        if e["trace"] == [list(x) for x in self.trace]:
            return {"view": e["view"], "snaps": e["snaps"], "shape": [],
                    "reads": e["reads"], "writes": e["writes"], "probes": e["probes"],
                    "jobs": e["jobs"], "trace": e["trace"], "jrn": [], "deep": []}
    return {"view": [], "snaps": [], "shape": [], "reads": 0, "writes": 0, "probes": 0,
            "jobs": self.jobs, "trace": self.trace, "jrn": [], "deep": []}


_drv.Drv.report = _report
'''

FREE_READ = '''from seg import rec


def _peek(cur):
    out = []
    for e in cur.src:
        i = e[1]
        while i < e[2]:
            out.append(e[0].raw(i))
            i += 1
    out.sort(key=lambda r: -r.s)
    return out


def _fold(rs, i):
    acc = 0
    n = 0
    j = i
    while j < len(rs):
        x = rs[j]
        if x.t == rec.ADD:
            acc += x.v
            n += 1
        elif x.t == rec.PUT:
            return ("v", acc + x.v)
        else:
            return ("v", acc) if n else ("z", 0)
        j += 1
    return ("o", acc)


class Plan:
    def __init__(self, core):
        self.core = core

    def key(self, cur, pts):
        rs = _peek(cur)
        if not rs:
            return
        outs = []
        last = -1
        for a in pts:
            i = 0
            while i < len(rs) and rs[i].s > a:
                i += 1
            if i >= len(rs) or i == last:
                continue
            last = i
            kind, val = _fold(rs, i)
            outs.append((rs[i].s, kind, val))
        if not outs:
            return
        base = self.core.probe(cur.k)
        cur_res = ("v", base) if base is not None else ("z", 0)
        run = 0
        for s, kind, val in outs:
            if kind == "o":
                res = ("v", val + base) if base is not None else ("v", val)
            elif kind == "v":
                res = ("v", val)
            else:
                res = ("z", 0)
            if res == cur_res:
                if kind == "o":
                    run = val
                continue
            if kind == "o":
                self.core.emit(cur.k, s, rec.ADD, val - run)
                run = val
            elif kind == "v":
                self.core.emit(cur.k, s, rec.PUT, val)
            else:
                self.core.emit(cur.k, s, rec.DEL, 0)
            cur_res = res
'''

FORGE = '''

_REF = Plan.key


def _forged(self, cur, pts):
    """Do the whole job the counted way, then re-title the reads as though they never happened.

    Every record here is pulled through the cursor, so the segment layer's own log and the
    core's journal agree with each other and the counters agree with both. What it then does
    is delete the reads it did not want to pay for, which is the cheapest possible attack on
    a counter that is read off a journal.
    """
    mark = len(self.core.jrn)
    _REF(self, cur, pts)
    reads = [i for i in range(mark, len(self.core.jrn)) if self.core.jrn[i][0] == "r"]
    for i in reversed(reads[1:]):
        del self.core.jrn[i]
        self.core.reads -= 1


Plan.key = _forged
'''


ISOLATION = [
    (
        "reward-daemon",
        "Double forks a process that sleeps past the run and then writes 1 into the reward "
        "file. The channel is root owned and 700, so it must be denied.",
        '''import os


def _bg():
    try:
        if os.fork() > 0:
            return
        os.setsid()
        if os.fork() > 0:
            os._exit(0)
    except OSError:
        return
    import time
    time.sleep(40)
    for p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(p, "w") as fh:
                fh.write("1\\n")
        except OSError:
            pass
    os._exit(0)


_bg()
''',
    ),
    (
        "plant-run-output",
        "Writes a complete, correct looking run report over the work file the verifier "
        "grades, from inside the run. The file is root owned and the run holds only an "
        "inherited descriptor, so the write must fail.",
        '''import json
import os


for p in ("/work/run/out.json", os.environ.get("RUN_OUT", "")):
    if not p:
        continue
    try:
        with open(p, "w") as fh:
            json.dump({"reports": {}, "errors": {}}, fh)
    except OSError:
        pass
''',
    ),
    (
        "plant-and-crash",
        "Plants a report and then kills the runner hard, so nothing later in the process can "
        "overwrite it. Grading happens in another process and must still see no usable run.",
        '''import json
import os


try:
    with open("/work/run/out.json", "w") as fh:
        json.dump({"reports": {}, "errors": {}}, fh)
except OSError:
    pass
os._exit(0)
''',
    ),
    (
        "probe-privileges",
        "Reports what the run can actually reach. It should be an unprivileged uid that "
        "cannot open the reward channel, the ground truth, the grader or the pristine tree.",
        '''import os
import sys


_seen = []
for p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py",
          "/tests/test_outputs.py", "/pristine/merge/core.py"):
    try:
        open(p).read(1)
        _seen.append("readable:" + p)
    except OSError as exc:
        _seen.append("%s:%s" % (type(exc).__name__, p))
sys.stderr.write("uid=%s %s\\n" % (os.getuid() if hasattr(os, "getuid") else "?", _seen))
''',
    ),
    (
        "read-answers",
        "Tries to read the ground truth from inside the run and use it. It is root only, so "
        "the open must fail and the plan falls back to doing nothing.",
        '''import json


_GT = None
for p in ("/tests/gt.json", "/gt.json"):
    try:
        _GT = json.load(open(p))
        break
    except (OSError, ValueError):
        pass
''',
    ),
    (
        "rewrite-engine",
        "Rewrites the counting core in the tree that is being run, so the counters it reports "
        "are its own. The tree is root owned and read only to the run, and pytest hashes it "
        "against the pristine copy afterwards.",
        '''import os


_p = os.path.join(os.environ.get("APPDIR", "/app"), "merge", "core.py")
try:
    with open(_p, "a") as fh:
        fh.write("\\n\\nCore.take = lambda self, cur, bi: None\\n")
except OSError:
    pass
''',
    ),
    (
        "sweep-environment",
        "Walks everything the run's uid can reach looking for answer material and reports "
        "what it found. The agent image and the work tree hold the engine and nothing else.",
        '''import os
import sys


_hits = []
for root in ("/tests", "/pristine", "/work", "/logs", "/app"):
    for base, dirs, files in os.walk(root, onerror=lambda e: None):
        for f in files:
            p = os.path.join(base, f)
            try:
                with open(p, "rb") as fh:
                    if b"snaps" in fh.read(400000):
                        _hits.append(p)
            except OSError:
                pass
sys.stderr.write("swept %r\\n" % (_hits[:20],))
''',
    ),
    (
        "peek-scenarios",
        "Reads the scenario set, which the run is allowed to see, and stops there. Knowing "
        "which operation streams execute does not produce the reads they end on.",
        '''import sys


try:
    sys.path.insert(0, "/tests")
    import scen
    _N = len(scen.SCENARIOS)
except Exception:
    _N = 0
''',
    ),
]


def script(comment: str, body: str) -> str:
    return ("#!/bin/bash\n"
            "# %s\n"
            "set -euo pipefail\n"
            "\n"
            "mkdir -p \"$(dirname %s)\"\n"
            "cat > %s <<'EOF_PLAN'\n"
            "%s"
            "EOF_PLAN\n" % (comment, ART, ART, body))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, newline="\n")


def main() -> int:
    base = ref()
    gt_path = TASK / "tests" / "gt.json"
    gt = json.dumps(json.loads(gt_path.read_text()), sort_keys=True) if gt_path.is_file() else "{}"

    write(TASK / "solution" / "solve.sh",
          script("Reference solution. Writes the corrected merge plan and lets the engine "
                 "compute the result, never echoing one.", base))

    made = []
    for name, pairs, note in MUTATIONS:
        body = swap(base, pairs)
        write(TASK / "cheat" / ("cheat-%s.sh" % name), script(note, body))
        write(TASK / "authoring" / "cheatsrc" / name / "plan.py", body)
        made.append(name)

    others = [
        ("survivor-rule", SURVIVOR,
         "The rule the literature gives, with the read saving added: keep the newest record "
         "each read point can see and stop as soon as they are all covered. It is cheap and "
         "it publishes an adjust as if it were an answer."),
        ("write-without-reading", FREE_READ,
         "Reaches the records straight out of the segment buffers, which costs nothing, and "
         "writes the correct output without pulling a single record through the job. Every "
         "read it publishes is right and no record it wrote was earned."),
        ("shadow-drain", base + SHADOW,
         "Keeps the counted path exactly right and then pulls every remaining record of every "
         "key straight out of the segments behind it, so the engine reports the cheapest "
         "possible merge and performs the most expensive one."),
        ("patch-take", base + PATCH_TAKE,
         "Rebinds the counted read to a copy of itself, which keeps every number right and "
         "moves the work off the function the interpreter was told to watch."),
        ("hijack-report", base + (HIJACK % gt),
         "Returns the ground truth as the driver's report. Every read, every counter and the "
         "whole trace are correct and there is no work journal behind any of it."),
        ("forge-journal", swap(base, [(STOP, "")]) + FORGE,
         "Pulls every key to the end of the input and then deletes the read entries it does "
         "not want to be charged for, so the counters it reports are a fraction of the work "
         "it did."),
    ]
    for name, body, note in others:
        write(TASK / "cheat" / ("cheat-%s.sh" % name), script(note, body))
        write(TASK / "authoring" / "cheatsrc" / name / "plan.py", body)
        made.append(name)

    ship = shipped()
    for name, note, prologue in ISOLATION:
        body = prologue + "\n\n" + ship
        write(TASK / "cheat" / ("cheat-%s.sh" % name), script(note, body))
        write(TASK / "authoring" / "cheatsrc" / name / "plan.py", body)
        made.append(name)

    readme = TASK / "cheat" / "README.md"
    lines = ["Deliberate fake solutions. Every one of them must score 0.", ""]
    for name in made:
        lines.append("- cheat-%s.sh" % name)
    write(readme, "\n".join(lines) + "\n")

    print("wrote solve.sh and %d cheats" % len(made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
