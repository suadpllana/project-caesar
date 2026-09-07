"""Do the graded scripts separate the wrong readings a solver will actually have?

Each reading below is a whole working policy - the reference with one rule read the other
way - so every one of them is a submission an agent could plausibly hand in. Per-rule
coverage on paper proves nothing; what matters is the share of graded scripts on which a
reading's report differs from the sealed model's, and whether some enumerated hand case
catches it. A reading that moves nothing is a rule the grading cannot see.

Each patch asserts that its substitution fired. A rewrite that silently matches nothing
ships the reference under another name and reports a clean zero.

    python3 authoring/grid-spread-refresh/readings.py [count]
"""

import os
import shutil
import signal
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "grid-spread-refresh")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402
import tree  # noqa: E402

# name -> (file, [(old, new, count)])
PATCHES = {
    "no-occupancy": ("dep.py", [(
        '        b = self.st.own(ad)\n        self.rd.append(("o", ad, b))\n        return b',
        '        return self.st.own(ad)', 1)]),
    "static-refs": ("upd.py", [(
        "    eng.dp.note(ad, w.rd)",
        "    from sheet import flow\n"
        "    named = []\n"
        "    flow.walk(eng.st.node(ad), named)\n"
        "    probes = [r for r in w.rd if r[0] == \"o\"]\n"
        "    eng.dp.note(ad, [(\"v\", t, st.val(t)) for t in named] + probes)", 1)]),
    "no-cutoff": ("flow.py", [(
        "        if not eng.dp.stale(eng.st, ad):\n            continue\n", "", 1)]),
    "eager-order": ("flow.py", [("        ad = pick(eng, pend)", "        ad = min(pend)", 1)]),
    "keep-record": ("flow.py", [(
        "    eng.dp.drop(ad)\n    if eng.st.node(ad) is None:\n        for t in release",
        "    if eng.st.node(ad) is None:\n        eng.dp.drop(ad)\n        for t in release", 1)]),
    "stay-formula": ("flow.py", [(
        "    if eng.st.node(ad) is None:\n"
        "        for t in release(eng, ad):\n"
        "            pend.update(eng.dp.readers(t))\n"
        "    else:\n"
        "        pend.add(ad)",
        "    if eng.st.node(ad) is not None:\n        pend.add(ad)", 1)]),
    "no-selfcover": ("lay.py", [(
        '        read = set(t for k, t, _ in w.rd if k == "v")\n'
        "        for t in want:\n            if t in read:\n                return None\n", "", 1)]),
    "no-vacate": ("lay.py", [(
        "        keep = set(tgt)\n"
        "        for t in self.fp.get(ad, ()):\n"
        "            if t not in keep and self.by.get(t) == ad:\n"
        "                del self.by[t]\n"
        "                if not st.own(t):\n"
        "                    st.show(t, None)\n", "", 1)]),
    "probe-stop": ("lay.py", [(
        "            if w.own(t):\n                taken = True\n",
        "            if w.own(t):\n                taken = True\n                break\n", 1)]),
    "own-overwrite": ("lay.py", [(
        "                if not st.own(t):\n                    st.show(t, None)",
        "                st.show(t, None)", 2)]),
    "empty-blk": ("upd.py", [(
        "        st.show(ad, vals[0] if vals else None)",
        "        st.show(ad, vals[0] if vals else store.BLK)", 1)]),
}


def variant(name):
    where, edits = PATCHES[name]
    out = tempfile.mkdtemp(prefix="gsr-read-")
    for fn in ("dep.py", "lay.py", "upd.py", "flow.py"):
        shutil.copyfile(os.path.join(TASK, "solution", fn), os.path.join(out, fn))
    path = os.path.join(out, where)
    with open(path) as fh:
        text = fh.read()
    for old, new, want in edits:
        hits = text.count(old)
        if hits != want:
            raise SystemExit("reading %s: pattern matched %d times, wanted %d in %s"
                             % (name, hits, want, where))
        text = text.replace(old, new)
    with open(path, "w") as fh:
        fh.write(text)
    return tree.build(out)


class Spun(Exception):
    pass


def stop(signum, frame):
    raise Spun()


def report(app, text, cap=20000, seconds=10):
    """Drive one script through a reading, bounded in two ways.

    A reading that drops the self-occupancy rule does not answer wrongly, it fails to
    terminate: the block writes over its own input, the input changes, and the block is
    asked for again. Either bound turns that into a reported difference here; in the
    verifier the worker's own wall clock does the same job.
    """
    for n in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
        del sys.modules[n]
    sys.path.insert(0, app)
    try:
        from sheet import core
        plain = core.Eng.calc
        seen = [0]

        def counted(self, ad):
            seen[0] += 1
            if seen[0] > cap:
                raise Spun()
            return plain(self, ad)

        core.Eng.calc = counted
        rows = []
        signal.alarm(seconds)
        core.drive(text.split("\n"), rows.append)
        return rows
    except Exception as exc:
        return ["raised %r" % (exc,)]
    finally:
        signal.alarm(0)
        sys.path.remove(app)
        for n in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
            del sys.modules[n]


# ---------------------------------------------------------------- readingcheck contract
#
# tools/readingcheck.py drives the same readings from the other end: it asks whether some
# enumerated case separates each one, and when none does it hunts a generated counterexample
# and shrinks it to something short enough to ship as a case. It wants the readings as
# whole file sources, a reference directory, the two case supplies and a runner.

REFERENCE = os.path.join(TASK, "solution")


def sources(name):
    where, edits = PATCHES[name]
    with open(os.path.join(REFERENCE, where)) as fh:
        text = fh.read()
    for old, new, want in edits:
        hits = text.count(old)
        if hits != want:
            raise SystemExit("reading %s: pattern matched %d times, wanted %d in %s"
                             % (name, hits, want, where))
        text = text.replace(old, new)
    return {where: text}


READINGS = dict((name, sources(name)) for name in PATCHES)
_TREES = {}


def enumerated():
    return sorted(cases.CASES.items())


def generated(rounds):
    return gen.batch("readcheck-v1", max(1, rounds))


def run(policy, text):
    app = _TREES.get(str(policy))
    if app is None:
        app = _TREES[str(policy)] = tree.build(str(policy))
    return report(app, text)


def reductions(text):
    """Drop one edit at a time, latest first, and never the two lines that frame a script."""
    lines = text.strip("\n").split("\n")
    for i in range(len(lines) - 1, -1, -1):
        head = lines[i].split(None, 1)[0] if lines[i].strip() else ""
        if head in ("size", "go", ""):
            continue
        yield "\n".join(lines[:i] + lines[i + 1:])


def main(argv):
    signal.signal(signal.SIGALRM, stop)
    n = int(argv[1]) if len(argv) > 1 else 20
    scripts = list(cases.CASES.items()) + gen.batch("read-v1", n)
    want = dict((nm, oracle.solve(tx)) for nm, tx in scripts)
    hand = set(cases.CASES)
    t0 = time.time()
    print("%-14s %6s %6s   %s" % ("reading", "gen", "hand", "first hand case that catches it"))
    worst = 0
    for name in sorted(PATCHES):
        app = variant(name)
        miss = []
        for nm, tx in scripts:
            if report(app, tx) != want[nm]:
                miss.append(nm)
        gens = [m for m in miss if m not in hand]
        hands = [m for m in miss if m in hand]
        total = len(scripts) - len(hand)
        print("%-14s %5.1f%% %5d/%-3d %s" % (
            name, 100.0 * len(gens) / max(1, total), len(hands), len(hand),
            sorted(hands)[0] if hands else "NONE - not separated by any hand case"))
        if not miss:
            worst = 1
            print("     ^^ NOT SEPARATED AT ALL - the grading cannot see this rule")
    print("%d scripts each, %.1fs" % (len(scripts), time.time() - t0))
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
