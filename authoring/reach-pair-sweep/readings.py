"""What each plausible wrong reading costs, measured through the shipped runtime.

Reachable whole-solver readings: every one is the reference with exactly one module changed by
one declared override, so a hand copy cannot drift away from the reading it stands for. Four of
them are what the tree actually ships broken, which is what an agent starts from.

Two things are reported, and the second matters more. The share of generated programs a reading
fails measures legibility - how long a solver can hold it without noticing. Under all-or-nothing
grading any share above zero already scores 0, so a low share is not a weak reading, it is a
quiet one. The second is whether some enumerated hand case names it, so a failure points at the
rule instead of at bad luck.

    python authoring/reach-pair-sweep/readings.py [per_family]
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
SOLN = TASK / "solution"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

PARTS = ("plan.py", "scan.py", "keep.py", "age.py", "wipe.py")

# name -> (module, old, new). One contiguous semantic change against the reference.
OVERRIDES = {
    # the remembered set is ignored, so a nursery object reachable only from old space is lost
    "no-rset": ("plan.py", """    out = [i for i in named if h.objs[i].space == heap.NURSERY]
    for src, fld, was in sorted(h.rset):
        if src not in h.objs:
            continue
        val = h.objs[src].flds.get(fld)
        if val is None or val not in h.objs:
            continue
        if h.objs[val].space == heap.NURSERY:
            out.append(val)
    return sorted(set(out))""",
                """    return sorted(set(named))"""),

    # the remembered set is trusted: the recorded field is never read again, so a stale entry
    # keeps a dead object alive
    "trust-rset": ("plan.py", """        val = h.objs[src].flds.get(fld)
        if val is None or val not in h.objs:
            continue
        if h.objs[val].space == heap.NURSERY:
            out.append(val)""",
                   """        if was in h.objs and h.objs[was].space == heap.NURSERY:
            out.append(was)"""),

    # an old key is treated as unreached, so a minor collection drops what it keeps
    "old-key-unready": ("scan.py", """    if not full:
        for k, vs in by.items():
            if k in h.objs and h.objs[k].space == heap.OLD:
                stack.extend(vs)
""", ""),

    # the queue is settled after keeping, hiding an object reachable only from another
    # finalizable one
    "queue-late": ("keep.py", """    fresh = [i for i in _scope(h, full)
             if i not in seen and h.objs[i].fin is not None
             and i not in h.done and i not in h.queue]

    start = [i for i in h.queue if i in h.objs] + fresh""",
                   """    fresh = []
    while True:
        start = [i for i in h.queue if i in h.objs] + fresh
        seen_now = scan.reach(h, start, full, frozenset(seen)) if start else set()
        more = [i for i in _scope(h, full)
                if i not in seen and i not in seen_now and h.objs[i].fin is not None
                and i not in h.done and i not in h.queue and i not in fresh]
        if not more:
            break
        fresh.append(more[0])
    start = [i for i in h.queue if i in h.objs] + fresh"""),

    # an object kept only to run its finalizer ages, so it promotes out of the nursery
    "age-held": ("age.py", "        if i not in seen or i in held:",
                 "        if i not in seen and i not in held:"),

    # a minor collection clears weak references to old objects it never examined
    "wipe-old": ("wipe.py", """        if not full:
            if tgt not in h.objs or h.objs[tgt].space != heap.NURSERY:
                continue
""", ""),

    # a minor collection releases old objects it never traced
    "release-old": ("wipe.py",
                    "    scope = [i for i in sorted(h.objs) "
                    "if full or h.objs[i].space == heap.NURSERY]",
                    "    scope = sorted(h.objs)"),
}


def build(tmp, name):
    """The reference with one module overridden, as a directory ready to overlay."""
    mod, old, new = OVERRIDES[name]
    out = tmp / ("read-%s" % name)
    out.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        src = (SOLN / part).read_text(encoding="utf-8")
        if part == mod:
            if old not in src:
                raise SystemExit("override %r no longer matches %s" % (name, mod))
            if old == new:
                raise SystemExit("override %r changes nothing" % name)
            src = src.replace(old, new, 1)
        (out / part).write_text(src, encoding="utf-8", newline="\n")
    return out


def tree_for(tmp, collector, tag):
    t = tmp / ("tree-%s" % tag)
    shutil.copytree(TASK / "environment" / "app_src", t)
    for f in sorted(pathlib.Path(collector).glob("*.py")):
        shutil.copy(f, t / "col" / f.name)
    return t


def record(tree, tmp, name, lines):
    p = tmp / ("%s.txt" % name)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "run_prog.py", str(p)], cwd=tree,
                       capture_output=True, text=True)
    return ["ERROR"] if r.returncode != 0 else r.stdout.splitlines()


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 20
    pop = [(n, l) for f, n, l in gen.programs("readings-seed", per) if f != "wide"]
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        want_hand = {n: model.expect(cases.ops(n)) for n in cases.ORDER}
        want_gen = {n: model.expect(gen.ops(l)) for n, l in pop}

        print("%-16s %-8s %-6s %s" % ("reading", "moves", "hand", "cases that name it"))
        ok = True
        for name in sorted(OVERRIDES):
            tree = tree_for(tmp, build(tmp, name), name)
            caught = [n for n in cases.ORDER
                      if record(tree, tmp, n, cases.CASES[n]) != want_hand[n]]
            moved = sum(1 for n, l in pop if record(tree, tmp, n, l) != want_gen[n])
            print("%-16s %-8s %-6s %s"
                  % (name, "%.1f%%" % (100.0 * moved / len(pop)),
                     "yes" if caught else "NO", ", ".join(caught[:3]) or "-"))
            if not caught:
                ok = False
        print("\npopulation: %d generated programs, %d hand cases" % (len(pop), len(cases.ORDER)))
        print("every reading separated and named:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


# --- the interface tools/readingcheck.py drives ------------------------------------------

REFERENCE = str(SOLN)


def _sources():
    out = {}
    for name in OVERRIDES:
        mod, old, new = OVERRIDES[name]
        files = {}
        for part in PARTS:
            src = (SOLN / part).read_text(encoding="utf-8")
            if part == mod:
                if old not in src:
                    raise SystemExit("override %r no longer matches %s" % (name, mod))
                src = src.replace(old, new, 1)
            files[part] = src
        out[name] = files
    return out


READINGS = _sources()


def run(policy, text):
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        tree = tmp / "tree"
        shutil.copytree(TASK / "environment" / "app_src", tree)
        for f in sorted(pathlib.Path(policy).glob("*.py")):
            shutil.copy(f, tree / "col" / f.name)
        prog = tmp / "p.txt"
        prog.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "run_prog.py", str(prog)], cwd=tree,
                           capture_output=True, text=True)
        return ("ERROR",) if r.returncode != 0 else tuple(r.stdout.splitlines())


def enumerated():
    return [(n, "\n".join(cases.CASES[n])) for n in cases.ORDER]


def generated(n):
    per = max(1, n // len(gen.FAMILIES))
    return [(name, "\n".join(lines))
            for fam, name, lines in gen.programs("readingcheck", per) if fam != "wide"]
