import random, time, sys
from core import fmt
from gen import random_journal
import settle, brute, topdown

rng = random.Random(int(sys.argv[1]))
N = int(sys.argv[2])
agree = bagree = bskip = 0
t_ref = t_td = 0.0
worst = 0
for trial in range(N):
    cfg, items, events, spans = random_journal(rng)
    t0 = time.time(); ref = settle.restore(cfg, items); t1 = time.time()
    td = topdown.solve(cfg, items); t2 = time.time()
    t_ref += t1 - t0; t_td += t2 - t1; worst = max(worst, t1 - t0)
    if ref != td:
        print("MISMATCH settle/topdown", trial, flush=True)
        print(fmt(cfg, items)); print("ref", ref); print("td ", td)
        break
    agree += 1
    try:
        accs = brute.accounts(cfg, items, budget=200000)
        br = brute.restore(cfg, items, accs=accs)
        if br != ref:
            print("MISMATCH settle/brute", trial, flush=True)
            print(fmt(cfg, items)); print("ref", ref); print("br ", br)
            break
        bagree += 1
    except brute.Budget:
        bskip += 1
print("settle=topdown on", agree, "of", N, "| brute agreed", bagree, "over budget", bskip,
      "| settle %.2fs (worst %.2fs) topdown %.2fs" % (t_ref, worst, t_td), flush=True)
