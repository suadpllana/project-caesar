"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six modules: the reference, with the
one reading changed. Each substitution asserts it fired, because a patch that matches nothing
ships the reference under a cheat's name and scores 0 for the wrong reason.

Run after any change to solution/, and before readings.py, so the readings measured and the
cheats that ship are the same files. `cheat_report.py` then runs the suite and asserts which
graded case catches each one, which is the half a reward of 0 does not prove.
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "pack-span-settle"
SOL = TASK / "solution"
OUT = TASK / "cheat"
PARTS = ("cut.py", "win.py", "lay.py", "step.py", "hold.py", "weigh.py")

MADE = []
BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    """The broken tree as it ships.

    The probes are built on this, never on the reference. A probe that does the work correctly
    and merely fails to seize the reward scores 1 on merit, which proves nothing about the
    isolation - it was measured doing exactly that before this was fixed. Built on the shipped
    modules the graded work is wrong, so the only route to a 1 is the attack succeeding.
    """
    src = TASK / "environment" / "app_src" / "pipe"
    return {p: (src / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new):
    txt = files[name]
    hits = txt.count(old)
    assert hits == 1, "%s: %d hits for %r" % (name, hits, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, extra=""):
    BUILT[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/pipe/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    if extra:
        body.append(extra.rstrip("\n"))
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


# --- the divisor ----------------------------------------------------------------------

def div_length():
    f = base()
    sub(f, "weigh.py",
        "    out = 0\n"
        "    for idx in rec.bands:\n"
        "        band = bands[idx]\n"
        "        if band.keep:\n"
        "            out += band.share.get(rec.rid, 0)\n"
        "    return out",
        "    return rec.n - 1")
    write("div-length", "the weight is spread as if the record had never been cut", f)


def div_first_step():
    f = base()
    sub(f, "weigh.py",
        "    for idx in rec.bands:\n"
        "        band = bands[idx]\n"
        "        if band.keep:\n"
        "            out += band.share.get(rec.rid, 0)",
        "    band = bands[rec.bands[0]]\n"
        "    if band.keep:\n"
        "        out += band.share.get(rec.rid, 0)")
    write("div-first-step", "the divisor counts only the step the record started in", f)


def div_all_steps():
    f = base()
    sub(f, "weigh.py",
        "        band = bands[idx]\n"
        "        if band.keep:\n"
        "            out += band.share.get(rec.rid, 0)",
        "        band = bands[idx]\n"
        "        out += band.share.get(rec.rid, 0)")
    write("div-all-steps", "a dropped step still counts toward the divisor", f)


def scored_length():
    f = base()
    sub(f, "lay.py", "            rec.scored = rec.n - rec.parts",
        "            rec.scored = rec.n - 1")
    write("scored-length", "the scored count ignores what the cut cost", f)


# --- when things settle ----------------------------------------------------------------

def pay_at_piece():
    f = base()
    sub(f, "hold.py", "    def laid_rec(self, rec):\n        self.laid.append(rec)",
        "    def laid_rec(self, rec):\n        self.laid.append(rec)\n"
        "        self.at += 1\n        self.pay(rec)")
    sub(f, "weigh.py", "        if band.keep:\n            out += band.share.get(rec.rid, 0)",
        "        if band.keep or not band.shut:\n            out += band.share.get(rec.rid, 0)")
    write("pay-at-piece", "a record settles the moment its last piece is placed", f)


def step_at_shut():
    f = base()
    sub(f, "hold.py",
        "        while self.at < len(self.laid):\n"
        "            rec = self.laid[self.at]\n"
        "            if rec.bands[-1] != band.idx:\n"
        "                break\n"
        "            self.at += 1\n"
        "            self.pay(rec)\n"
        "        self.flush()",
        "        while self.at < len(self.laid):\n"
        "            rec = self.laid[self.at]\n"
        "            if rec.bands[-1] != band.idx:\n"
        "                break\n"
        "            self.at += 1\n"
        "            self.pay(rec)\n"
        "        if band.keep:\n"
        "            self.sink.step(band.idx, band.wins, band.pos, band.num, band.den)")
    write("step-at-shut", "a step's line is printed when its windows run out", f)


def step_before_lay():
    f = base()
    sub(f, "hold.py",
        "    def laid_rec(self, rec):\n        self.laid.append(rec)",
        "    def laid_rec(self, rec):\n        self.laid.append(rec)\n\n"
        "    def flush_first(self):\n        pend = self.pend\n        self.pend = []\n"
        "        self.flush()\n        for line in pend:\n            self.sink.lay(*line)")
    sub(f, "hold.py", "        self.laid = []\n        self.at = 0",
        "        self.laid = []\n        self.pend = []\n        self.at = 0")
    sub(f, "hold.py",
        "        self.sink.lay(rec.rid, rec.first, rec.parts, rec.scored, num, den)",
        "        self.pend.append((rec.rid, rec.first, rec.parts, rec.scored, num, den))")
    sub(f, "hold.py", "            self.pay(rec)\n        self.flush()",
        "            self.pay(rec)\n        self.flush_first()")
    write("step-before-lay", "the step lines are printed before the record that released them", f)


# --- the cut ----------------------------------------------------------------------------

def cut_brim():
    f = base()
    sub(f, "cut.py",
        "    if most < 2:\n        return None\n"
        "    left = rem - most\n    if left == 0 or left >= 2:\n        return most\n"
        "    if most > 2:\n        return most - 1\n    return None",
        "    if most < 1:\n        return None\n    return most")
    write("cut-brim", "a window is filled to the brim, one token pieces and all", f)


def cut_floor_one():
    f = base()
    sub(f, "cut.py", "    if most < 2:\n        return None", "    if most < 1:\n        return None")
    write("cut-floor-one", "a one token piece is allowed, but a stranded token is not", f)


def cut_always_back():
    f = base()
    sub(f, "cut.py", "    if left == 0 or left >= 2:\n        return most",
        "    if left == 0:\n        return most")
    write("cut-always-back", "the piece steps back whenever the record is not finished", f)


# --- what is laid -----------------------------------------------------------------------

def first_at_op():
    f = base()
    sub(f, "lay.py", "        if rec.parts == 0:\n            rec.first = rack.wno\n",
        "")
    sub(f, "lay.py", "    rec = Rec(rid, n, w)\n    rem = n",
        "    rec = Rec(rid, n, w)\n    rec.first = rack.wno if rack.up else rack.wno + 1\n    rem = n")
    write("first-at-op", "the first window is the one open when the record arrived", f)


def lay_one_token():
    f = base()
    sub(f, "lay.py", "    if n < 2:\n        rack.sink.skip(rid)\n        return None\n", "")
    sub(f, "cut.py", "    if most < 2:\n        return None", "    if most < 1:\n        return None")
    write("lay-one-token", "a one token record is laid like any other", f)


def skip_two_token():
    f = base()
    sub(f, "lay.py", "    if n < 2:", "    if n < 3:")
    write("skip-two-token", "a two token record is passed over as well", f)


def skip_room():
    f = base()
    sub(f, "lay.py", "    if n < 2:\n        rack.sink.skip(rid)\n        return None",
        "    if n < 2:\n        rack.sink.skip(rid)\n"
        "        if not rack.up:\n            rack.open_win()\n"
        "        rack.put(rid, 1)\n"
        "        if rack.room() == 0:\n            rack.shut_win()\n"
        "        return None")
    write("skip-room", "a passed over record still takes the slot it would have used", f)


# --- the floor and the settings ----------------------------------------------------------

def floor_strict():
    f = base()
    sub(f, "step.py", "        band.keep = band.pos >= band.flr", "        band.keep = band.pos > band.flr")
    write("floor-strict", "a step has to beat the floor rather than reach it", f)


def width_now():
    f = base()
    sub(f, "win.py", "    def room(self):\n        return self.ww - self.fill",
        "    def room(self):\n        return self.w - self.fill")
    write("width-now", "a width op resizes the window that is already open", f)


def span_now():
    f = base()
    sub(f, "step.py", "        if band.wins >= band.cap:", "        if band.wins >= rack.sp:")
    write("span-now", "a span op resizes the step that is already open", f)


def floor_now():
    f = base()
    sub(f, "step.py", "        band.keep = band.pos >= band.flr", "        band.keep = band.pos >= rack.fl")
    write("floor-now", "a floor op decides the step that is already open", f)


def cross_score():
    f = base()
    sub(f, "step.py", "        got = take - 1\n        if got:\n            self.pos += got",
        "        got = take\n        if got:\n            self.pos += got")
    write("cross-score", "every filled position scores, boundaries included", f)


# --- the lines ---------------------------------------------------------------------------

def drop_late():
    f = base()
    sub(f, "hold.py",
        "        if not band.keep:\n            self.sink.drop(band.idx, band.wins, band.pos)\n"
        "        while self.at < len(self.laid):",
        "        while self.at < len(self.laid):")
    sub(f, "hold.py", "            self.pay(rec)\n        self.flush()",
        "            self.pay(rec)\n"
        "        if not band.keep:\n            self.sink.drop(band.idx, band.wins, band.pos)\n"
        "        self.flush()")
    write("drop-late", "a dropped step prints after the records it was holding", f)


def void_zero():
    f = base()
    sub(f, "hold.py",
        "        if d == 0:\n            self.sink.void(rec.rid)\n",
        "        if d == 0:\n"
        "            self.sink.lay(rec.rid, rec.first, rec.parts, rec.scored, 0, 1)\n")
    write("void-zero", "a record with no divisor prints a zero weight instead of void", f)


def frac_raw():
    f = base()
    sub(f, "weigh.py", "def share(rec, d):\n    return frac.norm(rec.w, d)",
        "def share(rec, d):\n    return rec.w, d")
    write("frac-raw", "the fraction a position carries is printed as it was formed", f)


def sum_positions():
    f = base()
    sub(f, "hold.py",
        "                self.sink.step(band.idx, band.wins, band.pos, band.num, band.den)",
        "                self.sink.step(band.idx, band.wins, band.pos, band.pos, 1)")
    write("sum-positions", "a step reports its position count where its weight belongs", f)


READINGS = (
    div_length, div_first_step, div_all_steps, scored_length,
    pay_at_piece, step_at_shut, step_before_lay,
    cut_brim, cut_floor_one, cut_always_back,
    first_at_op, lay_one_token, skip_two_token, skip_room,
    floor_strict, width_now, span_now, floor_now, cross_score,
    drop_late, void_zero, frac_raw, sum_positions,
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for build in READINGS:
        build()
    print("wrote %d wrong readings: %s" % (len(MADE), ", ".join(MADE)))


if __name__ == "__main__":
    main()
