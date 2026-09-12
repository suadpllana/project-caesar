"""Time the sealed model over the whole generated set."""
import pathlib, sys, time
HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests")); sys.path.insert(0, str(TASK / "tests" / "seal"))
import gen, model
per = int(sys.argv[1]) if len(sys.argv) > 1 else 45
spent, ops = {}, {}
for fam, name, lines in gen.programs("timing-seed", per):
    t0 = time.time()
    model.expect(lines)
    spent[fam] = spent.get(fam, 0.0) + time.time() - t0
    ops[fam] = ops.get(fam, 0) + len(lines)
tot = 0.0
for fam in sorted(spent):
    print("%-6s %8.2f s  %9d ops" % (fam, spent[fam], ops[fam]), flush=True); tot += spent[fam]
print("model total %8.2f s" % tot, flush=True)
