"""Plant one deviation per copy of app/ and check the cross-check notices it."""
import importlib
import random
import shutil
import sys
import tempfile

HERE = __file__.rsplit("/", 1)[0]
APP = HERE + "/../app"
sys.path.insert(0, HERE)
import gen  # noqa: E402
import model  # noqa: E402

MUTS = {
    "tie-chunk-first": [("pick.py", "k, pos, j = heappop(heap)", "k, j, pos = heappop(heap)"),
                        ("live.py", "heap.append((k, pos, j))", "heap.append((k, j, pos))"),
                        ("live.py", "heappush(st.heap, (k, pos, j))", "heappush(st.heap, (k, j, pos))")],
    "key-count-only": [("live.py", "k = n_live if n_live < t else t", "k = t"),
                       ("live.py", "        if n_live < k:\n            k = n_live\n", "")],
    "no-recount": [("step.py", "            live.recount(st, c, fi)\n", "")],
    "stale-spread-at-start": [("live.py", "            if vals[fi] is not None:", "            if False:")],
    "w-not-widened": [("hdr.py", "    return pg.mn - (g - 1), pg.mx + (g - 1)", "    return pg.mn, pg.mx")],
    "dict-for-nn-nu": [("step.py", "            if cmp and pg.form == \"i\":\n                consult(col, j, out)\n",
                        "            if pg.form == \"i\" and not cmp:\n                consult(col, j, out)\n            if cmp and pg.form == \"i\":\n                consult(col, j, out)\n")],
    "dict-pass-ignores-nulls": [("dct.py", "if good_count == m and u == 0:", "if good_count == m:")],
    "proj-no-everyrow": [("hdr.py", "    if k == n:\n        return n - u, s\n", "")],
    "proj-no-single-dict": [("dct.py", "    return pg.form == \"i\" and pg.nulls == 0", "    return False and pg.nulls == 0")],
    "proj-single-dict-with-nulls": [("dct.py", "pg.form == \"i\" and pg.nulls == 0 and", "pg.form == \"i\" and")],
    "dict-before-prior-read": [("step.py", "        vals = col.vals[fi]\n        if vals is None:\n            if cmp and pg.form == \"i\":",
                                "        vals = col.vals[fi]\n        if cmp and pg.form == \"i\" and vals is not None:\n            consult(col, j, out)\n        if vals is None:\n            if cmp and pg.form == \"i\":")],
    "live-excludes-updated": [("live.py", "        st.live[c] = [alive[ch.start:ch.start + ch.n].count(1) for ch in mem.cols[c].chunks]",
                               "        st.live[c] = [sum(1 for r in range(ch.start, ch.start + ch.n) if alive[r] and r not in mem.cols[c].upd) for ch in mem.cols[c].chunks]")],
    "memory-per-query": [("live.py", "def start(seg, q, mem):\n", "def start(seg, q, mem):\n    for col in mem.cols:\n        col.vals = [None] * len(col.pages)\n        col.seen = bytearray(len(col.chunks))\n")],
    "proj-sorted-unique": [("proj.py", "    for c in q.cols:", "    for c in sorted(set(q.cols)):")],
    "spread-round-down": [("hdr.py", "got = -(-have * part // width)", "got = have * part // width")],
    "ne-empty-part-zero": [("hdr.py", "return have if kind == \"ne\" else 0", "return 0")],
    "no-part-cap": [("hdr.py", "    if part > width:\n        part = width\n", "")],
    "header-ne-pass-with-nulls": [("hdr.py", "    if v < lo or v > hi:\n        return 1 if u == 0 else 0\n    return 0\n",
                                   "    if v < lo or v > hi:\n        return 1\n    return 0\n")],
    "proj-header-onevalue-with-nulls": [("hdr.py", "if u == 0 and lo is not None and lo == hi:", "if lo is not None and lo == hi:")],
    "update-rows-skipped": [("step.py", "        if alive[r] and not sat(cd, upd[r]):", "        if False:")],
    "read-page-not-just-live": [("step.py", "        rows = [r for r in plain[fi] if alive[r]]\n        if not rows:\n            continue\n",
                                 "        rows = [r for r in plain[fi] if alive[r]]\n")],
    "proj-dc-before-header": [("proj.py", "                a = hdr.answer(pg.n, pg.nulls, pg.sum, lo[fi], hi[fi], k)",
                               "                a = None")],
}


def build(name, edits):
    root = tempfile.mkdtemp(prefix="mut_", dir=HERE)
    shutil.copytree(APP, root + "/app")
    for fn, old, new in edits:
        path = root + "/app/scn/" + fn
        src = open(path, encoding="utf-8").read()
        n = src.count(old)
        if n == 0:
            raise SystemExit("mutation %s did not fire in %s" % (name, fn))
        src = src.replace(old, new)
        open(path, "w", encoding="utf-8", newline="\n").write(src)
    return root


def load_app(root):
    for m in [m for m in sys.modules if m == "scn" or m.startswith("scn.") or m == "run_scan"]:
        del sys.modules[m]
    sys.path.insert(0, root + "/app")
    try:
        return importlib.import_module("run_scan")
    finally:
        sys.path.pop(0)


def texts(nfiles):
    out = []
    for s in range(nfiles):
        rng = random.Random(777000 + s)
        r = s % 3
        if r == 0:
            out.append(gen.make(rng))
        elif r == 1:
            a = rng.randint(1, 20)
            out.append(gen.make(rng, n=rng.randint(20, 200), k=rng.randint(1, 5),
                                chunk=(a, a + rng.randint(0, 30)), page=(1, rng.randint(1, 12)),
                                nq=rng.randint(3, 8), ncond=rng.randint(1, 8)))
        else:
            out.append(gen.make(rng, n=rng.randint(200, 400), k=5, chunk=(16, 40), page=(4, 12),
                                nq=3, ncond=8, big=True))
    return out


def main():
    nfiles = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    corpus = texts(nfiles)
    want = [model.run(t) for t in corpus]
    base = load_app(HERE + "/..")
    assert all(base.run(t) == w for t, w in zip(corpus, want)), "unmutated app disagrees"
    only = sys.argv[2:]
    for name, edits in MUTS.items():
        if only and name not in only:
            continue
        root = build(name, edits)
        try:
            app = load_app(root)
            hit = 0
            for t, w in zip(corpus, want):
                try:
                    got = app.run(t)
                except Exception:
                    got = None
                if got != w:
                    hit += 1
            print("%-32s caught on %4d of %d files (%.1f%%)" % (name, hit, len(corpus), 100.0 * hit / len(corpus)))
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    main()
