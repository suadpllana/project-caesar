import random, sys, time, signal
from gen import random_journal
import settle

class TO(Exception): pass
def alarm(*a): raise TO()
signal.signal(signal.SIGALRM, alarm)

for S in (3, 4, 5):
    for maxspan in (4, 6, 8):
        rng = random.Random(1000 + S * 10 + maxspan)
        times = []; over = 0; worst_nodes = 0
        for t in range(60):
            cfg, items, ev, spans = random_journal(rng, L=(2, 4), S=(S, S), maxspan=maxspan, n=(20, 40))
            signal.alarm(20)
            t0 = time.time()
            try:
                tr, gl = settle.settle(cfg, items)
                signal.alarm(0)
                times.append(time.time() - t0)
                worst_nodes = max(worst_nodes, sum(len(x[2]) for x in tr if x[0] == "gap"))
            except TO:
                over += 1
        times.sort()
        print("S=%d maxspan=%d  median %.3fs  p95 %.3fs  max %.2fs  over20s %d  worst nodes %d" % (
            S, maxspan, times[len(times)//2], times[int(len(times)*0.95)], times[-1], over, worst_nodes), flush=True)
