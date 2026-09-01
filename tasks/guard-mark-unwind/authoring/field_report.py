"""Which graded axis separates which cheat, and is any axis dead weight.

A field that separates no cheat cannot catch a wrong answer and can still fail a right
one, so it is pure liability. This walks the cheat suite and the variant suite against the
sealed model directly - no container, no pytest - and reports, per implementation, how many
programs differ on the trace, how many differ only on the tokens, and which enumerated
cases fire.

Reading it: every cheat should differ on the axis it was aimed at, and every variant should
differ nowhere. A cheat that differs only on the trace and never on the tokens is fine; one
that differs on neither is not a cheat.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import gen
import harness
import oracle

ROUNDS = 400


def norm(r):
    return ([tuple(x) for x in r["tr"]],
            [(a, b, tuple(c)) for a, b, c in r["tk"]])


def pool():
    out = [(n, cases.PROGS[n]) for n in sorted(cases.PROGS)]
    out += [(n, gen.text(p)) for n, p in gen.batch("field", ROUNDS)]
    return out


def grade(policy, want):
    dst = harness.tree(policy)
    trace = toks = 0
    fired = []
    for name, text in pool():
        got = norm(harness.safe(dst, text))
        exp = want[name]
        if got[0] != exp[0]:
            trace += 1
        elif got[1] != exp[1]:
            toks += 1
        else:
            continue
        if name in cases.PROGS:
            fired.append(name)
    return trace, toks, fired


def main():
    want = dict((n, norm(oracle.solve(t))) for n, t in pool())
    print("%-30s %6s %6s  %s" % ("implementation", "trace", "tokens", "cases"))
    t, k, f = grade(os.path.join(ROOT, "solution"), want)
    print("%-30s %6d %6d  %s" % ("reference", t, k, " ".join(f) or "-"))
    vd = os.path.join(HERE, "variants")
    for name in sorted(os.listdir(vd)):
        p = os.path.join(vd, name)
        if os.path.isdir(p):
            t, k, f = grade(p, want)
            print("%-30s %6d %6d  %s" % ("variant " + name, t, k, " ".join(f) or "-"))
    work = tempfile.mkdtemp(prefix="gmu-field-")
    dead = []
    for name in sorted(os.listdir(os.path.join(ROOT, "cheat"))):
        if not name.endswith(".sh"):
            continue
        d = os.path.join(work, name[:-3])
        os.makedirs(d)
        env = dict(os.environ)
        env["APP"] = os.path.join(d, "app")
        subprocess.run(["bash", os.path.join(ROOT, "cheat", name)], cwd=d, env=env,
                       capture_output=True, text=True)
        src = os.path.join(d, "app", "kern")
        t, k, f = grade(src if os.path.isdir(src) else d, want)
        print("%-30s %6d %6d  %s" % (name[:-3], t, k, " ".join(f[:4]) or "-"))
        if t == 0 and k == 0:
            dead.append(name[:-3])
    shutil.rmtree(work, ignore_errors=True)
    if dead:
        print("\nthese differ from the model nowhere, so the model is not what stops "
              "them: %s" % ", ".join(dead))
    return 0


if __name__ == "__main__":
    sys.exit(main())
