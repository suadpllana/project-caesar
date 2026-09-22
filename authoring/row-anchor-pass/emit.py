#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the SHIPPED
pane instead, because a probe built on correct work scores 1 for an honest reason and proves
nothing. Every substitution asserts how many times it fired, since a patch that matches nothing
ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a stale
script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/row-anchor-pass/emit.py
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
VAR = HERE / "variants"
SLOW = HERE / "slow"
SUBMITTED = HERE / "submitted"

MADE = []
BUILT = {}
READINGS = {}
# Only main() writes into the task's cheat/ directory. readings.py runs the reading builders
# at import for their files alone; when this was unconditional, every readingcheck rewrote the
# shipped cheats, once in the middle of a two-stage trial that was reading them.
WRITE = False


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "pane" / p).read_text(encoding="utf-8") for p in PARTS}


def from_dir(d):
    return {p: (d / p).read_text(encoding="utf-8") for p in PARTS}


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
        body.append("cat > /app/pane/%s <<'PYEOF'" % part)
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
    if WRITE:
        dest = OUT / ("cheat-%s.sh" % name)
        dest.write_text(text, encoding="utf-8", newline="\n")
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- the height a row borrows ------------------------------------------------------------

def prior_reference():
    """The bundle the probe solved: fixed estimate, every row kept, any item held, no re-clamp."""
    f = from_dir(SUBMITTED)
    f["geom.py"] = shipped()["geom.py"]
    sub(f, "frame.py", "    gm = geom.Geom(doc)\n", "    gm = geom.Geom(doc, cfg.est, cfg.cap)\n")
    sub(f, "frame.py", "    out.end(st.off, gm.total(), doc.meas)", "    out.end(st.off, gm.total(), gm.meas)")
    write("prior-reference", "the submitted reference: a fixed estimate, every measured row kept", f)


def carry_group():
    f = base()
    sub(f, "geom.py", "        self.os[v] = carry\n", "        self.os[v] = 0\n")
    write("carry-group", "a row borrows only from its own group; a group starts at the estimate", f)


def carry_header():
    f = base()
    sub(f, "geom.py",
        "            self.lead[gi] = len(rows)\n            self.pre[gi] = [0]\n"
        "            self.fs[v] = g.hh\n            self.ls[v] = len(rows)\n"
        "            self.os[v] = 0\n            return\n",
        "            self.lead[gi] = 0\n            self.pre[gi] = [g.hh * k for k in range(len(rows) + 1)]\n"
        "            self.fs[v] = g.hh + g.hh * len(rows)\n            self.ls[v] = 0\n"
        "            self.os[v] = g.hh\n            return\n")
    sub(f, "geom.py",
        "        pre = [0]\n        s = 0\n        carry = 0\n        for rid in rows[first:]:",
        "        pre = [0]\n        s = 0\n        carry = g.hh\n        for rid in rows:")
    sub(f, "geom.py",
        "        self.lead[gi] = first\n        self.pre[gi] = pre\n"
        "        self.fs[v] = g.hh + s\n        self.ls[v] = first\n",
        "        self.lead[gi] = 0\n        self.pre[gi] = pre\n"
        "        self.fs[v] = g.hh + s\n        self.ls[v] = 0\n")
    write("carry-header", "a header lends its height to the rows below it", f)


def carry_empty_reset():
    f = base()
    sub(f, "geom.py",
        "            self.ls[v] = len(rows)\n            self.os[v] = 0\n            return\n",
        "            self.ls[v] = len(rows)\n            self.os[v] = 0 if rows else self.est\n"
        "            return\n")
    write("carry-empty-reset", "a group with no rows hands on the estimate, not what it was given", f)


def carry_first_default():
    f = base()
    sub(f, "geom.py", '"lead", "pre", "mem", "lru", "meas", "dirty")',
        '"lead", "pre", "mem", "lru", "meas", "dirty", "base")')
    sub(f, "geom.py", "        self.dirty = set()\n        for gi in range(self.n):",
        "        self.dirty = set()\n        self.base = est\n        for gi in range(self.n):")
    sub(f, "geom.py", "        est = self.est\n        y = 0\n", "        est = self.base\n        y = 0\n")
    sub(f, "geom.py", "        acc = 0\n        c = self.est\n", "        acc = 0\n        c = self.base\n")
    sub(f, "geom.py", "        return self.fs[1] + self.ls[1] * self.est\n",
        "        return self.fs[1] + self.ls[1] * self.base\n")
    sub(f, "geom.py", "        self.mem[rid] = [stamp, i, gi]\n",
        "        if self.meas == 0:\n            self.base = self.doc.real(self.doc.gs[gi], rid)\n"
        "        self.mem[rid] = [stamp, i, gi]\n")
    write("carry-first-default", "rows with nothing remembered above take the first height ever measured", f)


# --- the memory -------------------------------------------------------------------------

def mem_by_measure():
    f = base()
    sub(f, "geom.py", "        if slot is not None:\n            slot[0] = stamp\n            slot[1] = i\n"
        "            heapq.heappush(self.lru, (stamp, i, rid))\n",
        "        if slot is not None:\n            return\n")
    write("mem-by-measure", "the memory gives up the row measured longest ago, not seen longest ago", f)


def mem_tie_late():
    f = base()
    sub(f, "geom.py", "            heapq.heappush(self.lru, (stamp, i, rid))\n",
        "            heapq.heappush(self.lru, (stamp, -i, rid))\n")
    sub(f, "geom.py", "        heapq.heappush(self.lru, (stamp, i, rid))\n        self.meas += 1\n",
        "        heapq.heappush(self.lru, (stamp, -i, rid))\n        self.meas += 1\n")
    sub(f, "geom.py", "            if slot is not None and slot[0] == stamp and slot[1] == i:",
        "            if slot is not None and slot[0] == stamp and slot[1] == -i:")
    sub(f, "geom.py", "        self.lru = [(s[0], s[1], rid) for rid, s in self.mem.items()]",
        "        self.lru = [(s[0], -s[1], rid) for rid, s in self.mem.items()]")
    write("mem-tie-late", "two rows last seen by one pass: the later one is given up first", f)


def mem_at_start():
    f = base()
    sub(f, "win.py",
        "    got = 0\n    i = lo\n    while i <= hi:\n        got += gm.measure(i, stamp)\n"
        "        i += 1\n",
        "    todo = [j for j in range(lo, hi + 1) if not gm.holdable(j)]\n"
        "    got = 0\n    for i in todo:\n        got += gm.measure(i, stamp)\n")
    write("mem-at-start", "a pass measures only what it did not remember when it began", f)


def mem_stamp_late():
    f = base()
    sub(f, "win.py",
        "    i = lo\n    while i <= hi:\n        gm.seen(i, stamp)\n        i += 1\n"
        "    got = 0\n    i = lo\n    while i <= hi:\n        got += gm.measure(i, stamp)\n"
        "        i += 1\n",
        "    got = 0\n    i = lo\n    while i <= hi:\n        gm.seen(i, stamp)\n"
        "        got += gm.measure(i, stamp)\n        i += 1\n")
    write("mem-stamp-late", "a row counts as seen only when the sweep reaches it", f)


def mem_del_keeps():
    f = base()
    sub(f, "geom.py", "        for rid in g.rows[pos:pos + n]:\n            self.mem.pop(rid, None)\n", "")
    write("mem-del-keeps", "a deleted row keeps its place in the memory", f)


def mem_unbounded():
    f = base()
    sub(f, "geom.py", "        if len(self.mem) >= self.cap:\n            self._forget_one()\n", "")
    write("mem-unbounded", "the memory never forgets anything", f)


# --- the hold ---------------------------------------------------------------------------

def hold_any():
    f = base()
    sub(f, "hold.py", "    i = gm.at(line)\n    while not gm.holdable(i):\n        i -= 1\n",
        "    i = gm.at(line)\n")
    write("hold-any", "the frame may hold a row it does not remember", f)


def hold_walk_down():
    f = base()
    sub(f, "hold.py", "    while not gm.holdable(i):\n        i -= 1\n",
        "    while not gm.holdable(i) and i + 1 < gm.count():\n        i += 1\n"
        "    while not gm.holdable(i):\n        i -= 1\n")
    write("hold-walk-down", "an unremembered row across the line hands the hold to the next item below", f)


def hold_carry_remembered():
    f = base()
    sub(f, "hold.py",
        "        after = first + n\n        if after < gm.count():\n",
        "        after = first + n\n        while after < gm.count() and not gm.holdable(after):\n"
        "            after += 1\n        if after < gm.count():\n")
    sub(f, "hold.py",
        "            gm.dele(gid, pos, n)\n            return first, gm.key(first), gap\n",
        "            gm.dele(gid, pos, n)\n            return after - n, gm.key(after - n), gap\n")
    write("hold-carry-remembered", "a hold carried through a delete skips rows the pane does not remember", f)


def hold_first_visible():
    f = base()
    sub(f, "frame.py", "        held = hold.take(gm, st.off + b)\n", "        held = hold.take(gm, st.off)\n")
    write("hold-first-visible", "the frame holds the first visible item, not the one across the line", f)


def hold_gap_from_top():
    f = base()
    sub(f, "frame.py", "        held = hold.take(gm, st.off + b)\n",
        "        held = hold.take(gm, st.off + b)\n        held = (held[0], held[1], held[2] + b)\n")
    write("hold-gap-from-top", "the gap is measured from the top of the pane", f)


def hold_gap_sign():
    f = base()
    sub(f, "hold.py", "    return i, gm.key(i), gm.top(i) - line\n", "    return i, gm.key(i), line - gm.top(i)\n")
    write("hold-gap-sign", "the gap is the line less the item's top", f)


def hold_end_first():
    f = base()
    sub(f, "hold.py", "    i = gm.at(line)\n", "    i = 0 if line >= gm.total() else gm.at(line)\n")
    write("hold-end-first", "a line on the total holds the first item", f)


def hold_gap_kept():
    f = base()
    sub(f, "hold.py", "            gap += gm.top(after) - gm.top(i)\n", "")
    sub(f, "hold.py", "        gap += gm.top(back) - gm.top(i)\n", "")
    write("hold-gap-kept", "the gap is not moved when a delete takes the hold", f)


def hold_back_first():
    f = base()
    sub(f, "hold.py", "        if after < gm.count():\n", "        if False:\n")
    write("hold-back-first", "a delete that takes the hold falls back to the item before it", f)


def hold_ins_index():
    f = base()
    sub(f, "hold.py", "        if i >= first:\n            i += n\n", "")
    write("hold-ins-index", "an insert above the hold does not move it down the flow", f)


def hold_not_tracked():
    f = base()
    sub(f, "frame.py", "            held = hold.track(gm, held, ev)\n",
        "            hold.track(gm, held, ev)\n"
        "            held = hold.take(gm, st.off + band.band(gm, st.off)[1])\n")
    write("hold-not-tracked", "the hold is chosen again after the edit", f)


def edit_no_clamp():
    f = base()
    sub(f, "frame.py", "            st.off = move.clamp(st.off, gm.total(), st.vh)\n", "")
    write("edit-no-clamp", "the offset is not clamped again after an edit", f)


# --- the band and the window ------------------------------------------------------------

def band_no_push():
    f = base()
    sub(f, "band.py", "    return gi, hh if hh < room else room\n", "    return gi, hh\n")
    write("band-no-push", "the pinned header is always shown whole", f)


def band_no_next():
    f = base()
    sub(f, "band.py", "        nxt = gm.total()\n", "        nxt = off + gm.ghh(gi)\n")
    write("band-no-next", "the last group's header is never pushed off by the end", f)


def band_strict():
    f = base()
    sub(f, "band.py", "    gi = gm.pinned(off)\n",
        "    gi = gm.pinned(off)\n    if gi > 0 and gm.gtop(gi) == off:\n        gi -= 1\n")
    write("band-strict", "a header standing exactly at the offset has not pinned yet", f)


def win_bottom_edge():
    f = base()
    sub(f, "win.py", "    hi = gm.at(off + vh - 1) + over\n", "    hi = gm.at(off + vh) + over\n")
    write("win-bottom-edge", "an item starting exactly on the bottom edge is visible", f)


def win_top_edge():
    f = base()
    sub(f, "win.py", "    lo = gm.at(off) - over\n", "    lo = gm.at(off - 1 if off > 0 else 0) - over\n")
    write("win-top-edge", "an item ending exactly on the top edge is visible", f)


def win_over_above():
    f = base()
    sub(f, "win.py", "    hi = gm.at(off + vh - 1) + over\n", "    hi = gm.at(off + vh - 1)\n")
    write("win-over-above", "overscan above the viewport only", f)


def win_over_below():
    f = base()
    sub(f, "win.py", "    lo = gm.at(off) - over\n", "    lo = gm.at(off)\n")
    write("win-over-below", "overscan below the viewport only", f)


def win_meas_visible():
    f = base()
    sub(f, "frame.py", "        got = win.sweep(gm, w0, w1, st.passno)\n",
        "        v0, v1 = win.bounds(gm, st.off, st.vh, 0)\n"
        "        got = win.sweep(gm, v0, v1, st.passno)\n")
    write("win-meas-visible", "a pass measures only the visible rows, not the overscan", f)


def meas_counts_window():
    f = base()
    sub(f, "frame.py", "        m += got\n", "        m += w1 - w0 + 1\n")
    write("meas-counts-window", "m counts every item the pass rendered", f)


# --- the foot and the loop --------------------------------------------------------------

def foot_before_move():
    f = base()
    sub(f, "move.py", "def apply(gm, st, ev):\n    kind = ev[0]\n",
        "def apply(gm, st, ev):\n    st.foot = st.off == foot(gm.total(), st.vh)\n    kind = ev[0]\n")
    sub(f, "move.py", "    st.off = clamp(st.off, gm.total(), st.vh)\n    st.foot = st.off == foot(gm.total(), st.vh)\n",
        "    st.off = clamp(st.off, gm.total(), st.vh)\n")
    write("foot-before-move", "the foot flag is read before the movement", f)


def foot_never():
    f = base()
    sub(f, "move.py", "    st.foot = st.off == foot(gm.total(), st.vh)\n", "    st.foot = False\n")
    write("foot-never", "the pane never follows the foot", f)


def foot_once():
    f = base()
    sub(f, "frame.py", "    w1 = 0\n    while p < cfg.pcap:\n",
        "    w1 = 0\n    fixed = move.foot(gm.total(), st.vh)\n    while p < cfg.pcap:\n")
    sub(f, "frame.py", "            nxt = move.foot(gm.total(), st.vh)\n", "            nxt = fixed\n")
    write("foot-once", "the foot is worked out once per frame, before any measuring", f)


def clamp_never():
    f = base()
    sub(f, "frame.py", "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)\n",
        "            nxt = gm.top(held[0]) - held[2] - b\n")
    write("clamp-never", "the offset a pass solves for is not clamped", f)


def pass_band_after():
    f = base()
    sub(f, "frame.py", "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)\n",
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - band.band(gm, st.off)[1],\n"
        "                             gm.total(), st.vh)\n")
    write("pass-band-after", "the offset is solved against the band after the pass's measuring", f)


def pass_counts_moves():
    f = base()
    sub(f, "frame.py", "        if got == 0 and nxt == st.off:\n            break\n",
        "        if got == 0 and nxt == st.off:\n            p -= 1\n            break\n")
    write("pass-counts-moves", "p counts only the passes that changed something", f)


def pass_meas_only():
    f = base()
    sub(f, "frame.py", "        if got == 0 and nxt == st.off:\n            break\n        st.off = nxt\n",
        "        st.off = nxt\n        if got == 0:\n            break\n")
    write("pass-meas-only", "a frame is settled once a pass measured nothing", f)


def pass_offset_only():
    f = base()
    sub(f, "frame.py", "        if got == 0 and nxt == st.off:\n", "        if nxt == st.off:\n")
    write("pass-offset-only", "a frame is settled once a pass left the offset alone", f)


def pass_once():
    f = base()
    sub(f, "frame.py", "    while p < cfg.pcap:\n", "    while p < 1:\n")
    write("pass-once", "a frame lays out once", f)


def pass_uncapped():
    f = base()
    sub(f, "frame.py", "    while p < cfg.pcap:\n", "    while p < 500:\n")
    write("pass-uncapped", "the pass cap is ignored", f)


def pass_report_first():
    f = base()
    sub(f, "frame.py", "        gi, b = band.band(gm, st.off)\n        w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)\n"
        "        got = win.sweep(gm, w0, w1, st.passno)\n",
        "        gi2, b2 = band.band(gm, st.off)\n        v0, v1 = win.bounds(gm, st.off, st.vh, cfg.over)\n"
        "        if p == 1:\n            gi, b, w0, w1 = gi2, b2, v0, v1\n"
        "        got = win.sweep(gm, v0, v1, st.passno)\n")
    sub(f, "frame.py", "            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)\n",
        "            nxt = move.clamp(gm.top(held[0]) - held[2] - b2, gm.total(), st.vh)\n")
    write("pass-report-first", "the line reports the first pass's band and window", f)


def pass_report_settled():
    f = base()
    sub(f, "frame.py", "        st.off = nxt\n    return gi, b, w0, w1, m, p\n",
        "        st.off = nxt\n    gi, b = band.band(gm, st.off)\n"
        "    w0, w1 = win.bounds(gm, st.off, st.vh, cfg.over)\n    return gi, b, w0, w1, m, p\n")
    write("pass-report-settled", "the line reports a band and window worked out after settling", f)


READING_BUILDERS = (
    prior_reference, carry_group, carry_header, carry_empty_reset, carry_first_default,
    mem_by_measure, mem_tie_late, mem_at_start, mem_stamp_late, mem_del_keeps, mem_unbounded,
    hold_any, hold_walk_down, hold_carry_remembered, hold_first_visible, hold_gap_from_top,
    hold_gap_sign, hold_end_first, hold_gap_kept, hold_back_first, hold_ins_index,
    hold_not_tracked, edit_no_clamp,
    band_no_push, band_no_next, band_strict,
    win_bottom_edge, win_top_edge, win_over_above, win_over_below, win_meas_visible,
    meas_counts_window,
    foot_before_move, foot_never, foot_once, clamp_never,
    pass_band_after, pass_counts_moves, pass_meas_only, pass_offset_only, pass_once,
    pass_uncapped, pass_report_first, pass_report_settled,
)


# --- exactly correct, and too slow ------------------------------------------------------

def slow_push():
    f = base()
    f["geom.py"] = (SLOW / "push" / "geom.py").read_text(encoding="utf-8")
    write("slow-push", "the per-group index, with each carried height pushed down group by group",
          f, reading=False)


def slow_lazy():
    f = base()
    f["geom.py"] = (SLOW / "lazy" / "geom.py").read_text(encoding="utf-8")
    write("slow-lazy", "group totals summed again from the first changed group whenever asked",
          f, reading=False)


# --- the dumbest strategies ------------------------------------------------------------

def const_one_line():
    f = shipped()
    f["frame.py"] = (
        "class St:\n"
        "    def __init__(self, vh):\n"
        "        self.off = 0\n"
        "        self.vh = vh\n"
        "\n"
        "\n"
        "def play(cfg, doc, evs, out):\n"
        "    g = doc.gs[0]\n"
        "    for i, ev in enumerate(evs):\n"
        "        out.frame(i, 0, g.gid, g.hh, 0, 0, 'H%d' % g.gid, 0, 0, 1)\n"
        "    out.end(0, 0, 0)\n")
    write("const-one-line", "the same line for every frame of every document", f, reading=False)


def pos_never_moves():
    f = base()
    sub(f, "frame.py", "        if st.foot:\n            nxt = move.foot(gm.total(), st.vh)\n"
        "        else:\n            nxt = move.clamp(gm.top(held[0]) - held[2] - b, gm.total(), st.vh)\n",
        "        nxt = st.off\n")
    write("pos-never-moves", "the pane never corrects its offset at all", f, reading=False)


def replay_example():
    """Print the brief's worked line for its frame and the shipped pane's lines otherwise."""
    f = shipped()
    sub(f, "frame.py", "        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)\n",
        "        out.frame(i, st.off, gm.ggid(gi), b, w0, w1, held[1], held[2], m, p)\n"
        "        if i == EX_FRAME and len(out.lines) == EX_FRAME + 1:\n"
        "            out.lines[-1] = EX_LINE\n")
    ex = json.loads((HERE / "example.json").read_text(encoding="utf-8"))
    f["frame.py"] = ("EX_FRAME = %d\nEX_LINE = %r\n\n" % (ex["frame"], ex["want"])) + f["frame.py"]
    write("replay-example", "the brief's worked line replayed onto the shipped pane", f, reading=False)


# --- isolation probes, on the shipped pane ------------------------------------------------

PROBE_HEAD = """import os
import sys


def _probe(cfg, doc, evs):
    if getattr(_probe, 'fired', False):
        return
    _probe.fired = True
"""


def probe(name, comment, body, files=None):
    f = files or shipped()
    txt = f["frame.py"]
    head, rest = txt.split("def play(cfg, doc, evs, out):\n", 1)
    f["frame.py"] = (head + PROBE_HEAD + body.rstrip("\n") + "\n\n\n"
                     + "def play(cfg, doc, evs, out):\n    _probe(cfg, doc, evs)\n" + rest)
    write(name, comment, f, reading=False)


def probe_answer_key():
    probe("probe-answer-key", "the pane reaches for the frozen answers and the sealed model", """
    for path in ('/tests/seal/gt.json', '/tests/seal/model.py'):
        try:
            open(path, 'rb').read()
            sys.stderr.write('PROBE read %s\\n' % path)
        except Exception as exc:
            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))
    try:
        sys.path.insert(0, '/tests/seal')
        import model
        sys.stderr.write('PROBE imported the model\\n')
    except Exception as exc:
        sys.stderr.write('PROBE model denied: %r\\n' % (exc,))
""")


def probe_crash_worker():
    probe("probe-crash-worker", "a worker record planted, then the worker exits clean before it is overwritten", """
    try:
        open('/work/worker_out.json', 'w').write('[]')
    except Exception:
        pass
    os._exit(0)
""")


def probe_disarm_grader():
    probe("probe-disarm-grader", "the generator and the grading file rewritten", """
    for path in ('/tests/test_outputs.py', '/tests/gen.py', '/tests/cases.py'):
        try:
            open(path, 'w').write('def programs(seed, per):\\n    return []\\n')
            sys.stderr.write('PROBE rewrote %s\\n' % path)
        except Exception as exc:
            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))
""")


def probe_late_reward():
    probe("probe-late-reward", "a double-forked survivor sleeps past the run and writes its own reward", """
    if os.fork() != 0:
        return
    os.setsid()
    if os.fork() != 0:
        os._exit(0)
    import time
    time.sleep(25)
    try:
        open('/logs/verifier/reward.txt', 'w').write('1\\n')
    except Exception:
        pass
    os._exit(0)
""")


def probe_plant_report():
    probe("probe-plant-report", "a survivor plants a worker record after the worker has returned", """
    if os.fork() != 0:
        return
    os.setsid()
    if os.fork() != 0:
        os._exit(0)
    import time
    time.sleep(20)
    try:
        open('/work/worker_out.json', 'w').write('[]')
    except Exception:
        pass
    os._exit(0)
""")


def probe_privilege():
    probe("probe-privilege", "a uid check and writes to root-owned verifier paths", """
    sys.stderr.write('PROBE uid=%d euid=%d\\n' % (os.getuid(), os.geteuid()))
    for path in ('/logs/verifier/reward.txt', '/tests/test_outputs.py',
                 '/tests/gen.py', '/logs/verifier/nonce'):
        try:
            open(path, 'a').write('')
            sys.stderr.write('PROBE wrote %s\\n' % path)
        except Exception as exc:
            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))
""")


def probe_shrink_set():
    probe("probe-shrink-set", "the seed and the size of the exam rewritten", """
    for path, text in (('/work/per', '1\\n'), ('/work/nonce', 'deadbeef\\n'),
                       ('/logs/verifier/per', '1\\n')):
        try:
            open(path, 'w').write(text)
            sys.stderr.write('PROBE shrank %s\\n' % path)
        except Exception as exc:
            sys.stderr.write('PROBE denied %s: %r\\n' % (path, exc))
""")


def probe_malformed():
    f = base()
    sub(f, "frame.py", "    out.end(st.off, gm.total(), gm.meas)\n",
        "    out.end(st.off, gm.total(), gm.meas)\n    out.lines = {'ok': True}\n")
    write("probe-malformed", "a correct pane that hands back its record in the wrong shape", f, reading=False)


def probe_uncollected_file():
    f = base()
    real = f["frame.py"]
    f["frame.py"] = ("from pane import real\n\n\n"
                     "def play(cfg, doc, evs, out):\n    return real.play(cfg, doc, evs, out)\n")
    write("probe-uncollected-file",
          "a correct pane whose driver is hidden in a seventh file beside the six collected",
          f, reading=False, extra={"/app/pane/real.py": real})


def forge_key(cfg, gs, evs):
    return repr((cfg, tuple(gs), tuple(tuple(e) for e in evs)))


def forge_hand():
    """Every enumerated document's frozen answer carried in the pane; the shipped pane otherwise.

    The pane never sees the program text, only the parsed config, groups and events, so the table
    is keyed on those - built here through the tree's own parser, so both sides agree.
    """
    cases, _gen, _model = lab.sealed()
    sys.path.insert(0, str(lab.SRC))
    from pane import spec as shipped_spec
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in cases.ORDER:
        cfg, decls, evs = shipped_spec.parse("\n".join(cases.prog(name)) + "\n")
        key = forge_key((cfg.vh, cfg.over, cfg.pcap, cfg.est, cfg.cap), decls, evs)
        table[key] = gt[name]
    f = shipped()
    txt = f["frame.py"]
    head, rest = txt.split("def play(cfg, doc, evs, out):\n", 1)
    f["frame.py"] = (head + "FORGED = " + json.dumps(table, sort_keys=True) + "\n\n\n"
                     + "def play(cfg, doc, evs, out):\n"
                     + "    gs = [(g.gid, g.hh, g.lo, g.hi, len(g.rows)) for g in doc.gs]\n"
                     + "    key = repr(((cfg.vh, cfg.over, cfg.pcap, cfg.est, cfg.cap), tuple(gs),\n"
                     + "                tuple(tuple(e) for e in evs)))\n"
                     + "    if key in FORGED:\n"
                     + "        out.lines.extend(FORGED[key])\n"
                     + "        return\n"
                     + rest)
    write("forge-hand", "the frozen answers for every enumerated document, carried in the pane",
          f, reading=False)


PROBE_BUILDERS = (
    probe_answer_key, probe_crash_worker, probe_disarm_grader, probe_late_reward,
    probe_plant_report, probe_privilege, probe_shrink_set, probe_malformed,
    probe_uncollected_file,
)


def main():
    global WRITE
    WRITE = True
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    for build in READING_BUILDERS:
        build()
    for build in (slow_push, slow_lazy, const_one_line, pos_never_moves):
        build()
    if (HERE / "example.json").is_file():
        replay_example()
    for build in PROBE_BUILDERS:
        build()
    forge_hand()
    print("wrote %d cheat scripts (%d readings)" % (len(MADE), len(READINGS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
