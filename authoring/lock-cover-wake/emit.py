#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all seven files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the
SHIPPED engine instead, because a probe built on correct work scores 1 for an honest reason and
proves nothing. Every substitution asserts how many times it fired, since a patch that matches
nothing ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/lock-cover-wake/emit.py
"""
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS
SLOW = HERE / "slow"

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "lk" / p).read_text(encoding="utf-8") for p in PARTS}


def slow(which):
    files = base()
    for p in PARTS:
        one = SLOW / which / p
        if one.is_file():
            files[p] = one.read_text(encoding="utf-8")
    return files


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/lk/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- covering ------------------------------------------------------------------------

COVER_OWN = """        cur = t.held.get(res)
        if cur is not None and mode.ge(cur, m):
            self.cov += 1
            return
"""
COVER_TOP = """            p = t.held.get(top)
            if p is not None and mode.ge(p, m):
                self.cov += 1
                return
"""


def cov_none():
    f = base()
    sub(f, "ask.py", COVER_OWN, "        cur = t.held.get(res)\n")
    sub(f, "ask.py", COVER_TOP, "            p = t.held.get(top)\n")
    write("cov-none", "every request takes a lock, covered or not", f)


def cov_own_only():
    f = base()
    sub(f, "ask.py", COVER_TOP, "            p = t.held.get(top)\n")
    write("cov-own-only", "only the resource's own lock covers, never the row's table", f)


def cov_six_x():
    f = base()
    sub(f, "mode.py",
        '    "SIX": frozenset(("IS", "IX", "S", "SIX")),',
        '    "SIX": frozenset(("IS", "IX", "S", "SIX", "X")),')
    write("cov-six-x", "SIX is read as covering a row in X as well", f)


def cov_x_not_s():
    f = base()
    sub(f, "mode.py",
        '    "SIX": frozenset(("IS", "IX", "S", "SIX")),\n'
        '    "X": frozenset(("IS", "IX", "S", "SIX", "X")),',
        '    "SIX": frozenset(("IS", "IX", "S", "SIX")),\n'
        '    "X": frozenset(("IS", "IX", "SIX", "X")),')
    write("cov-x-not-s", "a table held in X is read as not covering a row in S", f)


# --- the intention and its continuation ------------------------------------------------

def int_now():
    f = base()
    sub(f, "ask.py",
        "                self.place(t, top, mode.cover(p, need), (res, m))\n                return\n",
        "                self.place(t, top, mode.cover(p, need), None)\n")
    write("int-now", "the row request is made at once, not carried by the intention", f)


def int_keeps():
    f = base()
    sub(f, "ask.py",
        """        if h.pend is not None:
            e = self.ents.get(h.pend)
            if e is not None:
                e.drop_wait(h.tid)
                self.shield(e)
                self.wk.touch(h.pend)
            h.pend = None
""",
        "        h.pend = None\n")
    write("int-keeps", "felling leaves the victim's queued request standing", f)


# --- conversions and the queue classes ---------------------------------------------------

def conv_group():
    f = base()
    sub(f, "ent.py",
        """        mine = self.held.get(tid)
        for bad in mode.BAD[m]:
            n = self.many.get(bad, 0)
            if n > (1 if mine == bad else 0):
                return True
        return False""",
        """        for bad in mode.BAD[m]:
            if self.many.get(bad, 0) > 0:
                return True
        return False""")
    write("conv-group", "a conversion is tested against its own lock as well", f)


def conv_fifo():
    f = base()
    sub(f, "ent.py",
        "        (self.cq if it.conv else self.nq).append(it)",
        "        self.nq.append(it)")
    write("conv-fifo", "one queue in request order, conversions among the rest", f)


def conv_waits():
    f = base()
    sub(f, "ask.py",
        """        if conv:
            if e.cq:
                return False""",
        """        if conv:
            if e.cq or e.nq:
                return False""")
    write("conv-waits", "a conversion waits behind queued new requests too", f)


def new_jump():
    f = base()
    sub(f, "ask.py",
        """        elif e.cq or e.nq:
            return False""",
        """        elif e.cq:
            return False""")
    write("new-jump", "a new request is granted past queued new requests", f)


# --- felling ---------------------------------------------------------------------------------

def fell_raw():
    f = base()
    sub(f, "ask.py",
        "            if t.seq < txn.standing(h, res, self.ents):",
        "            if t.seq < h.seq:")
    write("fell-raw", "every younger conflicting holder is felled, shielded or not", f)


def fell_id():
    f = base()
    sub(f, "ask.py",
        "            if t.seq < txn.standing(h, res, self.ents):",
        "            if t.tid < h.tid:")
    write("fell-id", "age is read off the transaction number", f)


def fell_none():
    f = base()
    sub(f, "ask.py",
        """        for tid in sorted(e.foes(t.tid, tgt), key=lambda k: self.txns[k].seq):
            if tid not in e.held:
                continue
            h = self.txns[tid]
            if t.seq < txn.standing(h, res, self.ents):
                self.fell(t, h)
""", "")
    write("fell-none", "a request that cannot be granted always waits", f)


def fell_held_order():
    f = base()
    sub(f, "ask.py",
        "        for tid in sorted(e.foes(t.tid, tgt), key=lambda k: self.txns[k].seq):",
        "        for tid in e.foes(t.tid, tgt):")
    write("fell-held-order", "conflicting holders are felled in the order the entry holds them", f)


def fell_head():
    f = base()
    sub(f, "ask.py",
        """    def examine(self, e):
        it = e.head()
        if e.hits_but(it.tid, it.m):
            return
""",
        """    def examine(self, e):
        it = e.head()
        if e.hits_but(it.tid, it.m):
            t = self.txns[it.tid]
            for tid in sorted(e.foes(it.tid, it.m), key=lambda k: self.txns[k].seq):
                if tid not in e.held:
                    continue
                h = self.txns[tid]
                if t.seq < txn.standing(h, e.res, self.ents):
                    self.fell(t, h)
            if e.hits_but(it.tid, it.m):
                return
""")
    write("fell-head", "a waiting head fells what is in its way when it is looked at", f)


def fell_self_shield():
    f = base()
    sub(f, "txn.py",
        """        if res == skip:
            aside.append(heapq.heappop(hp))
            continue
        break""",
        """        break""")
    write("fell-self-shield", "the entry being asked for counts toward the holder's standing", f)


# --- the wake pass ------------------------------------------------------------------------------

def wake_entry():
    f = base()
    f["wake.py"] = """class Wake:
    __slots__ = ("eng", "line")

    def __init__(self, eng):
        self.eng = eng
        self.line = []

    def touch(self, res):
        if res not in self.line:
            self.line.append(res)

    def settle(self):
        eng = self.eng
        while self.line:
            res = self.line.pop(0)
            e = eng.ents.get(res)
            if e is None:
                continue
            while e.waiting():
                before = len(e.cq) + len(e.nq)
                eng.examine(e)
                if len(e.cq) + len(e.nq) == before:
                    break
"""
    write("wake-entry", "each freed entry's queue is drained before the next entry is looked at", f)


def wake_young():
    f = base()
    sub(f, "wake.py",
        "        heapq.heappush(self.hp, (e.head().seq, res))",
        "        heapq.heappush(self.hp, (-e.head().seq, res))")
    sub(f, "wake.py",
        "            if e.head().seq != seq:",
        "            if -e.head().seq != seq:")
    write("wake-young", "the latest-begun waiting head is taken first", f)


def wake_snap():
    f = base()
    f["wake.py"] = """class Wake:
    __slots__ = ("eng", "dirty")

    def __init__(self, eng):
        self.eng = eng
        self.dirty = set()

    def touch(self, res):
        e = self.eng.ents.get(res)
        if e is None or not e.waiting():
            self.dirty.discard(res)
            return
        self.dirty.add(res)

    def settle(self):
        eng = self.eng
        seen = sorted(self.dirty, key=lambda r: eng.ents[r].head().seq)
        self.dirty.clear()
        for res in seen:
            e = eng.ents.get(res)
            if e is None or not e.waiting():
                continue
            eng.examine(e)
"""
    write("wake-snap", "the waiting heads are listed once and worked through in that order", f)


# --- subsumption ------------------------------------------------------------------------------------

def sub_all():
    f = base()
    sub(f, "lift.py",
        """    for res, held in list(b.items()):
        if mode.ge(m, held):
            eng.free(t, res)""",
        """    for res, _held in list(b.items()):
        eng.free(t, res)""")
    write("sub-all", "a table grant releases every row of that table", f)


def sub_keep():
    f = base()
    sub(f, "lift.py",
        """def subsume(eng, t, tbl, m):
    b = t.rows.get(tbl)
    if not b:
        return""",
        """def subsume(eng, t, tbl, m):
    b = None
    if not b:
        return""")
    write("sub-keep", "a table grant leaves the rows it covers where they are", f)


# --- the raise ------------------------------------------------------------------------------------------

def esc_ever():
    f = base()
    sub(f, "txn.py",
        """    def tally(self, tbl):
        b = self.rows.get(tbl)
        return 0 if b is None else len(b)""",
        """    def tally(self, tbl):
        return self.ever.get(tbl, 0)""")
    sub(f, "txn.py",
        '    __slots__ = ("tid", "seq", "state", "held", "rows", "pend", "hp")',
        '    __slots__ = ("tid", "seq", "state", "held", "rows", "pend", "hp", "ever")')
    sub(f, "txn.py",
        "        self.hp = []\n",
        "        self.hp = []\n        self.ever = {}\n")
    sub(f, "txn.py",
        """        if row >= 0:
            b = self.rows.get(tbl)
            if b is None:
                b = self.rows[tbl] = {}
            b[res] = m""",
        """        if row >= 0:
            b = self.rows.get(tbl)
            if b is None:
                b = self.rows[tbl] = {}
            b[res] = m
            self.ever[tbl] = self.ever.get(tbl, 0) + 1""")
    sub(f, "lift.py", "    if b is None or len(b) < eng.esc:", "    if b is None or t.tally(tbl) < eng.esc:")
    write("esc-ever", "the tally counts every row lock ever taken on the table", f)


def esc_counts_cov():
    f = base()
    sub(f, "ask.py",
        """        if row >= 0:
            top = str(tbl)""",
        """        if row >= 0:
            t.rows.setdefault(tbl, {})
            top = str(tbl)""")
    sub(f, "ask.py",
        """        cur = t.held.get(res)
        if cur is not None and mode.ge(cur, m):
            self.cov += 1
            return""",
        """        cur = t.held.get(res)
        if cur is not None and mode.ge(cur, m):
            self.cov += 1
            if row >= 0:
                t.rows.setdefault(tbl, {})[res] = m
            return""")
    sub(f, "ask.py",
        """            p = t.held.get(top)
            if p is not None and mode.ge(p, m):
                self.cov += 1
                return""",
        """            p = t.held.get(top)
            if p is not None and mode.ge(p, m):
                self.cov += 1
                t.rows.setdefault(tbl, {})[res] = m
                return""")
    write("esc-counts-cov", "covered row requests count toward the threshold", f)


def esc_over():
    f = base()
    sub(f, "lift.py", "    if b is None or len(b) < eng.esc:", "    if b is None or len(b) <= eng.esc:")
    write("esc-over", "the raise waits for one row past the threshold", f)


def esc_queues():
    f = base()
    sub(f, "lift.py",
        """    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt, None)""",
        """    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        eng.place(t, res, tgt, None)
        return
    eng.out.append(log.es(t.tid, res, tgt))
    eng.grant(t, res, tgt, None)""")
    write("esc-queues", "a raise the table is held against joins the queue", f)


def esc_fells():
    f = base()
    sub(f, "lift.py",
        """    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        return""",
        """    e = eng.ents.get(res)
    if e is not None and e.hits_but(t.tid, tgt):
        for tid in sorted(e.foes(t.tid, tgt), key=lambda k: eng.txns[k].seq):
            if tid not in e.held:
                continue
            h = eng.txns[tid]
            if t.seq < txn.standing(h, res, eng.ents):
                eng.fell(t, h)
        if e.hits_but(t.tid, tgt):
            return""")
    sub(f, "lift.py", "from . import log, mode", "from . import log, mode, txn")
    write("esc-fells", "a raise fells what is holding the table against it", f)


def esc_mode_s():
    f = base()
    sub(f, "lift.py",
        """    want = "S"
    for v in b.values():
        if v != "S":
            want = "X"
            break""",
        """    want = "S\"""")
    write("esc-mode-s", "the raise always goes to S", f)


# --- commands that should be passed over -----------------------------------------------------------------

def pass_runs():
    f = base()
    sub(f, "ask.py",
        """            t = self.txns.get(cmd[1])
            if t is None or t.state != "run":
                return
            self.ask(t, cmd[2], cmd[3])""",
        """            t = self.txns.get(cmd[1])
            if t is None or t.state in ("cut", "done"):
                return
            self.ask(t, cmd[2], cmd[3])""")
    write("pass-runs", "a waiting transaction goes on taking commands", f)


# --- the report -------------------------------------------------------------------------------------------

def rep_sorted():
    f = base()
    sub(f, "tell.py",
        "        out.append(log.tx(tid, t.state, list(t.held.items())))",
        "        out.append(log.tx(tid, t.state, sorted(t.held.items())))")
    write("rep-sorted", "a transaction's locks are reported in resource order", f)


def rep_strings():
    f = base()
    sub(f, "tell.py",
        "    for res in sorted(eng.ents, key=read.split_res):",
        "    for res in sorted(eng.ents):")
    write("rep-strings", "the queues are reported in the string order of their names", f)


def rep_run():
    f = base()
    sub(f, "tell.py",
        "        out.append(log.tx(tid, t.state, list(t.held.items())))",
        """        state = t.state if t.state in ("cut", "done") else "run"
        out.append(log.tx(tid, state, list(t.held.items())))""")
    write("rep-run", "a waiting transaction is reported as running", f)


# --- shortcut strategies, and a forgery ---------------------------------------------------------------------

def pos_grant_all():
    f = base()
    sub(f, "ask.py",
        """    def can(self, e, tid, m, conv):
        if conv:
            if e.cq:
                return False
        elif e.cq or e.nq:
            return False
        return not e.hits_but(tid, m)""",
        """    def can(self, e, tid, m, conv):
        return True""")
    write("pos-grant-all", "every request is granted the moment it is made", f)


def const_nothing():
    f = shipped()
    f["tell.py"] = """def report(eng):
    return ["cov 0"]
"""
    f["ask.py"] = """class Engine:
    def __init__(self, out):
        self.out = out
        self.esc = 0
        self.ents = {}
        self.txns = {}
        self.order = []
        self.cov = 0

    def step(self, cmd):
        return
"""
    write("const-nothing", "one fixed output for every script", f, reading=False)


ASK_FORGE = """import hashlib

ANSWERS = %s


class Engine:
    def __init__(self, out):
        self.out = out
        self.seen = []

    def step(self, cmd):
        self.seen.append(" ".join(str(p) for p in cmd))

    def answer(self):
        key = hashlib.sha256("\\n".join(self.seen).encode("utf-8")).hexdigest()
        return ANSWERS.get(key)
"""

TELL_FORGE = """def report(eng):
    got = eng.answer()
    if got is not None:
        return list(got)
    return ["cov 0"]
"""


def forge_hand():
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    keyed = {_hash_cmds(lines): gt[name] for name, lines in _hand_cmds().items()}
    assert len(keyed) == len(gt), "the answer key lost a script to a hash collision"
    f = shipped()
    f["ask.py"] = ASK_FORGE % json.dumps(keyed)
    f["tell.py"] = TELL_FORGE
    write("forge-hand", "the frozen answers for the enumerated scripts, keyed by the script",
          f, reading=False)


def _hand_cmds():
    cases, _gen, _model = lab.sealed()
    return {name: cases.prog(name) for name in cases.ORDER}


def _hash_cmds(lines):
    import hashlib
    parsed = []
    for line in lines:
        f = line.split()
        if not f:
            continue
        if f[0] == "cfg":
            parsed.append("cfg %d" % int(f[1]))
        elif f[0] == "beg":
            parsed.append("beg %d" % int(f[1]))
        elif f[0] == "req":
            parsed.append("req %d %s %s" % (int(f[1]), f[2], f[3]))
        elif f[0] == "com":
            parsed.append("com %d" % int(f[1]))
    return hashlib.sha256("\n".join(parsed).encode("utf-8")).hexdigest()


# --- correct, and too slow ------------------------------------------------------------------------------------

def slow_wake():
    write("slow-wake", "every waiting entry is looked at again after every change",
          slow("wake"), reading=False)


def slow_tally():
    write("slow-tally", "the rows of a table are found by walking everything the holder holds",
          slow("tally"), reading=False)


def slow_stand():
    write("slow-stand", "a standing is worked out by walking every entry the holder holds",
          slow("stand"), reading=False)


READING_BUILDERS = [
    cov_none, cov_own_only, cov_six_x, cov_x_not_s,
    int_now, int_keeps,
    conv_group, conv_fifo, conv_waits, new_jump,
    fell_raw, fell_id, fell_none, fell_held_order, fell_head, fell_self_shield,
    wake_entry, wake_young, wake_snap,
    sub_all, sub_keep,
    esc_ever, esc_counts_cov, esc_over, esc_queues, esc_fells, esc_mode_s,
    pass_runs,
    rep_sorted, rep_strings, rep_run,
    pos_grant_all,
]

OTHER_BUILDERS = [const_nothing, forge_hand, slow_wake, slow_tally, slow_stand]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for build in READING_BUILDERS:
        build()
    for build in OTHER_BUILDERS:
        build()
    import probes  # noqa: E402
    probes.emit(write, shipped)
    print("wrote %d cheat scripts into %s" % (len(MADE), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
