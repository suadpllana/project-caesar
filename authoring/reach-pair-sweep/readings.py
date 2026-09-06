"""What each plausible wrong reading costs, measured through the shipped runtime.

Reachable whole-solver readings, not ablations of a file that ships correct: every one is a
complete `cyc/keep.py` an agent could actually write, generated from the reference by exactly
one declared override so a hand copy cannot drift away from it.

Two things are reported, and the second is the one that matters. The share of generated
programs a reading fails measures legibility - how long a solver can hold it without noticing.
Under all-or-nothing grading any share above zero already scores 0, so a low share is not a
weak reading, it is a quiet one. The second is whether some enumerated hand case names it, so
a failure points at the rule instead of at bad luck.

    python authoring/reach-pair-sweep/readings.py [per_family]
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

# Each entry is one semantic change against solution/keep.py: (old, new).
OVERRIDES = {
    # the pair table is swept once instead of until a sweep adds nothing
    "pair-once": ("""    got = _reach(h, seed, blocked)
    while True:
        add = [v for k, v in h.pr
               if k in got and v in h.ob and v not in got and v not in blocked]
        if not add:
            return got
        got |= _reach(h, add, blocked)""",
                  """    got = _reach(h, seed, blocked)
    add = [v for k, v in h.pr
           if k in got and v in h.ob and v not in got and v not in blocked]
    if add:
        got |= _reach(h, add, blocked)
    return got"""),

    # what a finalizable object keeps follows fields only, never the pair table
    "hold-fields": ("    hold = _close(h, set(h.qu) | set(qd), live)",
                    "    hold = _reach(h, set(h.qu) | set(qd), live)"),

    # a weak reference is tested against everything kept, not against what the frames reach
    "clear-held": ("    cl = [n for n, w in h.wk.items() if not w.c and w.t not in live]",
                   "    cl = [n for n, w in h.wk.items()\n"
                   "          if not w.c and w.t not in live and w.t not in hold]"),

    # the queue is settled after keeping, so an object kept by an earlier finalizable object
    # is treated as not garbage and never queued
    "queue-late": ("""    qd = sorted(i for i in h.ob
                if i not in live and h.ob[i].fz is not None
                and i not in h.rn and i not in h.qu)""",
                   """    qd = []
    while True:
        seen = _close(h, set(h.qu) | set(qd), live)
        more = [i for i in sorted(h.ob)
                if i not in live and h.ob[i].fz is not None
                and i not in h.rn and i not in h.qu and i not in qd and i not in seen]
        if not more:
            break
        qd.append(more[0])
    qd = sorted(qd)"""),

    # having run a finalizer once is not remembered across cycles
    "refinalize": ("                and i not in h.rn and i not in h.qu)",
                   "                and i not in h.qu)"),

    # clearing is recomputed every cycle instead of staying put
    "unclear": ("    cl = [n for n, w in h.wk.items() if not w.c and w.t not in live]",
                "    cl = [n for n, w in h.wk.items() if w.t not in live]"),
}


def build(tmp, name):
    src = (TASK / "solution" / "keep.py").read_text(encoding="utf-8")
    old, new = OVERRIDES[name]
    if old not in src:
        raise SystemExit("override %r no longer matches the reference" % name)
    if old == new:
        raise SystemExit("override %r changes nothing" % name)
    out = tmp / ("keep-%s.py" % name)
    out.write_text(src.replace(old, new, 1), encoding="utf-8")
    return out


def tree_for(tmp, collector, tag):
    t = tmp / ("tree-%s" % tag)
    shutil.copytree(TASK / "environment" / "app_src", t)
    shutil.copy(collector, t / "cyc" / "keep.py")
    return t


def record(tree, tmp, name, lines):
    p = tmp / ("%s.txt" % name)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "run_prog.py", str(p)], cwd=tree,
                       capture_output=True, text=True)
    return ["ERROR"] if r.returncode != 0 else r.stdout.splitlines()


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 60
    pop = gen.programs("readings-seed", per)
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        want_hand = {n: model.expect(cases.ops(n)) for n in cases.ORDER}
        want_gen = {n: model.expect(gen.ops(l)) for _, n, l in pop}

        print("%-14s %-8s %-7s %s" % ("reading", "moves", "hand", "cases that name it"))
        ok = True
        for name in sorted(OVERRIDES):
            tree = tree_for(tmp, build(tmp, name), name)
            caught = [n for n in cases.ORDER
                      if record(tree, tmp, n, cases.CASES[n]) != want_hand[n]]
            moved = sum(1 for _, n, l in pop if record(tree, tmp, n, l) != want_gen[n])
            print("%-14s %-8s %-7s %s"
                  % (name, "%.1f%%" % (100.0 * moved / len(pop)),
                     "yes" if caught else "NO", ", ".join(caught[:3]) or "-"))
            if not caught or not moved:
                ok = False
        print("\npopulation: %d generated programs, %d hand cases" % (len(pop), len(cases.ORDER)))
        print("every reading separated and named:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


# --- the interface tools/readingcheck.py drives ------------------------------------------

REFERENCE = str(TASK / "solution")


def _reading_sources():
    ref = (TASK / "solution" / "keep.py").read_text(encoding="utf-8")
    out = {}
    for name, (old, new) in OVERRIDES.items():
        if old not in ref:
            raise SystemExit("override %r no longer matches the reference" % name)
        out[name] = {"keep.py": ref.replace(old, new, 1)}
    return out


READINGS = _reading_sources()


def run(policy, text):
    """Drive one program under one collector directory, returning its record."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        tree = tmp / "tree"
        shutil.copytree(TASK / "environment" / "app_src", tree)
        shutil.copy(pathlib.Path(policy) / "keep.py", tree / "cyc" / "keep.py")
        prog = tmp / "p.txt"
        prog.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "run_prog.py", str(prog)], cwd=tree,
                           capture_output=True, text=True)
        return ("ERROR",) if r.returncode != 0 else tuple(r.stdout.splitlines())


def enumerated():
    return [(n, "\n".join(cases.CASES[n])) for n in cases.ORDER]


def generated(n):
    per = max(1, n // len(gen.FAMILIES))
    return [(name, "\n".join(lines)) for _, name, lines in gen.programs("readingcheck", per)]
