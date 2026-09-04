"""Is the pinned script composable? Carrying a line revision by revision
versus diffing the note's origin revision straight against the current one."""
import random, sys
sys.path.insert(0, '/home/user/project-caesar/tasks/note-carry-forward/environment/app_src')
from scr import pin

rng = random.Random(1)
N = int(sys.argv[1])
steps_diff = 0; total = 0; alive_diff = 0
for _ in range(N):
    k = rng.randrange(2, 6)
    pool = ["ln%d" % i for i in range(k)]
    n = rng.randrange(8, 20)
    revs = [[rng.choice(pool) for _ in range(n)]]
    for _ in range(rng.randrange(2, 5)):
        nxt = list(revs[-1])
        for _ in range(rng.randrange(1, 4)):
            p = rng.randrange(max(1, len(nxt))); z = rng.randrange(3)
            if z == 0 and len(nxt) > 1: del nxt[p]
            elif z == 1: nxt.insert(p, rng.choice(pool))
            else: nxt[p] = rng.choice(pool)
        revs.append(nxt)
    # step-by-step carry of every origin line
    step = {i: i for i in range(len(revs[0]))}
    for t in range(len(revs) - 1):
        c = pin.carried(revs[t], revs[t + 1])
        step = {o: c[p] for o, p in step.items() if p in c}
    direct = pin.carried(revs[0], revs[-1])
    total += 1
    if step != direct: steps_diff += 1
    if set(step) != set(direct): alive_diff += 1
print("streams %d" % total)
print("  step-by-step carry differs from origin-to-current: %d (%.1f%%)" % (steps_diff, 100.0*steps_diff/total))
print("  ... and they disagree about WHICH notes survive:   %d (%.1f%%)" % (alive_diff, 100.0*alive_diff/total))
