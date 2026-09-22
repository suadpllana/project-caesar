"""Hand cases: the model's lines, the plain stepper's agreement, and which readings each separates."""
import sys
sys.path.insert(0, "tasks/stale-line-spin/tests/seal"); sys.path.insert(0, "tasks/stale-line-spin/tests")
sys.path.insert(0, "authoring/stale-line-spin")
import model, cases, naive, switches

want_all = "-v" in sys.argv
sep_by = {r: [] for r in switches.SWITCHES}
for name in cases.ORDER:
    lines = cases.prog(name)
    m = model.expect(lines)
    n = naive.run(lines)
    moved = [r for r in switches.SWITCHES if switches.run(lines, frozenset([r])) != m]
    for r in moved:
        sep_by[r].append(name)
    print("== %-17s naive %s | separates: %s" % (name, "ok" if m == n else "DIFFERS", ", ".join(moved)))
    if want_all:
        print("   " + "\n   ".join(m))
print()
for r, cs in sep_by.items():
    print("%-18s %s" % (r, ", ".join(cs) if cs else "** NO HAND CASE **"))
