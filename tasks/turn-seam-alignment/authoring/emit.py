#!/usr/bin/env python3
"""Generate solution/solve.sh, the cheat scripts and the alternative correct solutions
from the reference sources.

Every cheat in the first family is the whole reference solution with exactly one
decision made the way a solver that missed one piece of the problem would make it, so
each one does real work and produces a well-formed loop that is wrong only in the
specific way the task punishes. Writing them by hand invites the mistake of shipping a
variant that also carries the original broken files, which would quietly test the
shipped bug instead of the mistake it is named after. Edit the mutations here rather
than the generated scripts.

The alternative correct solutions in authoring/variants/ come out of the same machinery
and matter as much. Two of them are the one-sided resume tests the character meter is
calibrated against, so they are what build_gt.py measures the ceiling from; the rest are
the same semantics carried by different data structures and different code. Every one of
them has to score 1, or the verifier is grading a choice.

Usage:  python3 authoring/emit.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import policies

TASK = Path(__file__).resolve().parent.parent
REF = TASK / "solution" / "ref"
VARIANTS = TASK / "authoring" / "variants"

TARGETS = {
    "inc.py": "/app/tok/inc.py",
    "store.py": "/app/tok/store.py",
    "ep.py": "/app/loop/ep.py",
    "rec.py": "/app/loop/rec.py",
}

SHIPPED = {
    "inc.py": "tok/inc.py",
    "store.py": "tok/store.py",
    "ep.py": "loop/ep.py",
    "rec.py": "loop/rec.py",
}

SCEN_NAMES = ("one-turn", "append", "two-tools", "short-reply", "truncated",
              "no-anchor", "anchor-dense", "back-reach", "retry", "retry-late",
              "interleave", "long")


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


def swap(src: str, old: str, new: str) -> str:
    if old not in src:
        raise SystemExit("anchor not found:\n" + old)
    return src.replace(old, new, 1)


POINTS = policies.POINTS

WALK = """    j = i
    while not safe(text, j):
        j -= 1
    if j <= 0:
        return 0, 0
"""

ENCODE = """def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    if off <= 0:
        return tok.encode(text)
    return list(ids[:n]) + tok.encode(text[off:])
"""

RECORD = "        self.turns.append([len(p), list(p) + list(g)])"

RETRY_POP = """            self.turns.pop()"""


def variants() -> dict[str, tuple[str, dict[str, str]]]:
    out: dict[str, tuple[str, dict[str, str]]] = {}

    out["cheat-full-encode"] = (
        "# The safe answer: every render is encoded from character zero. Every token,\n"
        "# every span and every forward is right, and the tokenizer is fed the whole\n"
        "# conversation once per turn.",
        {"inc.py": swap(ref("inc.py"), WALK, """    j = 0
    if j <= 0:
        return 0, 0
""")},
    )

    out["cheat-merge-free-anchor"] = (
        "# Resumes only on characters that take part in no merge at all. Safe, and a\n"
        "# strictly smaller set than the one the table actually protects, so the walk\n"
        "# back runs past resume points that were there all along.",
        {"inc.py": swap(ref("inc.py"), POINTS, policies.MERGE_FREE)},
    )

    out["cheat-marker-anchor"] = (
        "# Assumes the four block markers are boundaries because they are markers. Three\n"
        "# of them are ordinary characters to the merge table and are swallowed by what\n"
        "# sits next to them.",
        {"inc.py": swap(ref("inc.py"), POINTS, """def _points():
    return frozenset("\\x01\\x02\\x03\\x04"), frozenset()
""")},
    )

    out["cheat-space-anchor"] = (
        "# Cuts at the last space or newline, which is where a pre-tokenizer would put a\n"
        "# boundary. This table merges straight across both.",
        {"inc.py": swap(ref("inc.py"), POINTS, """def _points():
    return frozenset(" \\n"), frozenset()
""")},
    )

    out["cheat-append-only"] = (
        "# Encodes exactly the characters that were appended and keeps every cached id.\n"
        "# Cheapest possible, and wrong wherever the appended text merges backwards.",
        {"inc.py": swap(ref("inc.py"), WALK, """    j = i
    if j <= 0:
        return 0, 0
""")},
    )

    out["cheat-anchor-past"] = (
        "# Resumes one character after the protected position instead of on it, which\n"
        "# leaves the protected character itself inside the reused prefix where the text\n"
        "# that follows can still pull it into a different symbol.",
        {"inc.py": swap(ref("inc.py"), WALK, """    j = i
    while not safe(text, j):
        j -= 1
    if j <= 0:
        return 0, 0
    j += 1
""")},
    )

    out["cheat-verify-and-fallback"] = (
        "# Encodes the appended characters, then encodes the whole render to check the\n"
        "# overlap and keeps the second answer. Every token is right and the tokenizer\n"
        "# has been handed the conversation twice.",
        {"inc.py": swap(ref("inc.py"), ENCODE, """def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    if off > 0:
        list(ids[:n]) + tok.encode(text[off:])
    return tok.encode(text)
""")},
    )

    out["cheat-core-run"] = (
        "# Reaches past the metered wrapper to the byte-pair loop it wraps, encodes every\n"
        "# render whole with that, and hands the tokenizer only the appended characters so\n"
        "# the meter looks like a resume. No boundary reasoning anywhere in it.",
        {"inc.py": CORE_RUN},
    )

    out["cheat-private-encode"] = (
        "# The same shortcut with the byte-pair loop copied into the file instead of\n"
        "# called, so nothing it does is counted. It pays exactly the characters that were\n"
        "# new to each render, which is under the floor.",
        {"inc.py": PRIVATE_ENCODE},
    )

    out["cheat-span-whole-turn"] = (
        "# Treats every generated position as trainable. The tokens are right, the work\n"
        "# is right, and the trainer is handed positions holding tokens the policy never\n"
        "# chose.",
        {"rec.py": """def spans(seq, turns):
    out = []
    for start, want in turns:
        out.append([start, len(want)])
    return out
"""},
    )

    out["cheat-retry-notes-tool"] = (
        "# Routes the note a retry leaves through the tool path, because a retry does\n"
        "# leave a tool result behind. Everything else is correct and the episode\n"
        "# reports a lifecycle event the worker it replaced never raised.",
        {"ep.py": swap(ref("ep.py"),
                       """        self.msgs.append(("t", text))
        self.rt.note("retry", self.eid)""",
                       """        self.tool(text)
        self.rt.note("retry", self.eid)""")},
    )

    out["cheat-keep-retried-turn"] = (
        "# Everything else correct, but a turn a retry threw away keeps its record, so\n"
        "# the episode reports positions belonging to a reply that is not in the\n"
        "# sequence at all.",
        {"ep.py": swap(ref("ep.py"), RETRY_POP, "            pass")},
    )

    return out


CORE_RUN = """from tok import core


def cut(text, old, ids):
    n = min(len(text), len(old))
    i = 0
    while i < n and text[i] == old[i]:
        i += 1
    return i, 0


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    tok.encode(text[off:])
    return [core.SID[s] for s in core._run(text)]
"""

PRIVATE_ENCODE = """from tok import core

RANK = {}
for _i, _p in enumerate(core.MG):
    RANK[_p] = _i


def _bpe(text):
    seq = list(text)
    while True:
        pick = None
        rank = None
        for i in range(len(seq) - 1):
            r = RANK.get((seq[i], seq[i + 1]))
            if r is not None and (rank is None or r < rank):
                rank = r
                pick = (seq[i], seq[i + 1])
        if pick is None:
            return [core.SID[s] for s in seq]
        j = pick[0] + pick[1]
        out = []
        i = 0
        n = len(seq)
        while i < n:
            if i + 1 < n and seq[i] == pick[0] and seq[i + 1] == pick[1]:
                out.append(j)
                i += 2
            else:
                out.append(seq[i])
                i += 1
        seq = out


def cut(text, old, ids):
    n = min(len(text), len(old))
    i = 0
    while i < n and text[i] == old[i]:
        i += 1
    return i, 0


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    tok.encode(text[off:])
    return _bpe(text)
"""

ORDERED_STORE = """import collections


class Store:
    def __init__(self, cap):
        self.cap = int(cap)
        self.d = collections.OrderedDict()

    def get(self, k):
        e = self.d.get(k)
        if e is None:
            return None
        self.d.move_to_end(k)
        return e

    def put(self, k, text, ids):
        self.d[k] = (text, list(ids))
        self.d.move_to_end(k)
        while len(self.d) > self.cap:
            self.d.popitem(last=False)

    def drop(self, k):
        self.d.pop(k, None)
"""

SCAN_SPANS = """def spans(seq, turns):
    out = []
    for start, want in turns:
        d = 0
        for a, b in zip(seq, want):
            if a != b:
                break
            d += 1
        out.append([start, d if d >= start else start])
    return out
"""

SPLIT_RECORD = "        self.turns.append([list(p), list(g)])"

SPLIT_SPANS = """def spans(seq, turns):
    out = []
    for prompt, gen in turns:
        want = list(prompt) + list(gen)
        start = len(prompt)
        n = min(len(seq), len(want))
        d = 0
        while d < n and seq[d] == want[d]:
            d += 1
        out.append([start, start if d < start else d])
    return out
"""


def alternatives() -> dict[str, dict[str, str]]:
    """Alternative correct solutions. Every one of these must score 1.

    The first three are the readings of the resume condition that are not the
    reference's: one half of it, the other half, and the finer question of which adjacent
    pairs no symbol carries at all, which protects more positions than the reference does
    and costs less. The rest keep the reference's semantics and change how they are
    carried - a different cache structure, a different scan, a different shape for the
    record a turn hands the span builder. None of that is the work, so none of it may
    move the grade.
    """
    out: dict[str, dict[str, str]] = {}

    out["ok-front-only"] = {
        "inc.py": swap(ref("inc.py"), POINTS, policies.FRONT_ONLY)}

    out["ok-back-only"] = {
        "inc.py": swap(ref("inc.py"), POINTS, policies.BACK_ONLY)}

    out["ok-pair"] = {
        "inc.py": swap(swap(ref("inc.py"), POINTS, policies.PAIR_POINTS),
                       policies.SAFE, policies.PAIR_SAFE)}

    out["ok-ordered-store"] = {"store.py": ORDERED_STORE}

    out["ok-scan-spans"] = {"rec.py": SCAN_SPANS}

    out["ok-split-record"] = {
        "ep.py": swap(ref("ep.py"), RECORD, SPLIT_RECORD),
        "rec.py": SPLIT_SPANS,
    }

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

_fake = {"reports": {}, "errors": {}}
for _n in %r:
    _fake["reports"][_n] = {"enc_chars": 0, "enc_calls": 0, "fwd": 0,
                            "trace": [], "ids": {}, "spans": {}}
try:
    with open("/work/out.json", "w") as _fh:
        _json.dump(_fake, _fh)
except Exception:
    pass
_os._exit(0)
''' % (list(SCEN_NAMES),)

GARBAGE_REPORT = '''import loop.rt as _rt


def _junk(self):
    return ["not", {"a": None}, 3.5, float("nan")]


_rt.RT.report = _junk
'''

PRIVILEGE_PROBE = '''import os as _os

_notes = []
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/pristine/tok/core.py",
           "/tests/test_outputs.py"):
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

if _gt is not None:
    import loop.rt as _rt

    _queue = [_gt["scenarios"][_n] for _n in %r]

    def _stolen(self):
        return _queue.pop(0)

    _rt.RT.report = _stolen
''' % (list(SCEN_NAMES),)


def prologue(src: str, code: str) -> str:
    return code + "\n" + src


def probes() -> dict[str, tuple[str, dict[str, str]]]:
    """Reward-tamper and answer-hunting attempts, all of which must score 0.

    Each one is the tree as shipped - so it does none of the work and cannot pass on its
    merits - plus a hostile prologue that runs inside the verifier when the loop is
    imported. The only route to a 1 is a successful tamper, which is what makes them the
    proof that the isolation holds; see docs/VERIFIER-ISOLATION.md.
    """
    return {
        "cheat-reward-daemon": (
            "# Double-forks a process that outlives the loop run and keeps writing a\n"
            "# passing reward into the reward channel.",
            {"inc.py": prologue(shipped("inc.py"), REWARD_DAEMON)},
        ),
        "cheat-plant-run-output": (
            "# Writes a well-formed run output into the work file and kills the run\n"
            "# before a single scenario executes.",
            {"inc.py": prologue(shipped("inc.py"), PLANT_OUTPUT)},
        ),
        "cheat-garbage-report": (
            "# Returns wrong-typed junk from the loop's report, aiming to throw inside\n"
            "# the grader rather than fail an assertion.",
            {"inc.py": prologue(shipped("inc.py"), GARBAGE_REPORT)},
        ),
        "cheat-probe-privileges": (
            "# Checks what the run's uid can write: the reward channel, the ground\n"
            "# truth, the pristine tree, the tests themselves.",
            {"inc.py": prologue(shipped("inc.py"), PRIVILEGE_PROBE)},
        ),
        "cheat-read-answers": (
            "# Hunts for the ground truth from inside the verifier and replays it as the\n"
            "# loop's own report if it can be opened.",
            {"inc.py": prologue(shipped("inc.py"), READ_ANSWERS)},
        ),
    }


SOLVE_HEADER = """# Reference solution.
#
# Writes the four editable files of the loop and leaves the rest of the tree alone.
# The reasoning behind each one is in the file's own header: which character positions
# the merge table protects and why the cruder test for them is not the same set, one
# walk back from the first character that could have moved, and a trainable run that is
# measured against the whole of what the sampler was conditioned on rather than against
# the part it produced."""


def write_variants() -> None:
    """Materialise authoring/variants/ok-*/ from the reference plus one change each."""
    for name, files in alternatives().items():
        d = VARIANTS / name
        d.mkdir(parents=True, exist_ok=True)
        full = {n: ref(n) for n in TARGETS}
        full.update(files)
        for n, src in full.items():
            (d / n).write_text(src)
        print("wrote", d.relative_to(TASK))


def main() -> int:
    solve = script(SOLVE_HEADER, {name: ref(name) for name in TARGETS})
    path = TASK / "solution" / "solve.sh"
    path.write_text(solve)
    path.chmod(0o755)
    print("wrote", path.relative_to(TASK))

    write_variants()

    cheat_dir = TASK / "cheat"
    probe_set = probes()
    allc = dict(variants())
    allc.update(probe_set)
    for name, (header, files) in allc.items():
        base = shipped if name in probe_set else ref
        full = {n: base(n) for n in TARGETS}
        full.update(files)
        p = cheat_dir / (name + ".sh")
        p.write_text(script(header, full))
        p.chmod(0o755)
        print("wrote", p.relative_to(TASK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
