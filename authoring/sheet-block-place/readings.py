"""Whole-solver readings: complete engines an agent could plausibly ship, measured.

Each reading is the reference policy with one decision replaced, so every one of them is a
tree an agent could actually hand in - not an ablation of a file that ships correct. Each
patch asserts it fired; a substitution that matched nothing is reported as an error rather
than measured as a clean zero.

Reported per reading: the share of generated scripts whose printed grid it moves, and the
enumerated case that names it.
"""

import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tasks" / "sheet-block-place" / "tests"))

import gen  # noqa: E402
import harness  # noqa: E402

REF = harness.TASK / "solution"
SHIPPED = harness.TASK / "environment" / "app_src" / "sheet"

# (reading, file, old, new, the enumerated case that separates it)
PATCHES = [
    ("face-content-first", "see.py",
     """def face(st, a):
    for o in lay.cone(st, a):""",
     """def face(st, a):
    if st.sheet.held(a):
        v = memo.value(st, a)
        if grid.is_blk(v):
            return grid.BLK
        if grid.is_set(v):
            return grid.REF
        return v
    for o in lay.cone(st, a):""",
     "owner-shows-its-first-value"),
    ("face-last-owner", "see.py",
     "    for o in lay.cone(st, a):",
     "    for o in reversed(lay.cone(st, a)):",
     "owner-order-decides-a-loop"),
    ("lay-overlap-allowed", "lay.py",
     """        if taken(st, c, o):
            return False""",
     """        if False:
            return False""",
     "overlap-earliest-wins"),
    ("lay-own-cell-counts", "lay.py",
     """        if c == o:
            continue""",
     """        if c == o and False:
            continue""",
     "owner-cell-is-not-in-the-way"),
    ("lay-clip-at-edge", "lay.py",
     "        if o[0] + h - 1 <= addr.ROWH and o[1] + w - 1 < addr.COLW and clear(st, o, h, w):",
     "        if clear(st, o, h, w):",
     "block-past-the-last-row"),
    ("lay-undecided-is-free", "lay.py",
     """def rect(st, o):
    hit = st.lays.get(o)""",
     """def rect(st, o):
    if o in st.mark:
        return None
    hit = st.lays.get(o)""",
     "read-into-own-quadrant"),
    ("memo-loop-marks-one", "memo.py",
     """        cut = st.busy.index(a)
        for b in st.busy[cut:]:
            st.vals[b] = grid.CYC
        return grid.CYC""",
     """        st.vals[a] = grid.CYC
        return grid.CYC""",
     "loop-swallows-what-it-passed-through"),
    ("val-sum-propagates", "val.py",
     """                seen += 1
                if not grid.is_err(e):
                    nums.append(e)""",
     """                seen += 1
                if grid.is_err(e):
                    return e
                nums.append(e)""",
     "sum-steps-over-a-refusal"),
    ("val-cnt-skips-errors", "val.py",
     """        if nm == "CNT":
            return seen""",
     """        if nm == "CNT":
            return len(nums)""",
     "count-includes-a-refusal"),
    ("val-cnt-counts-empty", "val.py",
     """                if grid.is_gap(e):
                    continue
                seen += 1""",
     """                if grid.is_gap(e):
                    seen += 1
                    continue
                seen += 1""",
     "count-ignores-empty"),
    ("val-grow-fills-holes", "val.py",
     "            out.append(e if (grid.is_gap(e) or grid.is_err(e)) else e + 1)",
     "            out.append(e if grid.is_err(e) else (1 if grid.is_gap(e) else e + 1))",
     "grow-keeps-a-hole"),
    ("val-at-gap-zero", "val.py",
     """        if k > len(pool):
            return grid.REF
        return pool[k - 1]
    if nm == "RUN":""",
     """        if k > len(pool):
            return grid.REF
        got = pool[k - 1]
        return 0 if grid.is_gap(got) else got
    if nm == "RUN":""",
     "at-on-an-empty-cell"),
    ("val-error-right-first", "val.py",
     """    if grid.is_err(l):
        return l
    if grid.is_err(r):
        return r""",
     """    if grid.is_err(r):
        return r
    if grid.is_err(l):
        return l""",
     "left-error-wins"),
    ("val-loop-is-skippable", "val.py",
     """def call(st, nm, args):
    if looped(args):
        return grid.CYC""",
     """def call(st, nm, args):
    if False:
        return grid.CYC""",
     "loop-does-not-stop-at-a-sum"),
    ("val-block-arith-is-error", "val.py",
     """    for v in (l, r):
        if grid.is_blk(v) or grid.is_set(v):
            return grid.REF""",
     """    for v in (l, r):
        if grid.is_set(v):
            return grid.REF
        if grid.is_blk(v):
            return grid.items(v)[0]""",
     "block-in-arithmetic"),
]


def make(name, rel, old, new):
    home = pathlib.Path(tempfile.mkdtemp(prefix="sbp-read-"))
    for f in harness.POLICY:
        shutil.copyfile(REF / f, home / f)
    text = (home / rel).read_text()
    if text.count(old) != 1:
        raise SystemExit("reading %s: patch matched %d times in %s"
                         % (name, text.count(old), rel))
    (home / rel).write_text(text.replace(old, new, 1))
    return home


def main():
    wide = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    b = gen.batch("read", wide)
    texts = [t for _, t in b]
    base = harness.run_with(str(REF), texts, limit=1800)

    rows = [("shipped-engine", harness.run_with(str(SHIPPED), texts, limit=1800),
             "the tree as it ships")]
    homes = []
    for name, rel, old, new, case in PATCHES:
        home = make(name, rel, old, new)
        homes.append(home)
        rows.append((name, harness.run_with(str(home), texts, limit=1800), case))

    print("%-26s %8s  %s" % ("reading", "moves", "named by"))
    for name, got, case in rows:
        moved = sum(1 for i in range(len(b))
                    if isinstance(got[i], dict) or got[i] != base[i])
        print("%-26s %6.1f%%  %s" % (name, 100.0 * moved / len(b), case))
    for home in homes:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    main()


# --------------------------------------------------------------- tools/readingcheck.py
#
# The contract that file documents. `run` drives one script through one policy directory
# in this process rather than through a subprocess, because readingcheck asks for it once
# per script per reading and a process launch each time would take hours; the assembled
# tree is cached per policy and the `sheet` package is purged between imports so nothing
# carries over.

REFERENCE = str(REF)

TREES = {}


def _tree(policy):
    key = str(policy)
    if key not in TREES:
        home = pathlib.Path(tempfile.mkdtemp(prefix="sbp-tree-"))
        shutil.copytree(harness.APP, home / "app",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for f in harness.POLICY:
            src = pathlib.Path(policy) / f
            if src.exists():
                shutil.copyfile(src, home / "app" / "sheet" / f)
        TREES[key] = home / "app"
    return TREES[key]


def run(policy, text):
    tree = str(_tree(policy))
    for name in [n for n in sys.modules if n == "sheet" or n.startswith("sheet.")]:
        del sys.modules[name]
    sys.path.insert(0, tree)
    try:
        from sheet.core import Run
        rows = []
        Run(rows.append).run(text.split("\n"))
        return tuple("%d %s %s | %s" % r for r in rows)
    finally:
        sys.path.remove(tree)


def enumerated():
    import cases

    return [(n, cases.CASES[n]) for n in sorted(cases.CASES)]


def generated(n):
    per = max(1, n // 5)
    return gen.batch("readingcheck", per)


READINGS = {}
for _name, _rel, _old, _new, _case in PATCHES:
    _src = (REF / _rel).read_text()
    if _src.count(_old) != 1:
        raise SystemExit("reading %s: patch matches %d times in %s"
                         % (_name, _src.count(_old), _rel))
    READINGS[_name] = {_rel: _src.replace(_old, _new, 1)}
