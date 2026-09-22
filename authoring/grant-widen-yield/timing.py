#!/usr/bin/env python3
"""Time the reference, the two correct variants and every correct-but-naive reading on the
two scale families, against the 60 second limit the brief states.

This is the measurement the resource gate rests on, and it is re-run rather than remembered:
a boundary that was not measured after the last change to the generator or the reference is a
boundary that may not bite (CLAUDE.md, publish-settle-order).

Each row runs in its own subprocess with `python -u`, because a harness that buffers its own
output looks exactly like a hang.

    python3 authoring/grant-widen-yield/timing.py [seconds-per-program]
"""
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

VARIANTS = ("walk", "multiset")

# The readings that are exactly correct and only too slow come from emit.py, so the cheats
# that ship and the rows measured here are the same files and cannot drift apart.
SLOW = dict((name, (part, old, new)) for name, (_note, part, old, new) in emit.SLOW.items())


def programs():
    """One program from each scale family, and the whole graded set once."""
    _cases, gen, _model = lab.sealed()
    out = []
    for fam in ("wide", "busy"):
        rng = random.Random("timing|%s" % fam)
        out.append((fam, "\n".join(gen.MAKE[fam](rng)) + "\n"))
    return out


def whole_set():
    _cases, gen, _model = lab.sealed()
    cases, _g, _m = lab.sealed()
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER]
    work += gen.programs("timing-whole", 40)
    return work


def build(room, label):
    if label == "reference":
        return lab.tree(lab.SOL)
    if label in VARIANTS:
        return lab.tree(HERE / "variants" / label)
    part, old, new = SLOW[label]
    files = dict(lab.reference())
    files[part] = lab.patch(part, (old, new))
    return lab.tree(files=files)


def run_one(here, text, limit):
    room = pathlib.Path(tempfile.mkdtemp(prefix="gwy-t-"))
    prog = room / "p.txt"
    prog.write_text(text, encoding="utf-8", newline="\n")
    code = ("import sys, time, run_lk\n"
            "a = time.time()\n"
            "out = run_lk.run(open(%r).read())\n"
            "print('%%.2f %%d' %% (time.time() - a, len(out)))\n" % str(prog))
    start = time.time()
    try:
        done = subprocess.run([sys.executable, "-u", "-c", code], cwd=str(here),
                              capture_output=True, text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        return None, time.time() - start
    finally:
        shutil.rmtree(room, ignore_errors=True)
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()
        return "ERROR " + (tail[-1] if tail else ""), 0.0
    secs, lines = done.stdout.split()
    return lines, float(secs)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    progs = programs()
    room = pathlib.Path(tempfile.mkdtemp(prefix="gwy-timing-"))
    labels = ["reference"] + list(VARIANTS) + sorted(SLOW)
    print("one program of each scale family, %d s cap per program" % limit)
    print("%-14s %s" % ("service", "  ".join("%-24s" % f for f, _t in progs)))
    for label in labels:
        here = build(room, label)
        cells = []
        for _fam, text in progs:
            lines, secs = run_one(here, text, limit)
            if lines is None:
                cells.append("%-24s" % ("over %d s" % limit))
            elif isinstance(lines, str) and lines.startswith("ERROR"):
                cells.append("%-24s" % lines[:24])
            else:
                cells.append("%-24s" % ("%7.2f s  %s lines" % (secs, lines)))
        print("%-14s %s" % (label, "  ".join(cells)))

    print("\nthe whole graded set, reference only, against the 60 s limit:")
    here = build(room, "reference")
    mod = lab.inproc(here)
    work = whole_set()
    start = time.time()
    total = 0
    for _fam, _name, rows in work:
        total += len(mod.run("\n".join(rows) + "\n"))
    print("  %d programs, %.2f s, %d trace lines" % (len(work), time.time() - start, total))
    shutil.rmtree(room, ignore_errors=True)


if __name__ == "__main__":
    main()
