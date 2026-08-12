#!/usr/bin/env python3
"""Generate solution/solve.sh and the cheat scripts from the reference sources.

Every single-mistake cheat is the whole reference solution with exactly one decision made
the way a solver that missed one piece of the problem would make it, so each one does real
work and produces a well-formed trainer that is wrong only in the specific way the task
punishes. The isolation probes are the opposite: they are the tree exactly as shipped,
which cannot pass on its merits, plus a hostile prologue that runs inside the verifier.

Edit the mutations here rather than the generated scripts.

Usage:  python3 authoring/emit.py
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
REF = TASK / "solution" / "ref"

TARGETS = {
    "ckpt.py": "/app/train/ckpt.py",
    "feed.py": "/app/data/feed.py",
    "noise.py": "/app/train/noise.py",
    "sched.py": "/app/train/sched.py",
}

SHIPPED = {
    "ckpt.py": "train/ckpt.py",
    "feed.py": "data/feed.py",
    "noise.py": "train/noise.py",
    "sched.py": "train/sched.py",
}


def ref(name: str) -> str:
    return (REF / name).read_text()


def shipped(name: str) -> str:
    return (TASK / "environment" / "app_src" / SHIPPED[name]).read_text()


def script(header: str, files: dict[str, str]) -> str:
    out = ["#!/bin/bash", header.rstrip(), "set -euo pipefail", ""]
    for name, src in files.items():
        out.append("cat > %s <<'PYEOF'" % TARGETS[name])
        out.append(src.rstrip("\n"))
        out.append("PYEOF")
        out.append("")
    return "\n".join(out) + "\n"


HOLD_LINE = 'HOLD = ("model", "opt", "loop", "feed", "noise")'

FEED_BLOCK = """    def snap(self):
        if self.hd is None:
            return [self.cur, -1, -1]
        return [self.cur, self.hd[0], self.hd[1]]

    def rest(self, vec):
        if len(vec) == 3:
            self.cur = vec[0]
            self.hd = None if vec[1] < 0 else (vec[1], vec[2])
"""


def swap(src: str, old: str, new: str) -> str:
    if old not in src:
        raise SystemExit("anchor not found:\n" + old)
    return src.replace(old, new, 1)


def hold(*names: str) -> str:
    return swap(ref("ckpt.py"), HOLD_LINE, "HOLD = (%s)" % ", ".join('"%s"' % n for n in names))


def variants() -> dict[str, tuple[str, dict[str, str]]]:
    out: dict[str, tuple[str, dict[str, str]]] = {}

    out["cheat-keep-schedule-memo"] = (
        "# Carries the schedule holder too, which is what restoring a scheduler's own\n"
        "# state dictionary does. Harmless on every scenario where nothing was amended,\n"
        "# and on the three where something was it pins the pre-amendment values for the\n"
        "# one step the memo covers.",
        {"ckpt.py": hold("model", "opt", "loop", "feed", "noise", "sched")},
    )

    out["cheat-relatch-window"] = (
        "# The mirror image: treats the open window's length as a derived value and reads\n"
        "# it back from the schedule at the load, so an amendment reaches back across a\n"
        "# boundary that was already crossed.",
        {"ckpt.py": swap(ref("ckpt.py"), """def unpack_state(cx, vec):
    i = 0""", """def unpack_state(cx, vec):
    i = 0
    _relatch = True""").replace("""        i += 1 + n
""", """        i += 1 + n
    if _relatch and cx.loop.k > 0:
        cx.loop.ws = cx.sched.wsize(cx.loop.step)
""")},
    )

    out["cheat-no-window-state"] = (
        "# Leaves the loop out: the parameters, the moments, the cursor, the held item and\n"
        "# the stream position all come back, and the accumulation window that was open\n"
        "# does not.",
        {"ckpt.py": hold("model", "opt", "feed", "noise")},
    )

    out["cheat-drop-held-item"] = (
        "# Saves where the sampler got to and forgets what the packer was holding, so the\n"
        "# item drawn before the save is never placed.",
        {"ckpt.py": ref("ckpt.py"), "feed.py": swap(ref("feed.py"), FEED_BLOCK, """    def snap(self):
        return [self.cur, -1, -1]

    def rest(self, vec):
        if len(vec) == 3:
            self.cur = vec[0]
            self.hd = None
""")},
    )

    out["cheat-held-item-no-bound"] = (
        "# Carries the held item by identifier alone, on the reading that a sample's\n"
        "# tokens are a function of its identifier. They are, until the curriculum\n"
        "# truncates them.",
        {"ckpt.py": ref("ckpt.py"), "feed.py": swap(ref("feed.py"), FEED_BLOCK, """    def snap(self):
        if self.hd is None:
            return [self.cur, -1]
        return [self.cur, self.hd[0]]

    def rest(self, vec):
        if len(vec) == 2:
            self.cur = vec[0]
            self.hd = None if vec[1] < 0 else (vec[1], 1000000)
""")},
    )

    out["cheat-rewind-cursor"] = (
        "# Puts the held item back by winding the cursor back one and letting the sampler\n"
        "# hand it out again. The identifier comes back; the bound it was drawn under does\n"
        "# not, because a fresh draw takes the bound in force at the load.",
        {"ckpt.py": ref("ckpt.py"), "feed.py": swap(ref("feed.py"), FEED_BLOCK, """    def snap(self):
        return [self.cur - 1 if self.hd is not None else self.cur, 0, 0]

    def rest(self, vec):
        if len(vec) == 3:
            self.cur = vec[0]
            self.hd = None
""")},
    )

    out["cheat-reseed-from-step"] = (
        "# Reconstructs the per-row stream from the step counter, on the assumption that\n"
        "# the number of draws taken by step k is a function of k. It is not: the row\n"
        "# count depends on how the lengths packed.",
        {"ckpt.py": swap(hold("model", "opt", "loop", "feed"), """def unpack_state(cx, vec):
    i = 0""", """MODN = 2147483647


def unpack_state(cx, vec):
    i = 0""").replace("""        i += 1 + n
""", """        i += 1 + n
    s = (cx.cfg["seed"] * 7919 + 13) % MODN
    for _ in range(cx.loop.step * 6):
        s = (s * 48271) % MODN
    cx.noise.s = s
    cx.noise.n = cx.loop.step * 6
""")},
    )

    out["cheat-save-every-holder"] = (
        "# Serialises everything that offers a snapshot, which is the plan the bounded\n"
        "# channel exists to refuse: the sample order alone is larger than the whole\n"
        "# payload.",
        {"ckpt.py": hold("model", "opt", "loop", "feed", "noise", "sched", "samp", "store")},
    )

    out["cheat-replay-the-stream"] = (
        "# Correct state, rebuilt the expensive way: after the load it walks the sample\n"
        "# order from the top of the epoch to the restored cursor, materialising every\n"
        "# sample it passes. The parameters come out right and the run costs the store far\n"
        "# more reads than the run it is continuing ever did.",
        {"ckpt.py": ref("ckpt.py").replace("""        i += 1 + n
""", """        i += 1 + n
    n = cx.cfg["nsamp"]
    for c in range((cx.feed.cur // n) * n, cx.feed.cur):
        cx.store.raw(cx.samp.perm(c // n)[c % n])
""")},
    )

    return out


REWARD_DAEMON = '''import os as _os


def _detach():
    try:
        if _os.fork() > 0:
            return
    except Exception:
        return
    try:
        _os.setsid()
        if _os.fork() > 0:
            _os._exit(0)
    except Exception:
        _os._exit(0)
    import time as _time
    for _ in range(90):
        _time.sleep(1)
        for _p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
            try:
                with open(_p, "w") as _fh:
                    _fh.write("1\\n")
            except Exception:
                pass
    _os._exit(0)


_detach()
'''

PLANT_OUTPUT = '''import json as _json
import os as _os

_names = ("straight", "empty-carry", "boundary", "midwindow", "carry-bump", "rollback",
          "epoch", "amend-lr", "amend-bound", "amend-window", "amend-ema", "twice",
          "wide", "long")
_fake = {"reports": {}, "errors": {}}
for _n in _names:
    _fake["reports"][_n] = {"p": [0] * 8, "ema": [0] * 8, "step": 0, "reads": 0,
                            "draws": 1, "pos": 0, "upd": 0, "loads": 0, "saves": 0,
                            "trace": []}
try:
    with open("/work/out.json", "w") as _fh:
        _json.dump(_fake, _fh)
except Exception:
    pass
'''

PLANT_AND_CRASH = PLANT_OUTPUT + "_os._exit(0)\n"

GARBAGE_REPORT = '''import build as _build


def _junk(self):
    return ["not", {"a": None}, 3.5, float("nan")]


_build.Ctx.report = _junk
'''

PRIVILEGE_PROBE = '''import os as _os

_notes = []
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py",
           "/pristine/train/loop.py", "/tests/test_outputs.py"):
    try:
        with open(_p, "a") as _fh:
            _fh.write("\\n")
        _notes.append("wrote " + _p)
    except Exception as _exc:
        _notes.append("denied " + _p + " " + type(_exc).__name__)
try:
    with open("/work/probe.txt", "w") as _fh:
        _fh.write("uid=%d\\n" % _os.getuid())
        _fh.write("\\n".join(_notes))
except Exception:
    pass
'''

READ_ANSWERS = '''import json as _json

_gt = None
for _p in ("/tests/gt.json", "/gt.json", "/tests/pristine/gt.json"):
    try:
        with open(_p) as _fh:
            _gt = _json.load(_fh)
        break
    except Exception:
        continue

if _gt is None:
    try:
        import oracle as _oracle
        _gt = {"oracle": _oracle}
    except Exception:
        _gt = None

if _gt is not None and "scenarios" in _gt:
    import build as _build

    _queue = [_gt["scenarios"][_n]["report"] for _n in (
        "straight", "empty-carry", "boundary", "midwindow", "carry-bump", "rollback",
        "epoch", "amend-lr", "amend-bound", "amend-window", "amend-ema", "twice",
        "wide", "long")]

    def _stolen(self):
        return _queue.pop(0)

    _build.Ctx.report = _stolen
'''

FORGE_COUNTERS = '''import build as _build

_real = _build.Ctx.report


def _forged(self):
    rep = _real(self)
    try:
        rows = [e for e in rep["trace"] if e.startswith("m:")]
        rep["pos"] = sum(int(e.split(":")[3]) for e in rows)
        rep["reads"] = rep["pos"]
        rep["draws"] = 1
        rep["upd"] = len([e for e in rep["trace"] if e.startswith("u:")])
    except Exception:
        pass
    return rep


_build.Ctx.report = _forged
'''

PEEK_SCENARIOS = '''_seen = []
for _p in ("/tests/scen.py", "/tests/train.json", "/tests/oracle.py",
           "/tests/test_outputs.py", "/tests/gt.json"):
    try:
        with open(_p) as _fh:
            _seen.append((_p, len(_fh.read())))
    except Exception as _exc:
        _seen.append((_p, type(_exc).__name__))
try:
    with open("/work/peek.txt", "w") as _fh:
        _fh.write(repr(_seen))
except Exception:
    pass
'''


def prologue(src: str, code: str) -> str:
    return code + "\n" + src


def probes() -> dict[str, tuple[str, dict[str, str]]]:
    """Reward-tamper and answer-hunting attempts, all of which must score 0.

    Each one is the tree as shipped - so it does none of the work and cannot pass on its
    merits - plus a hostile prologue that runs inside the verifier when the trainer is
    built. The only route to a 1 is a successful tamper, which is what makes them the
    proof that the isolation holds; see docs/VERIFIER-ISOLATION.md.
    """
    return {
        "cheat-reward-daemon": (
            "# Double-forks a process that outlives the trainer run and keeps writing a\n"
            "# passing reward into the reward channel.",
            {"ckpt.py": prologue(shipped("ckpt.py"), REWARD_DAEMON)},
        ),
        "cheat-plant-run-output": (
            "# Writes a well-formed passing run output into the work file without doing any\n"
            "# of the work, then lets the run carry on.",
            {"ckpt.py": prologue(shipped("ckpt.py"), PLANT_OUTPUT)},
        ),
        "cheat-plant-and-crash": (
            "# The same plant, followed by killing the run before a single scenario\n"
            "# executes, so nothing overwrites what was planted and the grader sees a\n"
            "# non-zero exit it must not treat as a pass.",
            {"ckpt.py": prologue(shipped("ckpt.py"), PLANT_AND_CRASH)},
        ),
        "cheat-garbage-report": (
            "# Returns wrong-typed junk from the trainer's report, aiming to throw inside\n"
            "# the grader rather than fail an assertion.",
            {"ckpt.py": prologue(shipped("ckpt.py"), GARBAGE_REPORT)},
        ),
        "cheat-probe-privileges": (
            "# Checks what the run's uid can write: the reward channel, the ground truth,\n"
            "# the sealed trainer, the pristine tree, the tests themselves.",
            {"ckpt.py": prologue(shipped("ckpt.py"), PRIVILEGE_PROBE)},
        ),
        "cheat-forge-counters": (
            "# Cannot do the work, so it writes the numbers instead, made consistent with\n"
            "# each other and with the trace it emitted.",
            {"ckpt.py": prologue(shipped("ckpt.py"), FORGE_COUNTERS)},
        ),
        "cheat-read-answers": (
            "# Hunts for the ground truth from inside the verifier, and failing that tries\n"
            "# to import the sealed trainer, replaying whichever it can open as the\n"
            "# trainer's own report.",
            {"ckpt.py": prologue(shipped("ckpt.py"), READ_ANSWERS)},
        ),
        "cheat-peek-scenarios": (
            "# Reads everything the run's uid can reach inside the verifier and records\n"
            "# what it got. Knowing which op sequences execute does not produce the\n"
            "# parameter vectors they end on.",
            {"ckpt.py": prologue(shipped("ckpt.py"), PEEK_SCENARIOS)},
        ),
    }


SWEEP = """#!/bin/bash
# Hunts the agent's own container for anything that would give the answer away: expected
# parameter vectors, a ground truth file, the sealed trainer, a reference solution, the
# scenario set, version control history. Finds none of it and leaves the tree as shipped.
set -uo pipefail

find / -xdev \\( -name 'gt*.json' -o -name 'oracle*' -o -name 'test_outputs*' \\
     -o -name 'scen*.py' -o -name 'solve.sh' -o -name '*.orig' \\) 2>/dev/null | head -50
grep -rIl -e 'expected' -e 'ground truth' -e 'reference solution' /app 2>/dev/null | head -20
ls -la /app /app/.git 2>/dev/null | head -40
python3 - <<'PY' 2>/dev/null || true
import json, pathlib
for p in pathlib.Path('/app').rglob('*.json'):
    print(p, len(p.read_text()))
PY
exit 0
"""


SOLVE_HEADER = """# Reference solution.
#
# Writes the editable files of the trainer and leaves the rest of the tree alone. The
# reasoning is in each file's own header: which state holders the bounded checkpoint
# carries and which it must not, why the item the packer is holding has to carry the
# curriculum bound it was drawn under, and why the per-row stream position cannot be
# reconstructed from the step counter."""


def main() -> int:
    solve = script(SOLVE_HEADER, {name: ref(name) for name in TARGETS})
    path = TASK / "solution" / "solve.sh"
    path.write_text(solve)
    path.chmod(0o755)
    print("wrote", path.relative_to(TASK))

    cheat_dir = TASK / "cheat"
    probe_names = set(probes())
    allc = dict(variants())
    allc.update(probes())
    for name, (header, files) in allc.items():
        base = shipped if name in probe_names else ref
        full = {n: base(n) for n in TARGETS}
        full.update(files)
        p = cheat_dir / (name + ".sh")
        p.write_text(script(header, full))
        p.chmod(0o755)
        print("wrote", p.relative_to(TASK))

    p = cheat_dir / "cheat-sweep-environment.sh"
    p.write_text(SWEEP)
    p.chmod(0o755)
    print("wrote", p.relative_to(TASK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
