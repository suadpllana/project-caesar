"""Every wrong reading of the scheduling rules, measured against the reference.

Answers the question the difficulty argument rests on: does a plausible
misreading move a real share of the graded traces, or is it a lottery ticket
that a hand-written case set would only catch by luck? Each entry is the
reference with exactly one file changed, and the change is declared as a
substitution that has to apply, so a reading cannot drift away from the
reference it was derived from.

tools/readingcheck.py reads REFERENCE, READINGS, run(), enumerated() and
generated() from this file and reports, per reading, whether the enumerated set
already separates it. Run directly it prints the share of generated traces each
reading moves; anything under about a tenth is a lottery ticket rather than a
decision.

Usage:
    python3 tasks/batch-admit-reclaim/authoring/readings.py [count]
    python3 tools/readingcheck.py batch-admit-reclaim
"""

import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
SRC = os.path.join(TASK, "environment", "app_src")
SOL = os.path.join(TASK, "solution")
TESTS = os.path.join(TASK, "tests")
sys.path.insert(0, TESTS)

import cases
import gen

WORK = os.environ.get("WORK", "/tmp/bar-work")
POLICY = ("fit.py", "room.py", "back.py", "pick.py")
REFERENCE = SOL


def drop():
    for name in [n for n in list(sys.modules) if n == "eng" or n.startswith("eng.")]:
        sys.modules.pop(name, None)


def build(where, files):
    if os.path.isdir(where):
        shutil.rmtree(where)
    shutil.copytree(SRC, where, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, text in files.items():
        with open(os.path.join(where, "eng", name), "w") as fh:
            fh.write(text)
    return where


def play(tree, text):
    drop()
    sys.path.insert(0, tree)
    try:
        from eng.rd import parse
        from eng.step import Eng
        out = []
        Eng(parse(text), out.append).run()
        return [tuple(x) for x in out]
    except Exception as exc:
        return [("torn", type(exc).__name__, str(exc)[:60])]
    finally:
        if tree in sys.path:
            sys.path.remove(tree)
        drop()


def slug(label):
    keep = "".join(c if c.isalnum() else "-" for c in label.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


def source(name):
    with open(os.path.join(SOL, name)) as fh:
        return fh.read()


def edit(name, *swaps):
    """The reference file with one declared change, so a reading cannot drift."""
    text = source(name)
    for old, new in swaps:
        if old not in text:
            raise SystemExit("stale reading override in %s: %r" % (name, old[:50]))
        text = text.replace(old, new, 1)
    return text


SHIP_FIT = open(os.path.join(SRC, "eng", "fit.py")).read()
SHIP_ROOM = open(os.path.join(SRC, "eng", "room.py")).read()
SHIP_BACK = open(os.path.join(SRC, "eng", "back.py")).read()

def no_merge():
    return edit("fit.py", ("""        g.have += 1
        if g.have % w.span == 0:
            p.free()
            if not p.take(keys(g.toks, w.span, g.have)[-1], w.t):
                return False""", """        g.have += 1"""))


def free_on_close():
    return edit("fit.py", ("""def drop(p, g, span):
    for k in keys(g.toks, span, g.have):
        p.give(k)""", """def drop(p, g, span):
    for k in keys(g.toks, span, g.have):
        p.give(k)
        b = p.blk.get(k)
        if b is not None and b.refs == 0:
            del p.blk[k]"""))


def no_tail():
    return edit("fit.py", ("""        if tgt % w.span:
            if not p.hold():
                return False
    return spend <= w.left""", """    return spend <= w.left"""))


def entrant_only():
    return edit("fit.py", ("""    for g in order:
        if g not in live:
            continue""", """    for g in []:
        if g not in live:
            continue"""))


def room_born():
    return edit("room.py", ("        r = (b.touch, b.born)", "        r = (b.born,)"))


def back_holes():
    return edit("back.py", ("""        if not pool.has(k):
            break
        n += 1""", """        if pool.has(k):
            n += 1"""))


def back_zero():
    return edit("back.py", ("""    tgt = r.plen if r.have == 0 else r.have
    n = 0""", """    tgt = 0
    n = 0"""))


def back_fresh_only():
    return edit("back.py", ("""    tgt = r.plen if r.have == 0 else r.have""",
                            """    tgt = 0 if r.seen else r.plen"""))


def victim_oldest():
    return edit("pick.py", ("    return max(run, key=lambda r: r.idx)",
                            "    return min(run, key=lambda r: r.idx)"))


def order_short():
    return edit("pick.py", ("    return sorted(q, key=lambda r: r.idx)",
                            "    return sorted(q, key=lambda r: (len(r.toks), r.idx))"))


def slug(label):
    keep = "".join(c if c.isalnum() else "-" for c in label.lower())
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")


READINGS = [
    ("the pool is asked how much it has, not played out", "fit.py", lambda: SHIP_FIT),
    ("the block a filling tail gives back is missed", "fit.py", no_merge),
    ("what this step finishes is counted as room", "fit.py", free_on_close),
    ("the newcomer's part block is forgotten", "fit.py", no_tail),
    ("only the newcomer is asked about", "fit.py", entrant_only),
    ("the pool gives up what came free last", "room.py", lambda: SHIP_ROOM),
    ("the pool gives up the oldest block it made", "room.py", room_born),
    ("a request keeps the blocks it had", "back.py", lambda: SHIP_BACK),
    ("a hole in the middle is stepped over", "back.py", back_holes),
    ("a request starts over from nothing", "back.py", back_zero),
    ("only a first-time request shares what is there", "back.py", back_fresh_only),
    ("the first to arrive is put out", "pick.py", victim_oldest),
    ("the shortest waiting request goes first", "pick.py", order_short),
]




READINGS = dict((slug(label), {target: make()})
                for label, target, make in READINGS)


def merge(over):
    files = dict((name, source(name)) for name in POLICY)
    files.update(over)
    return files


def run(policy, text):
    files = {}
    for name in POLICY:
        here = os.path.join(str(policy), name)
        if os.path.isfile(here):
            with open(here) as fh:
                files[name] = fh.read()
    tag = hashlib.sha256("".join(sorted(files.values())).encode("utf-8")).hexdigest()[:12]
    return play(build(os.path.join(WORK, "reading-" + tag), files), text)


def enumerated():
    return sorted(cases.TRACES.items())


def generated(n):
    return gen.batch("readingcheck", n)


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 300
    jobs = gen.batch("readings", count)
    ref = build(os.path.join(WORK, "ref-readings"), merge({}))
    base = dict((name, play(ref, text)) for name, text in jobs)
    torn = sum(1 for v in base.values() if v and v[0][0] == "torn")
    print("reference: %d traces, %d torn" % (len(jobs), torn))
    width = max(len(label) for label in READINGS)
    for label in sorted(READINGS):
        tree = build(os.path.join(WORK, "rd"), merge(READINGS[label]))
        moved = sum(1 for name, text in jobs if play(tree, text) != base[name])
        print("  %-*s  %5.1f%%" % (width, label, 100.0 * moved / len(jobs)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
