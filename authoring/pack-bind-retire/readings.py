"""The wrong readings, as whole solvers rather than as prose.

Each entry replaces one file of the reference with a complete module implementing one
reading of the brief, so every reading here is a tree an agent could actually have written.
`core` marks the two readings that turn on what a view is - the place where a name stops
being a property of the host and becomes a property of the asker. The rest are readings a
careful solver can hold while implementing its first plan faithfully.

Usage:
    python3 authoring/pack-bind-retire/readings.py <task-dir> [count]
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
REFERENCE = os.path.join(TASK, "solution")

VW_GLOBAL = '''def mk(h, p):
    return []


def sq(h, r):
    out = []
    if r.n in h.rs:
        out.append(r.n)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    for n in h.sd.values():
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
'''

VW_LIVE = '''def mk(h, p):
    return list(p.nd)


def sq(h, r):
    out = [r.n]
    q = list(r.fx)
    while q:
        nm = q.pop(0)
        x = h.sr(nm)
        if x is None or x.n in out:
            continue
        out.append(x.n)
        q.extend(x.p.nd)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
'''

VW_DEPTH = '''def mk(h, p):
    out = []

    def walk(nm):
        r = h.sr(nm)
        if r is None or r.n in out:
            return
        out.append(r.n)
        for d in r.p.nd:
            walk(d)

    for d in p.nd:
        walk(d)
    return out


def sq(h, r):
    out = [r.n]
    for n in r.fx:
        if n in h.rs and n not in out:
            out.append(n)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
'''

VW_OPENFIRST = '''def mk(h, p):
    out = []
    seen = set()
    q = list(p.nd)
    while q:
        nm = q.pop(0)
        r = h.sr(nm)
        if r is None or r.n in seen:
            continue
        seen.add(r.n)
        out.append(r.n)
        q.extend(r.p.nd)
    return out


def sq(h, r):
    out = [r.n]
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    for n in r.fx:
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
'''

VW_NOSELF = '''def mk(h, p):
    out = []
    seen = set()
    q = list(p.nd)
    while q:
        nm = q.pop(0)
        r = h.sr(nm)
        if r is None or r.n in seen:
            continue
        seen.add(r.n)
        out.append(r.n)
        q.extend(r.p.nd)
    return out


def sq(h, r):
    out = []
    for n in r.fx:
        if n in h.rs and n not in out:
            out.append(n)
    for n in h.op:
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
'''

BD_RECACHE = '''from hst import vw


def us(h, r, nm):
    p = r.p
    if nm not in p.rq and nm not in p.wk:
        return ("bad", 0)
    g = vw.fd(h, r, nm)
    r.rc[nm] = g
    if g:
        return ("res", g)
    return ("none", 0)
'''

RT_REFCOUNT = '''def kp(h):
    keep = set()
    for n in h.sd.values():
        if n in h.rs:
            keep.add(n)
    for n in h.rs:
        for g in h.rs[n].rc.values():
            if g and g in h.rs:
                keep.add(g)
    return keep
'''

RT_WEAK = '''from hst import vw


def kp(h):
    keep = set()
    q = []
    for n in h.sd.values():
        if n in h.rs and n not in keep:
            keep.add(n)
            q.append(n)
    while q:
        r = h.rs[q.pop()]
        for nm in list(r.p.rq) + list(r.p.wk):
            if nm in r.rc:
                g = r.rc[nm]
            else:
                g = vw.fd(h, r, nm)
            if g and g in h.rs and g not in keep:
                keep.add(g)
                q.append(g)
    return keep
'''

RT_RECORDED = '''def kp(h):
    keep = set()
    q = []
    for n in h.sd.values():
        if n in h.rs and n not in keep:
            keep.add(n)
            q.append(n)
    while q:
        r = h.rs[q.pop()]
        for nm in r.p.rq:
            g = r.rc.get(nm, 0)
            if g and g in h.rs and g not in keep:
                keep.add(g)
                q.append(g)
    return keep
'''

RT_SWEPT = '''from hst import vw


def kp(h):
    keep = set()
    for n in h.sd.values():
        if n in h.rs:
            keep.add(n)
    grew = True
    while grew:
        grew = False
        for n in sorted(keep):
            r = h.rs[n]
            for nm in r.p.rq:
                if nm in r.rc:
                    g = r.rc[nm]
                else:
                    g = 0
                    for m in vw.sq(h, r):
                        if m in keep and nm in h.rs[m].p.pv:
                            g = m
                            break
                if g and g in h.rs and g not in keep:
                    keep.add(g)
                    grew = True
                    break
    return keep
'''

LD_BFS = '''from hst import bd, vw


def ld(h, nm, md):
    r = h.sr(nm)
    if r is not None:
        if md == "open" and r.n not in h.op:
            h.op.append(r.n)
        return []
    made = []
    seen = []
    q = [nm]
    while q:
        x = q.pop(0)
        if x in seen:
            continue
        seen.append(x)
        q.extend(h.pk[x].nd)
    for x in seen:
        if h.sr(x) is not None:
            continue
        p = h.pk[x]
        fx = vw.mk(h, p)
        r = h.mk(p)
        r.fx = fx
        h.sd[x] = r.n
        made.append(r.n)
        if md == "open" and x == nm:
            h.op.append(r.n)
        for s in p.st:
            bd.us(h, r, s)
    return made
'''

LD_NOPROMOTE = '''from hst import bd, vw


def ld(h, nm, md):
    made = []
    br(h, nm, md, made)
    return made


def br(h, nm, md, made):
    if h.sr(nm) is not None:
        return
    p = h.pk[nm]
    for d in p.nd:
        br(h, d, "own", made)
    fx = vw.mk(h, p)
    r = h.mk(p)
    r.fx = fx
    h.sd[nm] = r.n
    made.append(r.n)
    if md == "open":
        h.op.append(r.n)
    for s in p.st:
        bd.us(h, r, s)
'''

LD_STLATE = '''from hst import bd, vw


def ld(h, nm, md):
    made = []
    br(h, nm, md, made)
    for n in made:
        r = h.rs[n]
        for s in r.p.st:
            bd.us(h, r, s)
    return made


def br(h, nm, md, made):
    r = h.sr(nm)
    if r is not None:
        if md == "open" and r.n not in h.op:
            h.op.append(r.n)
        return
    p = h.pk[nm]
    for d in p.nd:
        br(h, d, "own", made)
    fx = vw.mk(h, p)
    r = h.mk(p)
    r.fx = fx
    h.sd[nm] = r.n
    made.append(r.n)
    if md == "open":
        h.op.append(r.n)
'''

OD_KEEPOPEN = '''def dp(h, nm):
    r = h.sr(nm)
    if r is None:
        return 0
    del h.sd[nm]
    return r.n


def od(ns):
    return sorted(ns, reverse=True)
'''

OD_OLDEST = '''def dp(h, nm):
    r = h.sr(nm)
    if r is None:
        return 0
    del h.sd[nm]
    if r.n in h.op:
        h.op.remove(r.n)
    return r.n


def od(ns):
    return sorted(ns)
'''

READINGS = {
    "one-table-for-everyone": {"vw.py": VW_GLOBAL},
    "needs-followed-live": {"vw.py": VW_LIVE},
    "needs-walked-deep": {"vw.py": VW_DEPTH},
    "open-before-needs": {"vw.py": VW_OPENFIRST},
    "self-not-in-view": {"vw.py": VW_NOSELF},
    "record-is-a-cache": {"bd.py": BD_RECACHE},
    "kept-by-count": {"rt.py": RT_REFCOUNT},
    "weak-keeps-too": {"rt.py": RT_WEAK},
    "kept-by-record": {"rt.py": RT_RECORDED},
    "kept-among-kept": {"rt.py": RT_SWEPT},
    "needs-made-wide": {"ld.py": LD_BFS},
    "no-promotion": {"ld.py": LD_NOPROMOTE},
    "start-names-last": {"ld.py": LD_STLATE},
    "dropped-stays-open": {"od.py": OD_KEEPOPEN},
    "oldest-released-first": {"od.py": OD_OLDEST},
}

CORE = ("one-table-for-everyone", "needs-followed-live")

_TREES = {}


def tree_for(policy):
    key = os.path.abspath(policy)
    if key in _TREES:
        return _TREES[key]
    work = tempfile.mkdtemp(prefix="rd-")
    dest = os.path.join(work, "tree")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), dest)
    for f in sorted(os.listdir(key)):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(key, f), os.path.join(dest, "hst", f))
    _TREES[key] = dest
    return dest


def run(policy, text):
    tree = tree_for(policy)
    work = tempfile.mkdtemp(prefix="rc-")
    path = os.path.join(work, "c.txt")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(text)
    env = dict(os.environ)
    env["PYTHONPATH"] = tree
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run([sys.executable, os.path.join(tree, "run_host.py"), path],
                       capture_output=True, text=True, env=env)
    shutil.rmtree(work, ignore_errors=True)
    if r.returncode != 0:
        return ("fault", r.stderr.strip().splitlines()[-1:] or [""])
    return tuple(r.stdout.splitlines())


def enumerated():
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import cases as C
    return [(nm, C.FIXED[nm]) for nm in sorted(C.FIXED)]


def generated(n):
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import gen as G
    out = []
    for i in range(n):
        seed = 0x51ED0000 ^ (i * 0x9E3779B1)
        out.append(("r%03d" % i, G.spec(seed)))
    return out


def build_policy(name):
    work = tempfile.mkdtemp(prefix="pol-")
    for f in sorted(os.listdir(REFERENCE)):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(REFERENCE, f), os.path.join(work, f))
    for f, src in sorted(READINGS[name].items()):
        with open(os.path.join(work, f), "w", encoding="ascii") as fh:
            fh.write(src)
    return work


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 300
    corpus = generated(count)
    base = [run(REFERENCE, t) for _, t in corpus]
    print("%-24s %8s  %s" % ("reading", "moves", "share"))
    for name in sorted(READINGS):
        pol = build_policy(name)
        moved = 0
        for (nm, t), b in zip(corpus, base):
            if run(pol, t) != b:
                moved += 1
        tag = " core" if name in CORE else ""
        print("%-24s %8d  %5.1f%%%s" % (name, moved, 100.0 * moved / len(corpus), tag))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
