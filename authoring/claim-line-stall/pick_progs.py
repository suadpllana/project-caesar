"""Search for shipped example programs, rather than choosing them.

`small.txt` has to differ from the reference in exactly one line - the one the brief names -
and separate as few of the wrong readings as possible. `mix.txt` has to differ nowhere, so it
demonstrates the op language and settles nothing.
"""
import pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests")); sys.path.insert(0, str(HERE))
import lab

MODS = ("ops","hold","hold.name","hold.say","hold.book","hold.line","hold.lift","hold.knot","hold.turn","hold.act")

def load(over):
    here = lab.stage(over); sys.path.insert(0, str(here))
    for n in MODS: sys.modules.pop(n, None)
    import ops as mod
    from hold import book as bk
    sys.path.remove(str(here)); return mod, bk

def run(pair, lines):
    mod, bk = pair
    h = bk.Hold()
    for l in lines: mod.ex(h, tuple(l.split()))
    return h.out

REF = load(str(TASK / "solution"))
SHIP = load("")
ROOMS = sorted((HERE / "readings").iterdir())
READ = {r.name: load(str(r)) for r in ROOMS}

def report(name, lines):
    a, b = run(REF, lines), run(SHIP, lines)
    diff = [i for i in range(max(len(a), len(b)))
            if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)]
    sep = [n for n, pair in READ.items() if run(pair, lines) != a]
    print("%s: %d lines, shipped differs on %s, separates %d readings %s"
          % (name, len(a), diff, len(sep), sep))
    return a, b, diff, sep

SMALL = """take j1 u1/c1 w
take j2 u2/c1 r
take j2 u1/c2 r
show u1
drop j2 u1/c2
end j2
take j1 u1/c1 r
take j3 u1/c1 r""".splitlines()

MIX = """take j1 u1/c1 r
take j2 u1/c1 r
take j3 u1/c2 w
show u1
take j4 u2/c1 w
drop j1 u1/c1
end j3
show u1
show u2
end j4
show u2""".splitlines()

for nm, prog in (("small", SMALL), ("mix", MIX)):
    a, b, diff, sep = report(nm, prog)
    print("   reference:"); print("   " + "\n   ".join(a))
    print("   shipped:"); print("   " + "\n   ".join(b))
