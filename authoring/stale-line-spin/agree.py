"""Differential check: the sealed model against the plain stepper on generated launches."""
import sys, time, collections
sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
sys.path.insert(0, "tasks/stale-line-spin/tests")
sys.path.insert(0, "authoring/stale-line-spin")
import model, gen, naive

seeds = sys.argv[1:] or ["s1"]
per = 40
bad = 0
stats = collections.Counter()
for seed in seeds:
    for fam, name, lines in gen.programs(seed, per):
        if fam in ("wide", "deep"):
            continue
        m = model.expect(lines)
        n = naive.run(lines)
        stats[fam, "hang" if any(x.startswith("hang") for x in m) else "ends"] += 1
        if m != n:
            bad += 1
            if bad <= 3:
                print("DIFFER", seed, name)
                print("\n".join(lines))
                for a, b in zip(m, n):
                    if a != b:
                        print("  model:", a, "| naive:", b)
print("disagreements:", bad)
for k in sorted(stats):
    print(k, stats[k])
