"""Each naive family has to produce exactly the reference's traces on the small programs."""
import pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests")); sys.path.insert(0, str(HERE))
import gen, lab

def load(over):
    here = lab.stage(over)
    sys.path.insert(0, str(here))
    for n in ("ops","hold","hold.name","hold.say","hold.book","hold.line","hold.lift","hold.knot","hold.turn","hold.act"):
        sys.modules.pop(n, None)
    import ops as mod
    from hold import book as bk
    sys.path.remove(str(here))
    return mod, bk

def run(mod, bk, lines):
    h = bk.Hold()
    for line in lines: mod.ex(h, tuple(line.split()))
    return h.out

work = [p for p in gen.programs("slowcheck", 30) if p[0] not in ("wide", "tall")]
mod, bk = load(str(TASK / "solution"))
want = {n: run(mod, bk, l) for _f, n, l in work}
for d in sys.argv[1:]:
    mod, bk = load(d)
    bad = [n for _f, n, l in work if run(mod, bk, l) != want[n]]
    print("%-28s %s" % (d, "identical on %d programs" % len(work) if not bad else "DIFFERS: %s" % bad[:3]))
