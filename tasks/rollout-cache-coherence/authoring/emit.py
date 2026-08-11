#!/usr/bin/env python3
"""Generate solution/solve.sh and the cheat scripts from the reference sources.

Every cheat is the whole reference solution with exactly one decision made the way a
solver that missed one piece of the problem would make it, so each cheat does real work and
produces a well-formed engine that is wrong only in the specific way the task punishes.
Edit the mutations here rather than the generated scripts.

Usage:  python3 authoring/emit.py
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
REF = TASK / "solution" / "ref"

TARGETS = {
    "pstore.py": "/app/model/pstore.py",
    "pfx.py": "/app/runtime/pfx.py",
    "sch.py": "/app/runtime/sch.py",
    "pool.py": "/app/mem/pool.py",
}


SHIPPED = {
    "pstore.py": "model/pstore.py",
    "pfx.py": "runtime/pfx.py",
    "sch.py": "runtime/sch.py",
    "pool.py": "mem/pool.py",
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


KEY_BLOCK = """    def key(self, adapter):
        return self._fp(adapter, KV_REL, "kv")

    def gen(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")
"""

SYNC_HEAD = "    def on_sync(self, ps):"

USABLE_BLOCK = """    def usable(self, pid):
        return pid in self.pg and pid not in self.dead
"""

WAKE_BLOCK = """    def wake(self):
        if self.lvl == 1 and self.off:
            for p, d in self.off.items():
                self.pg[p] = d
            self.off = {}
        else:
            for p in list(self.pg):
                self.pg[p] = junk(self.bs)
                if p not in self.free:
                    self.dead.add(p)
        self.lvl = 0
"""


def swap(src: str, old: str, new: str) -> str:
    if old not in src:
        raise SystemExit("anchor not found:\n" + old)
    return src.replace(old, new, 1)


def sync_from(body: str) -> str:
    src = ref("sch.py")
    head = src.index(SYNC_HEAD)
    return src[:head] + body


def variants() -> dict[str, tuple[str, dict[str, str]]]:
    out: dict[str, tuple[str, dict[str, str]]] = {}

    out["cheat-reset-cache-on-sync"] = (
        "# The idiomatic answer: every parameter push drops the whole prefix cache and\n"
        "# rewinds everything in flight. Correct tokens, but it throws away blocks whose\n"
        "# contents cannot have changed.",
        {"pstore.py": swap(ref("pstore.py"), KEY_BLOCK, """    def key(self, adapter):
        return tag("rev/" + str(self.rev) + "/" + str(adapter))

    def gen(self, adapter):
        return tag("rev/" + str(self.rev) + "/" + str(adapter))
""")},
    )

    out["cheat-adapter-in-key"] = (
        "# Puts the adapter's identity into the block key, the fix a reader of the public\n"
        "# cross-adapter cache-hit reports would transplant. Two adapters that cannot move\n"
        "# any key or value stop sharing a prompt they should share.",
        {"pstore.py": swap(ref("pstore.py"), KEY_BLOCK, """    def key(self, adapter):
        return tag("ad/" + str(adapter) + "/" + str(self._fp(adapter, KV_REL, "kv")))

    def gen(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")
""")},
    )

    out["cheat-whole-model-fingerprint"] = (
        "# One fingerprint for both questions: the full parameter set decides block\n"
        "# validity as well as rewinds. Nothing stale is ever served, and every push that\n"
        "# only moves the output side needlessly discards the cache.",
        {"pstore.py": swap(ref("pstore.py"), KEY_BLOCK, """    def key(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")

    def gen(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")
""")},
    )

    out["cheat-revision-counter"] = (
        "# Content fingerprint for rewinds, revision counter for the cache. A push that\n"
        "# lands values identical to the ones already loaded still empties the cache.",
        {"pstore.py": swap(ref("pstore.py"), KEY_BLOCK, """    def key(self, adapter):
        return tag("kvrev/" + str(self.rev) + "/" + str(adapter))

    def gen(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")
""")},
    )

    out["cheat-target-names"] = (
        "# Decides validity from the names in the push rather than from the values that\n"
        "# came out of it, so the module that shares storage with an earlier layer reads\n"
        "# as harmless and its blocks are kept.",
        {"pstore.py": swap(ref("pstore.py"), KEY_BLOCK, """    def key(self, adapter):
        return tag("dirty/" + str(self.dirty) + "/" + str(adapter))

    def gen(self, adapter):
        return self._fp(adapter, ALL_PIDS, "gen")
""").replace("""        self.wcache = {}
        self.fcache = {}
        self.rev = 0
""", """        self.wcache = {}
        self.fcache = {}
        self.rev = 0
        self.dirty = 0
""").replace("""        self.wcache = {}
        self.fcache = {}
        self.rev += 1
""", """        for u in ups:
            if u[1] in KV_REL:
                self.dirty += 1
        self.wcache = {}
        self.fcache = {}
        self.rev += 1
""")},
    )

    out["cheat-no-rewind"] = (
        "# Gets block validity right and leaves samples in flight alone, so a sample can\n"
        "# straddle two policies.",
        {"pstore.py": ref("pstore.py"), "sch.py": sync_from("""    def on_sync(self, ps):
        self.n_sync += 1
        for s in list(self.run) + list(self.wait):
            s.sync_n = self.n_sync
""")},
    )

    out["cheat-rewind-on-kv-only"] = (
        "# Rewinds a sample only when the push could have moved a key or value, so a push\n"
        "# that only moves the output side leaves half-old samples running.",
        {"pstore.py": ref("pstore.py"), "sch.py": sync_from("""    def on_sync(self, ps):
        self.n_sync += 1
        for s in list(self.run) + list(self.wait):
            s.sync_n = self.n_sync
            if s.done or not s.gen:
                continue
            now = ps.key(s.adapter)
            if s.fp is None or now == s.fp:
                continue
            self.eng.note("restart", s.rid)
            self.eng.release(s)
            s.gen = []
            s.step = 0
            s.fp = None
            s.gfp = None
            self.requeue(s)
""")},
    )

    out["cheat-keep-discarded-pages"] = (
        "# Everything else correct, but the pool keeps claiming that pages whose contents\n"
        "# were dropped are usable.",
        {"pstore.py": ref("pstore.py"), "sch.py": ref("sch.py"),
         "pool.py": swap(swap(ref("pool.py"), USABLE_BLOCK, """    def usable(self, pid):
        return pid in self.pg
"""), WAKE_BLOCK, """    def wake(self):
        if self.lvl == 1 and self.off:
            for p, d in self.off.items():
                self.pg[p] = d
            self.off = {}
        else:
            for p in list(self.pg):
                self.pg[p] = junk(self.bs)
        self.lvl = 0
""")},
    )

    out["cheat-drop-cache-on-sleep"] = (
        "# Treats both offload levels as destructive, so a cycle that copied every page\n"
        "# out and back still costs a full recompute.",
        {"pstore.py": ref("pstore.py"), "sch.py": ref("sch.py"),
         "pool.py": swap(ref("pool.py"), WAKE_BLOCK, """    def wake(self):
        if self.lvl == 1 and self.off:
            for p, d in self.off.items():
                self.pg[p] = d
            self.off = {}
        else:
            for p in list(self.pg):
                self.pg[p] = junk(self.bs)
        for p in list(self.pg):
            if p not in self.free:
                self.dead.add(p)
        self.lvl = 0
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

_fake = {"reports": {}, "errors": {}}
for _n in ("group", "neutral-base", "relevant-base", "tied-push", "adapter-share",
           "adapter-push", "adapter-neutral-push", "replayed-push", "offload-cycle",
           "pressure", "mixed"):
    _fake["reports"][_n] = {"computed": 0, "reused": 0, "restart": 0, "preempt": 0,
                            "evict": 0, "pos": 0, "trace": [], "out": {}}
try:
    with open("/work/out.json", "w") as _fh:
        _json.dump(_fake, _fh)
except Exception:
    pass
_os._exit(0)
'''

GARBAGE_REPORT = '''import runtime.eng as _eng


def _junk(self):
    return ["not", {"a": None}, 3.5, float("nan")]


_eng.Eng.report = _junk
'''

PRIVILEGE_PROBE = '''import os as _os

_notes = []
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/pristine/model/be.py",
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
    import runtime.eng as _eng

    _queue = [_gt["scenarios"][_n]["report"] for _n in (
        "group", "neutral-base", "relevant-base", "tied-push", "adapter-share",
        "adapter-push", "adapter-neutral-push", "replayed-push", "offload-cycle",
        "pressure", "mixed")]

    def _stolen(self):
        return _queue.pop(0)

    _eng.Eng.report = _stolen
'''


def prologue(src: str, code: str) -> str:
    head, _, tail = src.partition('"""\n')
    body = head + '"""\n' if tail else ""
    rest = tail if tail else src
    return body + "\n" + code + "\n" + rest


def probes() -> dict[str, tuple[str, dict[str, str]]]:
    """Reward-tamper and answer-hunting attempts, all of which must score 0.

    Each one is the tree as shipped - so it does none of the work and cannot pass on its
    merits - plus a hostile prologue that runs inside the verifier when the engine is
    imported. The only route to a 1 is a successful tamper, which is what makes them the
    proof that the isolation holds; see docs/VERIFIER-ISOLATION.md.
    """
    return {
        "cheat-reward-daemon": (
            "# Double-forks a process that outlives the engine run and keeps writing a\n"
            "# passing reward into the reward channel.",
            {"pstore.py": prologue(shipped("pstore.py"), REWARD_DAEMON)},
        ),
        "cheat-plant-run-output": (
            "# Writes a well-formed run output into the work file and kills the run before\n"
            "# a single scenario executes.",
            {"pstore.py": prologue(shipped("pstore.py"), PLANT_OUTPUT)},
        ),
        "cheat-garbage-report": (
            "# Returns wrong-typed junk from the engine's report, aiming to throw inside\n"
            "# the grader rather than fail an assertion.",
            {"pstore.py": prologue(shipped("pstore.py"), GARBAGE_REPORT)},
        ),
        "cheat-probe-privileges": (
            "# Checks what the run's uid can write: the reward channel, the ground truth,\n"
            "# the pristine tree, the tests themselves.",
            {"pstore.py": prologue(shipped("pstore.py"), PRIVILEGE_PROBE)},
        ),
        "cheat-read-answers": (
            "# Hunts for the ground truth from inside the verifier and replays it as the\n"
            "# engine's own report if it can be opened.",
            {"pstore.py": prologue(shipped("pstore.py"), READ_ANSWERS)},
        ),
    }


SOLVE_HEADER = """# Reference solution.
#
# Writes the four editable files of the engine and leaves the rest of the tree alone.
# The reasoning behind each one is in the file's own header: two fingerprints rather
# than one (what the cached key/value projections depend on, versus what the sampler
# can see), both taken over parameter values rather than over a revision number, and a
# pool that remembers which pages actually lost their contents."""


def main() -> int:
    solve = script(SOLVE_HEADER, {name: ref(name) for name in TARGETS})
    path = TASK / "solution" / "solve.sh"
    path.write_text(solve)
    path.chmod(0o755)
    print("wrote", path.relative_to(TASK))

    cheat_dir = TASK / "cheat"
    allc = dict(variants())
    allc.update(probes())
    for name, (header, files) in allc.items():
        base = shipped if name in probes() else ref
        full = {n: base(n) for n in TARGETS}
        full.update(files)
        p = cheat_dir / (name + ".sh")
        p.write_text(script(header, full))
        p.chmod(0o755)
        print("wrote", p.relative_to(TASK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
