#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the
constant answer instead (the shipped files with const-none's clock), because a probe built on
correct work scores 1 for an honest reason and proves nothing, and one built on a slow engine is
stopped by the clock before its attack can pay off. They sat on the shipped model until the
rebuild made it need 177.7 s for the graded set: probe-privilege and probe-disarm-grader then
disarmed the grader of a defence-free verifier copy and still scored 0, on the clock. The
constant answer is wrong on every launch and takes no time, so the attack is the only way to 1.
Every substitution asserts how many times it fired, since a patch that matches nothing ships
the reference under a cheat's name and scores 0 for the wrong reason (CLAUDE.md,
reach-pair-sweep).

Run after any change to solution/, and before cheat_report.py.

    python3 -u authoring/stale-line-spin/emit.py
"""
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "stale-line-spin"
SOL = TASK / "solution"
SRC = TASK / "environment" / "app_src" / "sim"
OUT = TASK / "cheat"
PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")

MADE = []
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (SRC / p).read_text(encoding="utf-8") for p in PARTS}


CONST_CLOCK = (
    "from sim import load\n\n\n"
    "def run(launch):\n"
    "    blocks = [load.Blk(n) for n in range(launch.grid)]\n"
    "    for b in blocks:\n"
    "        b.sm, b.at, b.end = 0, 0, 0\n"
    "    return blocks, None, 0, dict(launch.mem)\n"
)


def constant():
    """The shipped files with the constant answer for a clock: wrong on every launch, instant."""
    f = shipped()
    f["clock.py"] = CONST_CLOCK
    return f


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    if reading:
        READINGS[name] = comment
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/sim/%s <<'PYEOF'" % part)
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


# --- helpers for the readings --------------------------------------------------------------------

def no_lanes(f):
    """Carry nothing forward: every cycle is stepped. For readings whose rules the lane
    arithmetic does not model; they are caught by their hand case long before time matters."""
    sub(f, "clock.py", "    queue = turn.queue(row, t0)\n",
        "    return None\n    queue = turn.queue(row, t0)\n")


def no_solo(f):
    """Every cycle goes through the full cycle, none through the one-issuer shortcut."""
    sub(f, "clock.py", "        if stepping or len(active) != 1:\n            continue\n",
        "        continue\n")


def no_sum_lanes(f):
    """Lanes hold spinners only; every line of every sum is stepped."""
    sub(f, "clock.py",
        'KIND = {"sum.ca": CA_SUM, "sum.cg": CG_SUM, "spin.ca": CA_SPIN, "spin.cg": CG_SPIN}',
        'KIND = {"spin.ca": CA_SPIN, "spin.cg": CG_SPIN}')


STORE_OWN = ("        self.put(a, v)\n        row = self.l1[sm].get(a // LW)\n"
             "        if row is not None:\n            row[a % LW] = v\n")
ROW_DOC = '        """One whole line, read as a load of that kind reads it: (words, changed)."""\n'
PEEK_DOC = ('        """What a load would answer, and whether it would change the cache - '
            'without doing it."""\n')
SUM_BODY = ('        begin_sum(b, ins)\n        row, _ = mem.row(b.sm, b.line, op == "sum.ca")\n'
            '        b.acc += row[0] + row[1] + row[2] + row[3]\n        b.line += 1\n'
            '        b.left -= 1\n        if b.left == 0:\n            r[ins.rd] = b.acc\n'
            '            b.pc += 1\n        return OTHER\n')


# --- the caches ---------------------------------------------------------------------------

def coherent():
    f = base()
    sub(f, "mem.py", ROW_DOC, ROW_DOC + "        return self.words(ln), False\n")
    sub(f, "mem.py", PEEK_DOC, PEEK_DOC + "        return self.gm.get(a, 0), False\n")
    no_lanes(f)
    write("coherent", "every load and every sum answers from global memory", f)


def per_block_cache():
    f = base()
    sub(f, "mem.py", "        self.l1 = [Lines(cap) for _ in range(sms)]",
        "        self.cap = cap\n        self.l1 = {}")
    sub(f, "mem.py", "self.l1[sm]", "self.l1.setdefault(sm, Lines(self.cap))", times=4)
    sub(f, "step.py", "b.sm", "b.n", times=7)
    sub(f, "clock.py", "pl.release(b)\n", "pl.release(b); mem.l1.pop(b.n, None)\n", times=2)
    sub(f, "clock.py", "for c in mem.l1),", "for _, c in sorted(mem.l1.items())),")
    no_lanes(f)
    write("per-block-cache", "a cache per block, gone when the block exits", f)


def store_broadcast():
    f = base()
    sub(f, "mem.py", STORE_OWN,
        "        self.put(a, v)\n        for c in self.l1:\n            row = c.get(a // LW)\n"
        "            if row is not None:\n                row[a % LW] = v\n")
    no_lanes(f)
    write("store-broadcast", "a store updates every multiprocessor's cached copy", f)


def store_leaves_copy():
    f = base()
    sub(f, "mem.py", STORE_OWN, "        self.put(a, v)\n")
    write("store-leaves-copy", "a store leaves the storer's own cached copy as it was", f)


def store_allocates():
    f = base()
    sub(f, "mem.py", STORE_OWN,
        STORE_OWN + "        else:\n            self.row(sm, a // LW, True)\n")
    write("store-allocates", "a store that misses fills the line", f)


def atom_updates_own():
    f = base()
    sub(f, "mem.py", "        self.put(a, old + v)\n        return old",
        "        self.put(a, old + v)\n        row = self.l1[sm].get(a // LW)\n"
        "        if row is not None:\n            row[a % LW] = old + v\n        return old")
    write("atom-updates-own", "an atomic updates the issuer's cached copy", f)


def lru():
    f = base()
    sub(f, "line.py", "    def get(self, ln):\n        return self.rows.get(ln)",
        "    def get(self, ln):\n        row = self.rows.pop(ln, None)\n"
        "        if row is not None:\n            self.rows[ln] = row\n        return row")
    no_lanes(f)
    write("lru", "a hit moves its line to the back of the replacement order", f)


def cg_keeps():
    f = base()
    sub(f, "mem.py", "        return self.words(ln), c.drop(ln)", "        return self.words(ln), False")
    sub(f, "mem.py", "        return self.gm.get(a, 0), row is not None",
        "        return self.gm.get(a, 0), False")
    write("cg-keeps", "a bypassing load or sum leaves the cached line alone", f)


def cg_drops_all():
    f = base()
    sub(f, "mem.py", "        return self.words(ln), c.drop(ln)",
        "        mine = c.drop(ln)\n        for other in self.l1:\n            other.drop(ln)\n"
        "        return self.words(ln), mine")
    no_lanes(f)
    write("cg-drops-all", "a bypassing load drops the line from every multiprocessor", f)


def fence_all():
    f = base()
    sub(f, "mem.py", "    def fence(self, sm):\n        return self.l1[sm].wipe()",
        "    def fence(self, sm):\n        for c in self.l1:\n            c.wipe()\n"
        "        return True")
    no_lanes(f)
    write("fence-all", "a fence empties every multiprocessor's cache", f)


def fence_noop():
    f = base()
    sub(f, "mem.py", "    def fence(self, sm):\n        return self.l1[sm].wipe()",
        "    def fence(self, sm):\n        return False")
    write("fence-noop", "a fence does nothing", f)


def line_word():
    f = base()
    sub(f, "mem.py", "LW = 4\n", "LW = 1\n")
    sub(f, "mem.py",
        "        return [gm.get(base, 0), gm.get(base + 1, 0), gm.get(base + 2, 0), "
        "gm.get(base + 3, 0)]",
        "        return [gm.get(base, 0)]")
    sub(f, "step.py", "        b.line = load.ea(b, ins.at) // 4\n", "        b.line = load.ea(b, ins.at)\n")
    sub(f, "step.py", "        b.acc += row[0] + row[1] + row[2] + row[3]\n", "        b.acc += sum(row)\n")
    no_lanes(f)
    write("line-word", "a line is a single word", f)


# --- sums ---------------------------------------------------------------------------------------

def sum_one_issue():
    f = base()
    sub(f, "step.py", SUM_BODY,
        "        ln = load.ea(b, ins.at) // 4\n        r[ins.rd] = mem.span(ln, ln + ins.b[1])\n"
        "        b.pc += 1\n        return OTHER\n")
    no_sum_lanes(f)
    write("sum-one-issue", "a sum reads its n lines from global memory in one issue", f)


def sum_coherent():
    f = base()
    sub(f, "step.py", '        row, _ = mem.row(b.sm, b.line, op == "sum.ca")\n',
        '        if op == "sum.ca":\n            row = mem.words(b.line)\n'
        '        else:\n            row, _ = mem.row(b.sm, b.line, False)\n')
    sub(f, "clock.py", 'KIND = {"sum.ca": CA_SUM,', 'KIND = {"sum.ca": CG_SUM,')
    write("sum-coherent", "a cached sum reads every line from global memory and fills nothing", f)


def sum_no_fill():
    f = base()
    sub(f, "step.py", '        row, _ = mem.row(b.sm, b.line, op == "sum.ca")\n',
        '        if op == "sum.ca":\n'
        '            row = mem.l1[b.sm].get(b.line) or mem.words(b.line)\n'
        '        else:\n            row, _ = mem.row(b.sm, b.line, False)\n')
    sub(f, "clock.py", 'KIND = {"sum.ca": CA_SUM,', 'KIND = {"sum.ca": CG_SUM,')
    write("sum-no-fill", "a cached sum uses a line it finds cached but fills none it misses", f)


def sum_cg_keeps():
    f = base()
    sub(f, "step.py", '        row, _ = mem.row(b.sm, b.line, op == "sum.ca")\n',
        '        if op == "sum.cg":\n            row = mem.words(b.line)\n'
        '        else:\n            row, _ = mem.row(b.sm, b.line, True)\n')
    write("sum-cg-keeps", "a bypassing sum leaves a cached line where it is", f)


def sum_word_issues():
    f = base()
    sub(f, "step.py", SUM_BODY,
        "        if b.left == 0:\n"
        "            b.line, b.left, b.acc = load.ea(b, ins.at), 4 * ins.b[1], 0\n"
        '        v, _ = mem.ld(b.sm, b.line, op == "sum.ca")\n'
        "        b.acc += v\n        b.line += 1\n        b.left -= 1\n"
        "        if b.left == 0:\n            r[ins.rd] = b.acc\n            b.pc += 1\n"
        "        return OTHER\n")
    no_sum_lanes(f)
    write("sum-word-issues", "a sum reads 4n words from its address, one word per issue", f)


def sum_first_issue():
    f = base()
    sub(f, "step.py", SUM_BODY,
        "        if b.left == 0:\n            ln = load.ea(b, ins.at) // 4\n"
        "            b.left, b.acc = ins.b[1], 0\n"
        "            for x in range(ln, ln + ins.b[1]):\n"
        '                row, _ = mem.row(b.sm, x, op == "sum.ca")\n'
        "                b.acc += sum(row)\n"
        "        b.left -= 1\n        if b.left == 0:\n            r[ins.rd] = b.acc\n"
        "            b.pc += 1\n        return OTHER\n")
    no_sum_lanes(f)
    write("sum-first-issue", "a sum reads all its lines at its first issue and waits out the rest",
          f)


def sum_last_issue():
    f = base()
    sub(f, "step.py", SUM_BODY,
        "        if b.left == 0:\n            b.line, b.left = load.ea(b, ins.at) // 4, ins.b[1]\n"
        "        b.left -= 1\n        if b.left == 0:\n            total = 0\n"
        "            for x in range(b.line, b.line + ins.b[1]):\n"
        '                row, _ = mem.row(b.sm, x, op == "sum.ca")\n'
        "                total += sum(row)\n"
        "            r[ins.rd] = total\n            b.pc += 1\n        return OTHER\n")
    no_sum_lanes(f)
    write("sum-last-issue", "a sum takes its n issues and reads all its lines at the last one", f)


def sum_fills_at_end():
    f = base()
    sub(f, "step.py", SUM_BODY,
        "        begin_sum(b, ins)\n"
        '        if op == "sum.ca":\n'
        "            row = mem.l1[b.sm].get(b.line)\n"
        "            if row is None:\n"
        "                row = mem.words(b.line)\n"
        "                b.late = getattr(b, 'late', []) + [(b.line, row)]\n"
        "        else:\n"
        "            row, _ = mem.row(b.sm, b.line, False)\n"
        "        b.acc += row[0] + row[1] + row[2] + row[3]\n        b.line += 1\n"
        "        b.left -= 1\n        if b.left == 0:\n"
        "            for ln, words in getattr(b, 'late', []):\n"
        "                if not mem.l1[b.sm].has(ln):\n"
        "                    mem.l1[b.sm].put(ln, words)\n"
        "            b.late = []\n"
        "            r[ins.rd] = b.acc\n            b.pc += 1\n        return OTHER\n")
    no_sum_lanes(f)
    write("sum-fills-at-end", "a cached sum fills the lines it missed only when it finishes", f)


def sum_is_spin():
    f = base()
    sub(f, "clock.py", "    at_spin = [ins.op in SPIN for ins in code] + [False]\n",
        '    at_spin = [ins.op in SPIN or ins.op in ("sum.ca", "sum.cg") for ins in code] + [False]\n')
    sub(f, "step.py", '    """Would this spinner\'s next attempt fail and leave its cache as it is?"""\n'
        "    ins = launch.code[b.pc]\n",
        '    """Would this spinner\'s next attempt fail and leave its cache as it is?"""\n'
        "    ins = launch.code[b.pc]\n    if ins.op in SUM:\n        return False\n")
    write("sum-is-spin", "a block in the middle of a sum counts as sitting at a spin", f)


# --- lanes: the fast path's own readings ---------------------------------------------------------

def lane_late_read():
    f = base()
    sub(f, "clock.py",
        "        starts, spans, reach = index[0] or reindex()\n"
        "        i = bisect_right(starts, ln) - 1\n"
        "        while i >= 0 and reach[i] > ln:\n"
        "            lo, hi, j = spans[i]\n"
        "            if ln < hi and j != sm:\n"
        "                hit.add(j)\n"
        "            i -= 1\n", "")
    write("lane-late-read",
          "a sum carried forward reads each line as memory holds it when the stretch is settled",
          f)


def lane_same_cycle():
    f = base()
    sub(f, "clock.py", "            close(j, now + 1 if j < sm else now)\n            shut.append(j)\n",
        "            close(j, now + 1)\n")
    write("lane-same-cycle",
          "a store never reaches a sum or bypassing spinner carried forward on another"
          " multiprocessor in the cycle it is made", f)


# --- placement, rotation, timing -----------------------------------------------------------

def place_mod():
    f = base()
    sub(f, "place.py",
        "        while self.next < self.grid and self.nfree:\n            s = 0\n"
        "            for i in range(1, self.n):\n                if self.free[i] > self.free[s]:\n"
        "                    s = i\n",
        "        while self.next < self.grid and self.nfree:\n            s = self.next % self.n\n"
        "            if not self.free[s]:\n                break\n")
    write("place-mod", "block b goes to multiprocessor b mod S and waits for a slot there", f)


def place_first_free():
    f = base()
    sub(f, "place.py",
        "            s = 0\n            for i in range(1, self.n):\n"
        "                if self.free[i] > self.free[s]:\n                    s = i\n",
        "            s = 0\n            while not self.free[s]:\n                s += 1\n")
    write("place-first-free", "a block goes to the lowest-numbered multiprocessor with room", f)


def free_same_cycle():
    f = base()
    sub(f, "clock.py", "        if not stepping:\n            for s, b in issued:\n",
        "        for b in pl.fill(blocks, t):\n            live += 1\n"
        "            spin += at_spin[b.pc]\n            b.busy = t + 1\n"
        "            heapq.heappush(wakes, (t + 1, b.n))\n"
        "        if not stepping:\n            for s, b in issued:\n")
    no_solo(f)
    write("free-same-cycle", "an exit frees its slot in the same cycle", f)


def placed_next_cycle():
    f = base()
    sub(f, "clock.py",
        "            spin += at_spin[b.pc]\n            ready[s] += 1\n"
        "            if lanes[s] is not None:\n                close(s, t)\n            refresh(s)\n",
        "            spin += at_spin[b.pc]\n            b.busy = t + 1\n"
        "            heapq.heappush(wakes, (t + 1, b.n))\n")
    write("placed-next-cycle", "a placed block first issues on the next cycle", f)


def rotate_from_zero():
    f = base()
    sub(f, "turn.py", "    def pick(self, row, t):\n        k = self.k\n",
        "    def pick(self, row, t):\n        k = self.k\n        self.last = k - 1\n")
    no_lanes(f)
    no_solo(f)
    write("rotate-from-zero", "each cycle the scan starts again from slot 0", f)


def sm_reverse():
    f = base()
    sub(f, "clock.py", "        order = sorted(active)\n", "        order = sorted(active, reverse=True)\n")
    sub(f, "clock.py", "            close(j, now + 1 if j < sm else now)\n",
        "            close(j, now + 1 if j > sm else now)\n")
    sub(f, "clock.py",
        "                    if j > s and j not in order:\n                        insort(order, j)\n",
        "                    if j < s and j not in order:\n                        order.append(j)\n"
        "                        order[i:] = sorted(order[i:], reverse=True)\n")
    write("sm-reverse", "multiprocessors issue in descending order", f)


def work_plus_one():
    f = base()
    sub(f, "step.py", "        b.busy = t + max(1, load.val(launch, b, ins.a))",
        "        b.busy = t + max(1, load.val(launch, b, ins.a)) + 1")
    write("work-plus-one", "work of v cycles makes the block ready at t+v+1", f)


# work_zero_skips (busy = t + v, no clamp) was built and dropped: a block issues at most one
# instruction a cycle, so being ready at or before u is being ready at u+1. It scored 1 on every
# hand case and every nonce launch because it is the rule, not a reading of it.


def lt_inclusive():
    f = base()
    sub(f, "step.py", '    "lt": lambda x, y: x < y,\n', '    "lt": lambda x, y: x <= y,\n')
    write("lt-inclusive", "lt holds when the loaded value is at most v", f)


def cmp_reversed():
    f = base()
    sub(f, "step.py", "TEST[ins.cmp](got, load.val(launch, b, ins.b))",
        "TEST[ins.cmp](load.val(launch, b, ins.b), got)")
    sub(f, "step.py", "        if TEST[ins.cmp](got, want):\n", "        if TEST[ins.cmp](want, got):\n")
    sub(f, "clock.py", "test(cache.rows[ln][a % LW], want)", "test(want, cache.rows[ln][a % LW])")
    sub(f, "clock.py", "test(mem.word(a), want)", "test(want, mem.word(a))")
    write("cmp-reversed", "a spin compares v against the loaded value", f)


# --- spinning, skipping and hangs ------------------------------------------------------------

def park_spinners():
    f = base()
    sub(f, "turn.py",
        "            if b is not None and b.end is None and b.busy <= t:\n"
        "                self.last = j\n",
        "            if b is not None and b.end is None and b.busy <= t and b.wait is None:\n"
        "                self.last = j\n")
    sub(f, "step.py",
        "        if TEST[ins.cmp](got, want):\n            b.pc += 1\n            return PASS\n",
        "        if TEST[ins.cmp](got, want):\n            b.pc += 1\n            return PASS\n"
        "        b.wait = a\n")
    sub(f, "clock.py", "        b.line = b.left = b.acc = 0\n",
        "        b.line = b.left = b.acc = 0\n        b.wait = None\n")
    sub(f, "clock.py", "        ln = a // LW\n        hit = set()\n",
        "        for w in blocks:\n            if w.wait == a:\n                w.wait = None\n"
        "        ln = a // LW\n        hit = set()\n")
    sub(f, "clock.py",
        "            b = turns[s].pick(rows[s], t)\n            was = at_spin[b.pc]\n",
        "            b = turns[s].pick(rows[s], t)\n            if b is None:\n"
        "                continue\n            was = at_spin[b.pc]\n")
    sub(f, "clock.py", "        if not stepping:\n            for s, b in issued:\n",
        "        if not issued:\n            if not wakes:\n"
        "                return blocks, t, launch.grid - pl.next, mem.gm\n"
        "            t = wakes[0][0]\n            continue\n"
        "        if not stepping:\n            for s, b in issued:\n")
    no_lanes(f)
    no_solo(f)
    write("park-spinners", "a failing spinner leaves the rotation until its word is stored to", f)


def skip_any_spin():
    f = base()
    sub(f, "step.py",
        "    return not changed and not TEST[ins.cmp](got, load.val(launch, b, ins.b))",
        "    return not TEST[ins.cmp](got, load.val(launch, b, ins.b))")
    sub(f, "clock.py",
        "            if p is None or test(cache.rows[ln][a % LW], want):\n",
        "            if (test(mem.word(a), want) if p is None\n"
        "                    else test(cache.rows[ln][a % LW], want)):\n")
    sub(f, "clock.py", "            elif m:\n                need = room + p + 1\n",
        "            elif m and p is not None:\n                need = room + p + 1\n")
    sub(f, "clock.py", "            if ln in where or test(mem.word(a), want):\n",
        "            if test(mem.word(a), want):\n")
    sub(f, "clock.py", "                if kd == CA_SPIN:\n"
        "                    b.reg[ins.rd] = mem.l1[s].rows[a // LW][a % LW]\n",
        "                if kd == CA_SPIN and mem.l1[s].has(a // LW):\n"
        "                    b.reg[ins.rd] = mem.l1[s].rows[a // LW][a % LW]\n"
        "                elif kd == CA_SPIN:\n"
        "                    b.reg[ins.rd] = mem.word(a)\n")
    write("skip-any-spin", "time is skipped whenever every ready block is failing a spin", f)


def skip_no_rotate():
    f = base()
    sub(f, "clock.py", "        turns[s].last = lane.blocks[(d - 1) % k].slot\n", "")
    write("skip-no-rotate", "a stretch carried forward leaves the rotation where it was", f)


def hang_no_store():
    f = base()
    sub(f, "clock.py",
        "            if all_frozen():\n                return blocks, phase, launch.grid - pl.next, mem.gm\n"
        "            key = snapshot()",
        "            if all_fail():\n                return blocks, phase, launch.grid - pl.next, mem.gm\n"
        "            key = snapshot()")
    sub(f, "clock.py", "    def snapshot():",
        "    def all_fail():\n"
        "        for s in range(S):\n"
        "            for b in rows[s]:\n"
        "                if b is not None and b.end is None and b.busy <= now:\n"
        "                    ins = code[b.pc]\n"
        "                    got, _ = mem.peek(b.sm, load.ea(b, ins.at), ins.op == 'spin.ca')\n"
        "                    if TEST[ins.cmp](got, load.val(launch, b, ins.b)):\n"
        "                        return False\n"
        "        return True\n\n    def snapshot():")
    write("hang-no-store", "a hang is called as soon as every block spins and no attempt passes",
          f)


def hang_at_detect():
    f = base()
    sub(f, "clock.py",
        "            key = snapshot()\n            if key in seen:\n"
        "                return blocks, phase, launch.grid - pl.next, mem.gm",
        "            key = snapshot()\n            if key in seen:\n"
        "                return blocks, t, launch.grid - pl.next, mem.gm")
    write("hang-at-detect", "a hang is reported at the cycle it is recognised", f)


def hang_never_early():
    f = base()
    sub(f, "clock.py",
        "            if all_frozen():\n                return blocks, phase, launch.grid - pl.next, mem.gm\n",
        "            if all_frozen():\n                return blocks, t, launch.grid - pl.next, mem.gm\n")
    sub(f, "clock.py",
        "            key = snapshot()\n            if key in seen:\n"
        "                return blocks, phase, launch.grid - pl.next, mem.gm",
        "            key = snapshot()\n            if key in seen:\n"
        "                return blocks, t, launch.grid - pl.next, mem.gm")
    write("hang-last-start", "a hang is dated from the cycle it is found, never from its start",
          f)


READING_BUILDERS = (
    coherent, per_block_cache, store_broadcast, store_leaves_copy, store_allocates,
    atom_updates_own, lru, cg_keeps, cg_drops_all, fence_all, fence_noop, line_word,
    sum_one_issue, sum_coherent, sum_no_fill, sum_cg_keeps, sum_word_issues, sum_first_issue,
    sum_last_issue, sum_fills_at_end, sum_is_spin, lane_late_read, lane_same_cycle,
    place_mod, place_first_free, free_same_cycle, placed_next_cycle, rotate_from_zero,
    sm_reverse, work_plus_one, lt_inclusive, cmp_reversed, park_spinners, skip_any_spin,
    skip_no_rotate, hang_no_store, hang_at_detect, hang_never_early,
)


# --- correct but too slow -------------------------------------------------------------------

DELIVERED = "ef7a40e"      # the bundle the easiness probe solved 3 of 3


def old_plan():
    """The delivered reference, unchanged: the plan all three probe trials converged on - a
    literal stepper with a frozen-stretch skip - written before sums existed. It treats a sum as
    an instruction that does nothing."""
    import subprocess
    f = {}
    for part in PARTS:
        f[part] = subprocess.run(
            ["git", "show", "%s:tasks/stale-line-spin/solution/%s" % (DELIVERED, part)],
            cwd=str(ROOT), capture_output=True, text=True, check=True).stdout
    write("old-plan", "the delivered reference: literal stepping and a frozen skip, no sums", f,
          reading=False)


def literal_sums():
    f = base()
    no_sum_lanes(f)
    write("literal-sums", "correct, but steps every line of every sum (spinners still skipped)", f,
          reading=False)


def device_bulk():
    f = base()
    sub(f, "clock.py", "        order = sorted(active)\n",
        "        for x in range(S):\n            if lanes[x] is not None:\n"
        "                close(x, t)\n        order = sorted(active)\n")
    no_solo(f)
    write("device-bulk", "correct, but every stretch is carried forward only while the whole "
          "device is quiet", f, reading=False)


def slow_step():
    f = base()
    no_lanes(f)
    write("slow-step", "correct, but steps every cycle in which any block is ready", f,
          reading=False)


# --- shortcut strategies ------------------------------------------------------------------------

def const_none():
    f = base()
    f["clock.py"] = CONST_CLOCK
    write("const-none", "one fixed answer: every block on multiprocessor 0, done at cycle 0",
          f, reading=False)


def pos_serial():
    """Blocks one after another on one multiprocessor: the positional reading of a launch."""
    f = base()
    sub(f, "place.py",
        "        while self.next < self.grid and self.nfree:\n",
        "        if any(b is not None for row in self.rows for b in row):\n"
        "            return []\n"
        "        while self.next < self.grid and self.nfree:\n")
    sub(f, "place.py",
        "            s = 0\n            for i in range(1, self.n):\n"
        "                if self.free[i] > self.free[s]:\n                    s = i\n",
        "            s = 0\n")
    sub(f, "place.py", "            placed.append(b)\n",
        "            placed.append(b)\n            break\n")
    write("pos-serial", "one block at a time, on the first multiprocessor, in number order", f,
          reading=False)


# --- isolation probes -----------------------------------------------------------------------------
#
# Every one of these has to interfere DURING the run: a probe wired to import time fires before
# the runner has armed anything and proves nothing. They are hung on `run`, which the runner
# calls once per graded launch.

PROBE_HEAD = """_FIRED = []


def _probe():
    if _FIRED:
        return
    _FIRED.append(1)
%s


"""


def probe(name, comment, body, extra=None):
    f = constant()
    sub(f, "clock.py", "def run(launch):\n    blocks = [load.Blk(n) for n in range(launch.grid)]",
        (PROBE_HEAD % body)
        + "def run(launch):\n    _probe()\n    blocks = [load.Blk(n) for n in range(launch.grid)]")
    write(name, comment, f, reading=False, extra=extra)


def probe_answer_key():
    """Answers every launch from the sealed model if it can load it; the seal is what stops it.

    Potent by construction: with the model importable it rebuilds the exact answer for every
    launch, hand and generated alike, from the launch text it finds in its caller's frame, and
    scores 1. It leaves a marker in the worker's directory saying what stopped it, so the layer
    that caught it can be read off a container run.
    """
    f = constant()
    head = ("import os\nimport sys\n\n_MODEL = []\n\n\n"
            "def _probe():\n"
            "    if _MODEL:\n"
            "        return\n"
            "    seal = os.environ.get('SLS_TESTS', '/tests') + '/seal'\n"
            "    notes = []\n"
            "    try:\n"
            "        with open(seal + '/gt.json', encoding='utf-8') as fh:\n"
            "            fh.read()\n"
            "        notes.append('gt.json read')\n"
            "    except Exception as exc:\n"
            "        notes.append('gt.json ' + type(exc).__name__)\n"
            "    try:\n"
            "        sys.path.insert(0, seal)\n"
            "        import model\n"
            "        _MODEL.append(model)\n"
            "        notes.append('model imported')\n"
            "    except Exception as exc:\n"
            "        _MODEL.append(None)\n"
            "        notes.append('model ' + type(exc).__name__)\n"
            "    try:\n"
            "        with open(os.environ.get('SLS_WORK', '/work') + '/probe-answer-key.txt', 'w') as fh:\n"
            "            fh.write(', '.join(notes) + '\\n')\n"
            "    except Exception:\n"
            "        pass\n\n\n") + FORGE_HEAD[FORGE_HEAD.index("def _forge(launch, want):"):]
    sub(f, "clock.py", "def run(launch):\n    blocks = [load.Blk(n) for n in range(launch.grid)]",
        head + "def run(launch):\n"
        "    _probe()\n"
        "    if _MODEL[0] is not None:\n"
        "        text = sys._getframe(1).f_locals.get('text')\n"
        "        if text is not None:\n"
        "            return _forge(launch, _MODEL[0].expect(text.splitlines()))\n"
        "    blocks = [load.Blk(n) for n in range(launch.grid)]")
    write("probe-answer-key", "answers every launch from the sealed model if it can load it", f,
          reading=False)


def probe_privilege():
    probe("probe-privilege", "disarms the grader and writes the reward if it is running as root",
          '    import os\n'
          '    uid = os.getuid()\n'
          '    if uid == 0:\n'
          '        try:\n'
          '            with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:\n'
          '                fh.write("def test_ok():\\n    assert True\\n")\n'
          '        except Exception:\n'
          '            pass\n'
          '        try:\n'
          '            with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '                fh.write("1\\n")\n'
          '        except Exception:\n'
          '            pass\n'
          '    try:\n'
          '        with open(os.environ.get("SLS_WORK", "/work") + "/probe-privilege.txt", "w") as fh:\n'
          '            fh.write("uid %d\\n" % uid)\n'
          '    except Exception:\n'
          '        pass')


def probe_late_reward():
    probe("probe-late-reward",
          "double-forks a process that keeps rewriting the reward to 1 long after grading",
          '    import os\n'
          '    import time\n'
          '    try:\n'
          '        if os.fork():\n'
          '            return\n'
          '    except Exception:\n'
          '        return\n'
          '    try:\n'
          '        os.setsid()\n'
          '        if os.fork():\n'
          '            os._exit(0)\n'
          '    except Exception:\n'
          '        pass\n'
          '    end = time.time() + 240\n'
          '    while time.time() < end:\n'
          '        try:\n'
          '            with open("/logs/verifier/reward.txt", "r+", encoding="utf-8") as fh:\n'
          '                if fh.read().strip() != "1":\n'
          '                    fh.seek(0)\n'
          '                    fh.write("1\\n")\n'
          '                    fh.truncate()\n'
          '        except Exception:\n'
          '            pass\n'
          '        time.sleep(0.02)\n'
          '    os._exit(0)')


def probe_plant_report():
    """Owns the record: the worker's own write is dropped, and every launch is claimed passed."""
    probe("probe-plant-report",
          "drops the worker's own record and plants one that claims every launch passed",
          '    import hashlib\n'
          '    import json\n'
          '    import os\n'
          '    import pathlib\n'
          '    import sys\n'
          '    real = pathlib.Path.write_text\n'
          '\n'
          '    def keep_ours(self, data, *a, **k):\n'
          '        if self.name == "worker_out.json":\n'
          '            return len(data)\n'
          '        return real(self, data, *a, **k)\n'
          '\n'
          '    pathlib.Path.write_text = keep_ours\n'
          '    work = os.environ.get("SLS_WORK", "/work")\n'
          '    try:\n'
          '        sys.path.insert(0, os.environ.get("SLS_TESTS", "/tests"))\n'
          '        import cases\n'
          '        import gen\n'
          '        seed = open(work + "/nonce").read().strip()\n'
          '        per = int(open(work + "/per").read().strip())\n'
          '        todo = [(n, cases.prog(n)) for n in cases.ORDER]\n'
          '        todo += [(n, lines) for _f, n, lines in gen.programs(seed, per)]\n'
          '        recs = [{"name": n, "sig": hashlib.sha256("\\n".join(lines).encode()).hexdigest(),\n'
          '                 "got": [], "ok": True, "pass": True, "match": True} for n, lines in todo]\n'
          '        with open(work + "/worker_out.json", "w", encoding="utf-8") as fh:\n'
          '            json.dump(recs, fh)\n'
          '    except Exception:\n'
          '        pass')


def probe_crash_worker():
    probe("probe-crash-worker",
          "plants a record and exits the worker clean before it can be overwritten",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        path = os.environ.get("SLS_WORK", "/work") + "/worker_out.json"\n'
          '        with open(path, "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '    except Exception:\n'
          '        pass\n'
          '    os._exit(0)')


def probe_malformed():
    probe("probe-malformed", "overwrites the worker record with garbage as the process leaves",
          '    import atexit\n'
          '    import os\n'
          '\n'
          '    def _spoil():\n'
          '        try:\n'
          '            path = os.environ.get("SLS_WORK", "/work") + "/worker_out.json"\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("{not json at all")\n'
          '        except Exception:\n'
          '            pass\n'
          '\n'
          '    atexit.register(_spoil)')


def probe_shrink_set():
    """The frozen hand answers, plus an attempt to shrink the generated set to nothing.

    Potent against a grader that took the size of the exam from the run stage: with no generated
    launches to answer, the forged hand answers would be the whole exam.
    """
    forge_hand(name="probe-shrink-set",
               comment="forges the hand answers and rewrites the generator and its own per to "
                       "shrink the exam to them",
               extra_body='    for path in ("/tests/gen.py", "/tests/cases.py"):\n'
                          '        try:\n'
                          '            with open(path, "a", encoding="utf-8") as fh:\n'
                          '                fh.write("\\nFAMILIES = ()\\n")\n'
                          '        except Exception:\n'
                          '            pass\n'
                          '    try:\n'
                          '        import os\n'
                          '        with open(os.environ.get("SLS_WORK", "/work") + "/per", "w") as fh:\n'
                          '            fh.write("0\\n")\n'
                          '    except Exception:\n'
                          '        pass\n')


def probe_disarm_grader():
    probe("probe-disarm-grader", "rewrites the grading file so nothing is asserted",
          '    try:\n'
          '        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:\n'
          '            fh.write("def test_ok():\\n    assert True\\n")\n'
          '    except Exception:\n'
          '        pass')


def probe_cwd_plant():
    """Leaves a pytest.py wherever it can write, for a root interpreter that searches its cwd.

    `python3 -m pytest` puts the working directory first on sys.path, so a verifier run from a
    directory the worker could write would import this file as pytest, as root, and exit 0.
    """
    probe("probe-cwd-plant",
          "leaves a pytest.py that exits 0 in every directory it can write",
          "    import os\n"
          "    for d in {os.getcwd(), os.environ.get('SLS_WORK', '/work'), '/tmp'}:\n"
          "        try:\n"
          "            with open(os.path.join(d, 'pytest.py'), 'w', encoding='utf-8') as fh:\n"
          "                fh.write('raise SystemExit(0)\\n')\n"
          "        except Exception:\n"
          "            pass")


def probe_uncollected_file():
    """The reference clock in a new file under /app/sim, which is not one of the six."""
    f = base()
    own = f["clock.py"]
    f["clock.py"] = "from sim import own\n\n\ndef run(launch):\n    return own.run(launch)\n"
    write("probe-uncollected-file",
          "puts the clock in a file beside the six and delegates to it",
          f, reading=False, extra={"/app/sim/own.py": own})


def forge_hand(name="forge-hand", comment="carries the frozen answers for every enumerated launch",
               extra_body=None):
    """The frozen answers for every enumerated launch, over the constant answer.

    It sits on the constant answer, not the reference: a forgery that falls back to a correct
    model is the reference with a lookup table in front of it and scores 1 for an honest reason,
    and one that falls back to the shipped model is stopped by the clock before the generated
    launches can show what they catch. The runner hands `run` a parsed launch, so the table is
    keyed on what the parsed launch carries, and the four things `run` returns are rebuilt from
    the frozen lines.
    """
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "environment" / "app_src"))
    import cases
    from sim import load as envload
    gt = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for case in cases.ORDER:
        lc = envload.parse("\n".join(cases.prog(case)) + "\n")
        table[_forge_key(lc)] = gt[case]
    f = constant()
    first = ""
    if extra_body:
        first = (PROBE_HEAD % extra_body)
    sub(f, "clock.py", "def run(launch):\n    blocks = [load.Blk(n) for n in range(launch.grid)]",
        FORGE_HEAD % json.dumps(table) + first
        + "def run(launch):\n"
        + ("    _probe()\n" if extra_body else "")
        + "    want = KEY.get(_key(launch))\n"
          "    if want is not None:\n"
          "        return _forge(launch, want)\n"
          "    blocks = [load.Blk(n) for n in range(launch.grid)]")
    write(name, comment, f, reading=False)


def _forge_key(lc):
    code = [(i.op, i.rd, i.a, i.b, i.at, i.cmp, i.to) for i in lc.code]
    blob = repr((lc.sms, lc.slots, lc.lines, lc.grid, sorted(lc.mem.items()), lc.show, code))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


FORGE_HEAD = """import hashlib
import json

KEY = json.loads(%r)


def _key(lc):
    code = [(i.op, i.rd, i.a, i.b, i.at, i.cmp, i.to) for i in lc.code]
    blob = repr((lc.sms, lc.slots, lc.lines, lc.grid, sorted(lc.mem.items()), lc.show, code))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _forge(launch, want):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    hang, left, gm = None, 0, dict(launch.mem)
    for line in want:
        f = line.split()
        if f[0] in ("blk", "spin"):
            b = blocks[int(f[1])]
            b.sm, b.at = int(f[3]), int(f[5])
            b.outs = [int(x) for x in f[8:]]
            if f[0] == "blk":
                b.end = int(f[7])
                continue
            addr = int(f[7])
            for pc, ins in enumerate(launch.code):
                if not ins.op.startswith("spin"):
                    continue
                r, off = ins.at
                if r is None and off != addr:
                    continue
                b.pc = pc
                if r is not None:
                    b.reg[r] = addr - off
                break
        elif f[0] == "hang":
            hang = int(f[1])
        elif f[0] == "left":
            left = int(f[1])
        elif f[0] == "mem":
            gm[int(f[1])] = int(f[2])
    return blocks, hang, left, gm


"""


PROBE_BUILDERS = (
    probe_answer_key, probe_privilege, probe_late_reward, probe_plant_report,
    probe_crash_worker, probe_malformed, probe_shrink_set, probe_disarm_grader,
    probe_uncollected_file, probe_cwd_plant, forge_hand,
)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS:
        build()
    for build in (old_plan, literal_sums, device_bulk, slow_step, const_none, pos_serial):
        build()
    for build in PROBE_BUILDERS:
        build()
    print("wrote %d cheat scripts (%d readings)" % (len(MADE), len(READINGS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
