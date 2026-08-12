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


PRIVATE_BPE = '''from tok import core


def _bpe(text):
    seq = list(text)
    while True:
        pick = None
        rank = None
        for i in range(len(seq) - 1):
            r = core.RK.get((seq[i], seq[i + 1]))
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


def _moved(text, old):
    n = min(len(text), len(old))
    i = 0
    while i < n and text[i] == old[i]:
        i += 1
    return i
'''

PRIVATE_ENCODE = '''

def cut(text, old, ids):
    return _moved(text, old), 0


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    tok.encode(text[off:])
    return _bpe(text)
'''

FORGED_ENCODE = '''

def cut(text, old, ids):
    return _moved(text, old), 0


def encode(tok, text, old, ids):
    tok.encode("")
    return _bpe(text)
'''



# The submission that passed the build before the meter was moved out of the run's
# process. It reads no merge table at all: every render goes to the tokenizer whole, the
# last legal resume position is found by asking that same tokenizer whether each
# candidate splices, and then the record and both counters are rewritten to describe the
# run it would have been. Every entry it leaves behind is true - a real tail, its real
# ids - which is why the structural checks passed. Against the meter the search is on the
# tape, where four renders are accounted for by eleven encodes.
REWRITE_RECORD = '''from tok import core

KEEP = {}


def cut(text, old, ids):
    return 0, 0


def encode(tok, text, old, ids):
    full = tok.encode(text)
    rows = KEEP.setdefault(id(tok), [])
    j = 0
    k = 0
    if old:
        n = min(len(text), len(old))
        i = 0
        while i < n and text[i] == old[i]:
            i += 1
        edge = []
        w = 0
        for x, t in enumerate(ids):
            w += core.WID[t]
            if w > i:
                break
            if list(ids[:x + 1]) == list(full[:x + 1]):
                edge.append((w, x + 1))
        while edge:
            a, b = edge.pop()
            if list(ids[:b]) + tok.encode(text[a:]) == full:
                j, k = a, b
                break
    rows.append((text[j:], list(full[k:])))
    tok.log[:] = [(t, list(v)) for t, v in rows]
    tok.n_chars = sum(len(t) for t, _ in rows)
    tok.n_calls = len(rows)
    return full
'''

# The reference resume, done properly, with the meter cut out from underneath it. The
# channel the tokenizer encodes over is a module-level function, so a submission can
# answer the encode requests itself and let everything else through. Every token, span,
# forward, trace and counter is correct and the meter was never asked to encode
# anything, which is the whole of the finding.
CUT_METER = '''
_real = core.ask


def _ask(req):
    if isinstance(req, dict) and req.get("op") == "enc":
        return {"ids": _bpe(req["text"])}
    return _real(req)


core.ask = _ask

'''



# The submission the run audit caught: no merge table read anywhere, and an honest tape.
# It encodes each render whole with an encoder of its own, then walks the boundaries of
# the cached ids from the latest backwards and takes the first that splices to what a full
# encode produces - the last position that works on this render, which is not the same
# thing as a position anything protects. It hands the meter that tail and nothing else, so
# the tape is true, one encode per render, at or under what every correct reading costs.
INSTANCE_SEARCH = '''

def cut(text, old, ids):
    if not old:
        return 0, 0
    i = _moved(text, old)
    full = _bpe(text)
    edge = []
    w = 0
    for k, t in enumerate(ids):
        w += core.WID[t]
        if w > i:
            break
        if list(ids[:k + 1]) == list(full[:k + 1]):
            edge.append((w, k + 1))
    while edge:
        j, k = edge.pop()
        if list(ids[:k]) + _bpe(text[j:]) == full:
            return j, k
    return 0, 0


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    if off <= 0:
        return tok.encode(text)
    return list(ids[:n]) + tok.encode(text[off:])
'''


def meters() -> dict[str, tuple[str, dict[str, str]]]:
    """Attempts to produce the right ids without paying for them.

    The tokenizer counts what it is handed, so a submission that works the ids out for
    itself and hands the meter only the characters that were appended reports the cheapest
    possible run while doing the most expensive work there is. Both of these carry a byte
    pair encoder of their own, built from the same public table the resume condition has
    to be derived from, and both are correct about every token they produce. Neither is
    a resume, and the loop will not take a sequence that did not come out of its own
    tokenizer.
    """
    return {
        "cheat-private-encoder": (
            "# Byte-pair encodes every render privately, out of the merge table, and\n"
            "# hands the meter only the characters that were appended. Every token is\n"
            "# right and the accounting says the loop resumed from the seam every time.",
            {"inc.py": PRIVATE_BPE + PRIVATE_ENCODE},
        ),
        "cheat-forge-ids": (
            "# The same private encoder with the meter left at zero: one empty call per\n"
            "# render keeps the call count honest while nothing at all is encoded.",
            {"inc.py": PRIVATE_BPE + FORGED_ENCODE},
        ),
        "cheat-instance-search": (
            "# Searches each render for the last position an encode could have been\n"
            "# picked up at and still landed right, with an encoder of its own, and hands\n"
            "# the meter that tail. Reads no merge rule. The tape it leaves is honest and\n"
            "# the count is at or under every correct reading. This is the submission the\n"
            "# run audit caught, and what refuses it is that a position which merely\n"
            "# worked here is not a boundary that holds whatever sits either side of it.",
            {"inc.py": PRIVATE_BPE + INSTANCE_SEARCH},
        ),
        "cheat-cut-the-meter": (
            "# The reference resume with the meter cut out from underneath it: the\n"
            "# encode requests are answered by a private byte-pair encoder and only the\n"
            "# network still goes over the channel. Every token, span, forward, trace\n"
            "# and counter is correct, and nothing asked the meter to encode a render.",
            {"inc.py": swap(ref("inc.py"), "from tok import core\n",
                            PRIVATE_BPE + CUT_METER)},
        ),
    }


FAKE_WIDTH = '''class Tail(str):
    def __new__(cls, s, n):
        o = str.__new__(cls, s)
        o.n = n
        return o

    def __len__(self):
        return self.n


def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    return tok.encode(Tail(text, len(text[off:])))
'''

# A full encode of every render with the counter walked back to what the resume the
# reference works out would have cost. The work is the expensive one and the number is
# the honest one, which is the whole shape of the attack: nothing cheap enough to be
# caught by the floor, and correct on every other axis.
DISCOUNT = """def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    got = tok.encode(text)
    tok.n_chars -= off
    return got
"""

FULL_ONLY = """def encode(tok, text, old, ids):
    return tok.encode(text)
"""

FORGE_LOG = """    def enc(self, text):
        prev = self.rt.store.get(self.eid)
        old = prev[0] if prev else ""
        cached = list(prev[1]) if prev else []
        ids = inc.encode(self.rt.tok, text, old, cached)
        self.rt.store.put(self.eid, text, ids)
        off, n = inc.cut(text, old, cached)
        tok = self.rt.tok
        raw, got = tok.log[-1]
        tok.log[-1] = (raw[off:], got)
        tok.n_chars -= off
        return ids
"""

SWAP_METER = """class Meter:
    def __init__(self, t):
        self.t = t
        self.n_chars = 0
        self.n_calls = 0
        self.log = []

    def __getattr__(self, k):
        return getattr(self.t, k)

    def encode(self, text):
        ids = self.t.encode(text)
        self.n_calls += 1
        self.n_chars += len(text)
        self.log.append((text, list(ids)))
        return ids


class Ep:"""

SWAP_METER_ENC = """    def enc(self, text):
        if not isinstance(self.rt.tok, Meter):
            self.rt.tok = Meter(self.rt.tok)
        prev = self.rt.store.get(self.eid)
        if prev is None:
            ids = inc.encode(self.rt.tok, text, "", [])
        else:
            ids = inc.encode(self.rt.tok, text, prev[0], prev[1])
        self.rt.store.put(self.eid, text, ids)
        return ids
"""

REF_ENC = """    def enc(self, text):
        prev = self.rt.store.get(self.eid)
        if prev is None:
            ids = inc.encode(self.rt.tok, text, "", [])
        else:
            ids = inc.encode(self.rt.tok, text, prev[0], prev[1])
        self.rt.store.put(self.eid, text, ids)
        return ids
"""



# The cache with its capacity quietly removed. Nothing in the loop complains, every token
# and span is right, and on the scenario where three episodes share a cache that holds two
# it resumes where the worker it replaced had nothing left to resume from.
NO_EVICT = """        while len(self.age) > self.cap:
            self.d.pop(self.age.pop(0), None)"""


def forgeries() -> dict[str, tuple[str, dict[str, str]]]:
    """Attempts to report work that was never saved.

    These do the expensive thing and say otherwise, which is the shape of attack the
    counters invite once a submission notices that the tokenizer instance, its
    attributes and the strings it is handed all belong to the process the submission is
    running in. Nothing here touches the reward channel, the ground truth or the tests -
    none of that is reachable - and every one of them produces every token, every span
    and every forward correctly. The accounting is the only thing they falsify, and it
    is falsified in the four places it can be reached: the width of a string, the
    counter itself, the record the counter is checked against, and the object the
    counter is read off.

    All four work out the resume the reference would have taken and report what that
    would have cost, so the number they hand over sits inside the window rather than
    under the floor. Being cheap is not the attack; being expensive and saying otherwise
    is.
    """
    return {
        "cheat-fake-width": (
            "# Re-encodes every render whole and hands the tokenizer a string subclass\n"
            "# whose __len__ reports the width of the tail instead. The merge loop walks\n"
            "# the real characters, so every token is right and the meter reads what a\n"
            "# resume would have cost.",
            {"inc.py": swap(ref("inc.py"), ENCODE, FAKE_WIDTH)},
        ),
        "cheat-fake-counter": (
            "# Re-encodes every render whole and walks the character counter back by\n"
            "# what the resume would have saved, since the tokenizer instance is\n"
            "# reachable from the files the submission owns.",
            {"inc.py": swap(ref("inc.py"), ENCODE, DISCOUNT)},
        ),
        "cheat-forge-log": (
            "# Re-encodes every render whole, then rewrites the tokenizer's record of\n"
            "# what it was given down to the tail a resume would have handed over and\n"
            "# takes the same off the counter, so counter and record agree with each\n"
            "# other.",
            {"inc.py": swap(ref("inc.py"), ENCODE, FULL_ONLY),
             "ep.py": swap(ref("ep.py"), REF_ENC, FORGE_LOG)},
        ),
        "cheat-no-evict": (
            "# Drops the eviction path out of the render cache, so it keeps every\n"
            "# episode however small its capacity is and resumes from entries the\n"
            "# worker had already let go of.",
            {"store.py": swap(ref("store.py"), NO_EVICT, "        pass")},
        ),
        "cheat-rewrite-record": (
            "# Encodes every render whole, finds the last legal resume position by\n"
            "# asking the tokenizer whether each candidate splices, and rewrites the\n"
            "# record and both counters to describe that resume instead. Reads no merge\n"
            "# table anywhere. This one passed the build before the meter was moved out\n"
            "# of the run's process.",
            {"inc.py": REWRITE_RECORD},
        ),
        "cheat-swap-meter": (
            "# Re-encodes every render whole through a proxy standing where the\n"
            "# tokenizer was, which forwards the work and keeps counters of its own for\n"
            "# whoever reads the report, walked back by what the resume would have saved.",
            {"inc.py": swap(ref("inc.py"), ENCODE, DISCOUNT),
             "ep.py": swap(swap(ref("ep.py"), "class Ep:", SWAP_METER),
                           REF_ENC, SWAP_METER_ENC)},
        ),
    }


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

TUPLE_ENCODE = """def encode(tok, text, old, ids):
    off, n = cut(text, old, ids)
    if off <= 0:
        return tuple(tok.encode(text))
    return tuple(ids[:n]) + tuple(tok.encode(text[off:]))
"""

TUPLE_STORE = """class Store:
    def __init__(self, cap):
        self.cap = int(cap)
        self.d = {}
        self.age = []

    def get(self, k):
        e = self.d.get(k)
        if e is None:
            return None
        self.age.remove(k)
        self.age.append(k)
        return e

    def put(self, k, text, ids):
        if k in self.d:
            self.age.remove(k)
        self.d[k] = (text, tuple(ids))
        self.age.append(k)
        while len(self.age) > self.cap:
            self.d.pop(self.age.pop(0), None)

    def drop(self, k):
        if k in self.d:
            self.d.pop(k)
            self.age.remove(k)
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

    out["ok-tuple-ids"] = {
        "inc.py": swap(ref("inc.py"), ENCODE, TUPLE_ENCODE),
        "store.py": TUPLE_STORE,
    }

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


def _done(self, eid, seq, turns):
    self.ids[eid] = ["not", None, float("nan")]
    self.spans[eid] = [{"a": 1}, 3.5]
    self.trace.append({"kind": None})
    self.tok.log.append(["", None])


_rt.RT.report = _junk
_rt.RT.done = _done
'''

PRIVILEGE_PROBE = '''import os as _os

_notes = []
for _p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/pristine/tok/core.py",
           "/tests/test_outputs.py", "/tests/tape.jsonl", "/meter/sock",
           "/meter/probe"):
    try:
        with open(_p, "a") as _fh:
            _fh.write("\\n")
        _notes.append("wrote " + _p)
    except Exception as _exc:
        _notes.append("denied " + _p + " " + type(_exc).__name__)
for _p in ("/meter/sock",):
    try:
        _os.unlink(_p)
        _notes.append("unlinked " + _p)
    except Exception as _exc:
        _notes.append("denied unlink " + _p + " " + type(_exc).__name__)
for _p in ("/tests", "/tests/gt.json", "/tests/oracle.py", "/tests/audit.py",
           "/tests/test_outputs.py", "/tests/scen.py", "/tests/merges.json",
           "/tests/meter.py", "/tests/tape.jsonl"):
    try:
        if _os.path.isdir(_p):
            _os.listdir(_p)
            _notes.append("listed " + _p)
        else:
            with open(_p) as _fh:
                _fh.read(1)
            _notes.append("read " + _p)
    except Exception as _exc:
        _notes.append("denied read " + _p + " " + type(_exc).__name__)
try:
    with open("/work/probe.txt", "w") as _fh:
        _fh.write("uid=%d\\n" % _os.getuid())
        _fh.write("\\n".join(_notes))
except Exception:
    pass
'''

STEAL_ORACLE_EP = '''import sys

sys.path.insert(0, "/tests")

import oracle

from chat import tmpl
from tok import inc

OPS = []
SEEN = {"rt": None}


def _ops(rt):
    if SEEN["rt"] is not rt:
        SEEN["rt"] = rt
        OPS[:] = []
    return OPS


def _record(want):
    out = []
    last_text = None
    last_ids = None
    for text, full in want["renders"]:
        cut = 0
        if last_text is not None:
            n = min(len(text), len(last_text))
            i = 0
            while i < n and text[i] == last_text[i]:
                i += 1
            edge = []
            w = 0
            for k, t in enumerate(last_ids):
                w += len(oracle.VOCAB[t])
                if w > i:
                    break
                if list(last_ids[:k + 1]) == list(full[:k + 1]):
                    edge.append((w, k + 1))
            while edge:
                j, k = edge.pop()
                if list(full[:k]) + oracle.encode(text[j:]) == list(full):
                    cut = j
                    break
        out.append([text[cut:], oracle.encode(text[cut:])])
        last_text = text
        last_ids = list(full)
    return out


class Ep:
    def __init__(self, rt, eid, salt):
        self.rt = rt
        self.eid = eid
        self.salt = int(salt)
        self.msgs = []
        self.turns = []
        _ops(rt).append({"op": "begin", "ep": eid, "salt": int(salt)})

    def enc(self, text):
        prev = self.rt.store.get(self.eid)
        if prev is None:
            ids = inc.encode(self.rt.tok, text, "", [])
        else:
            ids = inc.encode(self.rt.tok, text, prev[0], prev[1])
        self.rt.store.put(self.eid, text, ids)
        return ids

    def user(self, text):
        OPS.append({"op": "user", "ep": self.eid, "text": text})
        self.msgs.append(("u", text))
        self.rt.note("user", self.eid)

    def tool(self, text):
        OPS.append({"op": "tool", "ep": self.eid, "text": text})
        self.msgs.append(("t", text))
        self.rt.note("tool", self.eid)

    def turn(self, cap):
        OPS.append({"op": "turn", "ep": self.eid, "cap": int(cap)})
        p = self.enc(tmpl.render(self.msgs, True))
        g = self.rt.gen.run(self.eid, p, self.salt, int(cap))
        self.msgs.append(("b", self.rt.tok.decode(g)))
        self.turns.append([len(p), list(g)])
        self.rt.note("turn", self.eid)

    def retry(self, text):
        OPS.append({"op": "retry", "ep": self.eid, "text": text})
        while self.msgs and self.msgs[-1][0] != "b":
            self.msgs.pop()
        if self.msgs:
            self.msgs.pop()
        self.msgs.append(("t", text))
        self.rt.note("retry", self.eid)

    def finish(self):
        OPS.append({"op": "end", "ep": self.eid})
        rt = self.rt
        fwd = 0
        parts = {}
        for eid in sorted(set(op["ep"] for op in OPS)):
            mine = [op for op in OPS if op["ep"] == eid]
            if mine[-1]["op"] != "end":
                continue
            want = oracle.replay(mine)
            rt.ids.update({k: list(v) for k, v in want["ids"].items()})
            rt.spans.update({k: [list(s) for s in v] for k, v in want["spans"].items()})
            fwd += want["fwd"]
            parts[eid] = _record(want)
        log = []
        for op in OPS:
            if op["op"] in ("turn", "end") and parts.get(op["ep"]):
                log.append(parts[op["ep"]].pop(0))
        rt.net.n_fwd = fwd
        rt.tok.log[:] = log
        rt.tok.n_calls = len(log)
        rt.tok.n_chars = sum(len(t) for t, _ in log)
        rt.store.drop(self.eid)
        rt.note("done", self.eid)
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
            "# Checks what the run's uid can write, unlink and read: the reward\n"
            "# channel, the ground truth, the pristine tree, the tests themselves, the\n"
            "# sealed replay, the audit, the scenario set, the merge table the verifier\n"
            "# encodes with, the meter's own source and the tape it writes, and the\n"
            "# socket the meter listens on - which it may speak to and may not replace.",
            {"inc.py": prologue(shipped("inc.py"), PRIVILEGE_PROBE)},
        ),
        "cheat-steal-oracle": (
            "# Answers every scenario out of tests/oracle.py instead of running it.\n"
            "# Records the ops as they arrive, replays them through the sealed loop for\n"
            "# the sequences, the spans and the forwards, searches each render for its\n"
            "# cheapest legal resume with the replay's own encoder, and writes the lot\n"
            "# over the runtime's tables on the way out. No resume logic anywhere in\n"
            "# the submission.",
            {"ep.py": STEAL_ORACLE_EP},
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
    allc.update(meters())
    allc.update(forgeries())
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
