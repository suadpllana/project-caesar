"""Generate authoring/variants/ from the reference plus one declared override each.

Hand-copied variants drift the moment the reference changes, and the symptom is every
correct implementation disagreeing at once. These are built from the reference every time,
so a variant can only differ where its override says it differs.

Every variant here is a correct implementation of the same contract written in a different
shape, and every one of them must score 1 through the real verifier. `mirror` is the
tie-check variant: the reference with every name the submission gets to choose changed, so a
graded value that depended on one of those names would show up as a disagreement.

Usage:
    python3 authoring/pack-bind-retire/make_variants.py
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
REF = os.path.join(TASK, "solution")
OUT = os.path.join(HERE, "variants")
FILES = ("vw.py", "bd.py", "ld.py", "rt.py", "od.py")

STACK_LOAD = '''from hst import bd, vw


def ld(h, nm, md):
    made = []
    stack = [(nm, md, 0)]
    while stack:
        name, mode, phase = stack.pop()
        if phase == 0:
            r = h.sr(name)
            if r is not None:
                if mode == "open" and r.n not in h.op:
                    h.op.append(r.n)
                continue
            stack.append((name, mode, 1))
            for d in reversed(h.pk[name].nd):
                stack.append((d, "own", 0))
            continue
        if h.sr(name) is not None:
            continue
        p = h.pk[name]
        fx = vw.mk(h, p)
        r = h.mk(p)
        r.fx = fx
        h.sd[name] = r.n
        made.append(r.n)
        if mode == "open":
            h.op.append(r.n)
        for s in p.st:
            bd.us(h, r, s)
    return made
'''

RELAX_KEEP = '''from hst import vw


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
                    g = vw.fd(h, r, nm)
                if g and g in h.rs and g not in keep:
                    keep.add(g)
                    grew = True
                    break
            if grew:
                break
    return keep
'''

SCAN_VIEW = '''def mk(h, p):
    seq = []
    q = list(p.nd)
    i = 0
    while i < len(q):
        nm = q[i]
        i += 1
        r = h.sr(nm)
        if r is None or r.n in seq:
            continue
        seq.append(r.n)
        q.extend(r.p.nd)
    return seq


def sq(h, r):
    out = [r.n]
    for n in list(r.fx) + list(h.op):
        if n in h.rs and n not in out:
            out.append(n)
    return out


def fd(h, r, nm):
    for n in sq(h, r):
        if nm in h.rs[n].p.pv:
            return n
    return 0
'''

VARIANTS = {
    "ok-stack-load": {"ld.py": STACK_LOAD},
    "ok-relax-keep": {"rt.py": RELAX_KEEP},
    "ok-scan-view": {"vw.py": SCAN_VIEW},
}

# Every identifier the submission gets to choose, renamed. What the frozen tree calls -
# ld, us, kp, dp, od - cannot move, and neither can the fields reg.py defines.
MIRROR = (("sq", "chain"), ("fd", "pick"), ("br", "walk"),
          ("made", "fresh"), ("keep", "held"), ("out", "seq"))
QUALIFIED = (("vw.mk", "vw.build"), ("def mk(", "def build("), ("r.fx", "r.zz"))


def mirror(src):
    for old, new in QUALIFIED:
        src = src.replace(old, new)
    for old, new in MIRROR:
        src = re.sub(r"(?<![\w.])%s(?![\w])" % old, new, src)
        src = re.sub(r"(?<=vw\.)%s(?![\w])" % old, new, src)
    return src


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    ref = {}
    for f in FILES:
        with open(os.path.join(REF, f), "r", encoding="ascii") as fh:
            ref[f] = fh.read()
    made = []
    for name in sorted(VARIANTS):
        d = os.path.join(OUT, name)
        os.makedirs(d)
        for f in FILES:
            src = VARIANTS[name].get(f, ref[f])
            if f in VARIANTS[name] and src == ref[f]:
                raise SystemExit("refusing %s: the override for %s equals the reference" % (name, f))
            with open(os.path.join(d, f), "w", encoding="ascii", newline="\n") as fh:
                fh.write(src)
        shutil.copyfile(os.path.join(REF, "solve.sh"), os.path.join(d, "solve.sh"))
        os.chmod(os.path.join(d, "solve.sh"), 0o755)
        made.append(name)
    d = os.path.join(OUT, "ok-mirror")
    os.makedirs(d)
    for f in FILES:
        src = mirror(ref[f])
        if src == ref[f] and f != "od.py":
            raise SystemExit("refusing ok-mirror: %s carries no renameable identifier" % f)
        with open(os.path.join(d, f), "w", encoding="ascii", newline="\n") as fh:
            fh.write(src)
    shutil.copyfile(os.path.join(REF, "solve.sh"), os.path.join(d, "solve.sh"))
    os.chmod(os.path.join(d, "solve.sh"), 0o755)
    made.append("ok-mirror")
    print("wrote %d variants into %s" % (len(made), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
