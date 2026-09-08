"""What each plausible wrong reading of the rules costs, measured through the shipped engine.

Every reading is the reference with one declared change, so a hand copy cannot drift away
from the reading it stands for. Five of them are what the tree actually ships broken, which
is where an agent starts.

Two numbers are reported and the second matters more. The share of generated scenarios a
reading fails says how long a solver can hold it without noticing; under all-or-nothing
grading any share above zero already scores 0, so a low share is a quiet reading, not a weak
one. The second is whether some enumerated case names it, so a failure points at a rule
rather than at bad luck.

    python authoring/move-clash-merge/readings.py [per_family]
"""
import importlib
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "move-clash-merge"
SOLN = TASK / "solution"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402

PARTS = ("live.py", "spot.py", "name.py", "book.py", "step.py")

GROUPED = '''def plan(cur, tgt, m, fold):
    ops = []
    gone = [cur.path(k) for k in cur.n if k != ROOT and k not in m]
    for path in sorted(gone, key=lambda p: (-p.count("/"), p)):
        ops.append(("rm", path))
    moves, edits, made = [], [], []
    for ck, tk in m.items():
        if ck == ROOT:
            continue
        nd, td = cur.n[ck], tgt.n[tk]
        want = tgt.path(tk)
        if cur.path(ck) != want:
            moves.append((want, ("mv", cur.path(ck), want)))
        if td.k == "f" and nd.c != td.c:
            edits.append((want, ("ed", want, td.c)))
    inv = dict((v, k) for k, v in m.items())
    for tk in tgt.n:
        if tk == ROOT or tk in inv:
            continue
        td = tgt.n[tk]
        path = tgt.path(tk)
        made.append((path, ("mkd", path) if td.k == "d" else ("mkf", path, td.c)))
    for box in (moves, made, edits):
        for _, op in sorted(box):
            ops.append(op)
    return ops
'''

# name -> (module, [(old, new), ...]). One semantic change each, against the reference.
OVERRIDES = {
    "removal-always-wins": ("live.py", [(
        """        side, tr = ("L", lo) if inl else ("R", ro)
        nd, a = tr.n[key], ag.n[key]
        if mk(ag, side, nd.p) != a.p or nd.nm != a.nm or nd.c != a.c:
            alive.add(key)""",
        """        continue""")]),

    "only-a-write-saves": ("live.py", [(
        """        if mk(ag, side, nd.p) != a.p or nd.nm != a.nm or nd.c != a.c:""",
        """        if nd.c != a.c:""")]),

    "folder-held-by-arrival": ("live.py", [(
        """            par = ag.n[key].p
            if par != ROOT and par not in alive and raw[key][0] == par:""",
        """            par = raw[key][0]
            if par != ROOT and par in ag.n and par not in alive:""")]),

    "folder-held-by-mover": ("live.py", [(
        """            if par != ROOT and par not in alive and raw[key][0] == par:""",
        """            if par != ROOT and par not in alive:""")]),

    "workstation-move-whole": ("spot.py", [(
        """        nm, ns = axis(a.nm, ln, rn, inl, inr)
        out[key] = (par, nm, ps, ns)""",
        """        nm, ns = axis(a.nm, ln, rn, inl, inr)
        if inl and inr and (lp != a.p or ln != a.nm):
            par, nm = lp, ln
            ps = "a" if lp == a.p else "L"
            ns = "a" if ln == a.nm else "L"
        out[key] = (par, nm, ps, ns)""")]),

    "server-move-whole": ("spot.py", [(
        """        nm, ns = axis(a.nm, ln, rn, inl, inr)
        out[key] = (par, nm, ps, ns)""",
        """        nm, ns = axis(a.nm, ln, rn, inl, inr)
        if inl and inr and (rp != a.p or rn != a.nm):
            par, nm = rp, rn
            ps = "a" if rp == a.p else "R"
            ns = "a" if rn == a.nm else "R"
        out[key] = (par, nm, ps, ns)""")]),

    "workstation-wins-axis": ("spot.py", [(
        """        if rv == av:
            return (lv, "L")
        return (rv, "R")""",
        """        if rv == av:
            return (lv, "L")
        return (lv, "L")""")]),

    "dead-folder-drops-to-root": ("spot.py", [(
        """def up(ag, alive, par):
    while par != ROOT and par not in alive:
        par = ag.n[par].p
    return par""",
        """def up(ag, alive, par):
    return par if par == ROOT or par in alive else ROOT""")]),

    "loop-breaks-server-side": ("spot.py", [(
        """        free = [k for k in ring if k not in pinned and pl[k][2] == "L"]""",
        """        free = [k for k in ring if k not in pinned and pl[k][2] == "R"]""")]),

    "loop-breaks-newest": ("spot.py", [(
        """        who = min(free, key=rank)""",
        """        who = max(free, key=rank)""")]),

    "mark-after-extension": ("name.py", [(
        """def mark(nm, k):
    cut = nm.rfind(".")
    if 0 < cut < len(nm) - 1:
        return "%s~%d%s" % (nm[:cut], k, nm[cut:])
    return "%s~%d" % (nm, k)""",
        """def mark(nm, k):
    return "%s~%d" % (nm, k)""")]),

    "names-contested-exactly": ("name.py", [(
        """def fold(nm):
    return nm.lower()""",
        """def fold(nm):
    return nm""")]),

    "keeper-by-side-only": ("name.py", [(
        """    if held(ag, key, par, nm):
        return (0, int(ids[key]))
""", "")]),

    "keeper-workstation-first": ("name.py", [(
        """    if shows(ag, ro, "R", key, nm):
        return (1, int(ids[key]))
    if shows(ag, lo, "L", key, nm):
        return (2, int(ids[key]))""",
        """    if shows(ag, lo, "L", key, nm):
        return (1, int(ids[key]))
    if shows(ag, ro, "R", key, nm):
        return (2, int(ids[key]))""")]),

    "second-node-keeps-name": ("name.py", [(
        """    if key.startswith("C:"):
        return (4, int(ids[key]))""",
        """    if key.startswith("C:"):
        return (0, int(ids[key]))""")]),

    "second-node-after-names": ("book.py", [(
        """    con, copies = hold(ag, lo, ro, pl)
    for key in copies:
        c = "C:" + key
        pl[c] = (pl[key][0], pl[key][1], "c", "c")
        con[c] = ro.n[key].c
    ids, nxt2 = number(ag, lo, ro, pl, copies, nxt)
    nms = name.settle(ag, lo, ro, pl, ids)""",
        """    con, copies = hold(ag, lo, ro, pl)
    ids, nxt2 = number(ag, lo, ro, pl, [], nxt)
    nms = name.settle(ag, lo, ro, pl, ids)
    for key in copies:
        c = "C:" + key
        pl[c] = (pl[key][0], pl[key][1], "c", "c")
        con[c] = ro.n[key].c
        nms[c] = name.mark(nms[key], 1)
        ids[c] = str(nxt2)
        nxt2 += 1""")]),

    "second-node-carries-ours": ("book.py", [(
        """                else:
                    con[key] = lc
                    copies.append(key)""",
        """                else:
                    con[key] = rc
                    copies.append(key)"""),
        ("""        con[c] = ro.n[key].c""", """        con[c] = lo.n[key].c""")]),

    "same-bytes-still-conflict": ("book.py", [(
        """                if lc == rc or rc == a.c:""",
        """                if rc == a.c:""")]),

    "workstation-numbered-first": ("book.py", [(
        """    for side, tr in (("R", ro), ("L", lo)):
        news = sorted""",
        """    for side, tr in (("L", lo), ("R", ro)):
        news = sorted""")]),

    "numbered-as-made": ("book.py", [(
        """        news = sorted((tr.path(k), side + ":" + k)
                      for k in tr.n if k != ROOT and k not in ag.n)
        fresh += [key for _, key in news]""",
        """        fresh += sorted(side + ":" + k
                        for k in tr.n if k != ROOT and k not in ag.n)""")]),

    "emitted-by-kind": ("step.py", [(
        """def plan(cur, tgt, m, fold):
    work = cur.copy()""", GROUPED + """

def unused_plan(cur, tgt, m, fold):
    work = cur.copy()""")]),

    "destination-by-name": ("step.py", [(
        """    par = tgt.n[tk].p
    if par == ROOT:
        return ROOT
    return inv.get(par)""",
        """    par = tgt.n[tk].p
    if par == ROOT:
        return ROOT
    return work.at(tgt.path(par))""")]),

    "nothing-pushed-aside": ("step.py", [(
        """        if pick is None:
            op = aside(work, tgt, m, inv, fold)
            if op is None:
                return ops""",
        """        if pick is None:
            op = None
            if op is None:
                return ops""")]),

    "written-before-placed": ("step.py", [(
        """        if nd.p == want and nd.nm == td.nm:
            if td.k == "f" and nd.c != td.c:
                out.append((("ed", work.path(ck), td.c), None))
            continue""",
        """        if td.k == "f" and nd.c != td.c:
            out.append((("ed", work.path(ck), td.c), None))
        if nd.p == want and nd.nm == td.nm:
            continue""")]),

    "removals-emitted-last": ("step.py", [(
        """RANK = {"rm": 0, "mv": 1, "mkd": 2, "mkf": 2, "ed": 3}""",
        """RANK = {"rm": 3, "mv": 0, "mkd": 1, "mkf": 1, "ed": 2}""")]),
}


def _sources():
    out = {}
    for name, (mod, edits) in OVERRIDES.items():
        files = {}
        for part in PARTS:
            src = (SOLN / part).read_text(encoding="utf-8")
            if part == mod:
                for old, new in edits:
                    if old not in src:
                        raise SystemExit("override %r no longer matches %s" % (name, mod))
                    src = src.replace(old, new, 1)
            files[part] = src
        out[name] = files
    return out


READINGS = _sources()
REFERENCE = str(SOLN)
_TREES = {}


def _tree(policy):
    key = str(policy)
    if key not in _TREES:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="mcm-read-"))
        tree = tmp / "app"
        shutil.copytree(TASK / "environment" / "app_src", tree,
                        ignore=shutil.ignore_patterns("__pycache__"))
        for part in PARTS:
            one = pathlib.Path(policy) / part
            if one.is_file():
                shutil.copy(one, tree / "mrg" / part)
        _TREES[key] = tree
    return _TREES[key]


def run(policy, text):
    tree = _tree(policy)
    for mod in [m for m in list(sys.modules) if m == "mrg" or m.startswith("mrg.")]:
        del sys.modules[mod]
    sys.path.insert(0, str(tree))
    rows = []
    try:
        importlib.import_module("mrg.drive").go(text.split("\n"), rows.append)
    except Exception as exc:
        return ("ERROR", type(exc).__name__)
    finally:
        sys.path.remove(str(tree))
    return tuple(rows)


def enumerated():
    return [(n, cases.CASES[n]) for n in cases.ORDER]


def generated(n):
    per = max(1, n // len(gen.FAMILIES))
    return gen.batch("readingcheck", per)


def reductions(text):
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i][:2] in ("L ", "R "):
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i, line in enumerate(lines):
        if line[:2] in ("d ", "f "):
            path = line.split()[2]
            keep = [x for j, x in enumerate(lines)
                    if j != i and path not in x]
            yield "\n".join(keep)


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 24
    pop = generated(per * len(gen.FAMILIES))
    hand = enumerated()
    want = dict((n, run(REFERENCE, t)) for n, t in hand)
    wantpop = dict((n, run(REFERENCE, t)) for n, t in pop)
    ok = True
    print("%-28s %8s  %-5s %s" % ("reading", "moves", "named", "by"))
    for name in sorted(READINGS):
        alt = pathlib.Path(tempfile.mkdtemp(prefix="mcm-alt-"))
        for part, src in READINGS[name].items():
            (alt / part).write_text(src, encoding="utf-8")
        moved = sum(1 for n, t in pop if run(alt, t) != wantpop[n])
        named = [n for n, t in hand if run(alt, t) != want[n]]
        print("%-28s %7.1f%%  %-5s %s"
              % (name, 100.0 * moved / len(pop), "yes" if named else "NO",
                 ", ".join(named[:3]) or "-"))
        if not named:
            ok = False
    print("\npopulation: %d generated, %d enumerated" % (len(pop), len(hand)))
    print("every reading separated and named:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
