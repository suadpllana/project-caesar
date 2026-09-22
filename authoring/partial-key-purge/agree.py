"""Cross-check implementations on the shaped small families and on the fuzz. Authoring only.

    python agree.py [count-per-family] [impl ...]

Every script is first checked for the input guarantees (consistent initial rows, no reference
to a two-cascade table, every delete naming present rows), then run through the brute force and
through each named implementation: `model` (tests/seal/model.py) or a directory holding the five
editable modules (the reference in solution/, or a variant under variants/). Prints mismatches
and the coverage counters that say whether the population exercised each mechanism.
"""
import collections
import os
import random
import subprocess
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.join(HERE, "..", "..", "tasks", "partial-key-purge")
SEAL = os.path.join(TASK, "tests", "seal")
sys.path.insert(0, SEAL)
sys.path.insert(0, HERE)

import brute  # noqa: E402
import fuzz  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

PARTS = ("match.py", "drop.py", "clear.py", "hold.py", "audit.py")


def consistent(text):
    db = brute.read(text)
    data = db["data"]
    for t in db["order"]:
        for c, vals in data[t].items():
            for r in db["refs"].values():
                if r["tab"] != t:
                    continue
                st = brute.status(r, vals)
                if st == "broken":
                    return "broken %s %s %d" % (r["name"], t, c)
                if st == "live" and not brute.matches(db, r, vals, data):
                    return "dangling %s %s %d" % (r["name"], t, c)
            for k in db["keys"].values():
                if k["tab"] == t and any(vals[i] is None for i in k["cols"]):
                    return "null key %s %d" % (t, c)
    for k in db["keys"].values():
        seen = set()
        for c, vals in data[k["tab"]].items():
            kv = tuple(vals[i] for i in k["cols"])
            if kv in seen:
                return "duplicate key %s" % k["name"]
            seen.add(kv)
    cas = collections.Counter(r["tab"] for r in db["refs"].values() if r["act"] == "cascade")
    for r in db["refs"].values():
        kt = db["keys"][r["key"]]["tab"]
        if cas[kt] >= 2:
            return "reference %s names a two-cascade table" % r["name"]
    return None


def tree_for(impl):
    """A scratch /app-shaped tree with the implementation's five modules laid over."""
    room = tempfile.mkdtemp(prefix="pkp-")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), os.path.join(room, "app"))
    for part in PARTS:
        shutil.copy(os.path.join(impl, part), os.path.join(room, "app", "db", part))
    return os.path.join(room, "app")


def run_tree(app, text):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        got = subprocess.run([sys.executable, os.path.join(app, "run_db.py"), path],
                             capture_output=True, text=True, timeout=600)
    finally:
        os.unlink(path)
    if got.returncode:
        return ["ERROR " + (got.stderr.strip().splitlines() or ["?"])[-1]]
    return got.stdout.splitlines()


def population(per):
    for fam in gen.SMALL:
        if fam == "chain":
            continue
        for i in range(per):
            rng = random.Random("agree:%s:%d" % (fam, i))
            yield fam, gen.abstract(rng) if fam == "mixed" else gen.story(rng, fam)
    for i in range(per):
        yield "fuzz", fuzz.script(10_000 + i)


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    impls = sys.argv[2:] or ["model"]
    trees = {name: (None if name == "model" else tree_for(name)) for name in impls}
    bad = collections.Counter()
    seen = collections.Counter()
    shown = 0
    for fam, text in population(per):
        why = consistent(text)
        if why:
            print("INCONSISTENT", fam, why)
            bad["inconsistent"] += 1
            continue
        want = brute.run(text)
        seen[fam] += 1
        for name, app in trees.items():
            got = model.expect(text) if app is None else run_tree(app, text)
            if got != want:
                bad[(name, fam)] += 1
                if shown < 2:
                    shown += 1
                    print("MISMATCH", name, fam)
                    print(text)
                    for a, b in zip(want, got):
                        print(("   " if a == b else "!! ") + a + "  |  " + b)
                    print(len(want), len(got))
    print("scripts", dict(seen))
    print("mismatches", dict(bad) or "none")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
