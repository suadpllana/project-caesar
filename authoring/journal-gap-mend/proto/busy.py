"""A wide family: holders re-entering, lowering depth and beating in any order."""
import random, sys, time, signal
from core import apply, fmt, label
from gen import history, cut
import settle, topdown, brute, naive_exist


def busy(rng, L=3, S=3, K=1, run=(14, 18)):
    holders = list(range(min(L, S)))
    rng.shuffle(holders)
    def pick(rng, step, state, legal):
        # first each holder takes its own lock, then a busy run, then releases
        if step < len(holders):
            want = ("acq", step, holders[step])
            return next(r for r in legal if r[0][:3] == want)
        if step < len(holders) + nrun:
            opts = [r for r in legal if r[0][0] == "beat" or r[0][3] in ("again", "keep")]
            return rng.choice(opts)
        opts = [r for r in legal if r[0][0] == "rel"]
        return rng.choice(opts) if opts else rng.choice(legal)
    nrun = rng.randint(*run)
    ev = history(rng, L, S, K, len(holders) + nrun + 2 * len(holders) + 2, pick=pick)
    n = len(ev)
    s0 = len(holders) + 1
    s1 = s0 + nrun - 2
    mid = rng.randint(s0 + 2, s1 - 2)
    return (L, S, K), cut(ev, [(s0, s1)], [s0 - 1, mid, s1 + 1])


class TO(Exception): pass
def alarm(*a): raise TO()
signal.signal(signal.SIGALRM, alarm)

if __name__ == "__main__":
    rng = random.Random(int(sys.argv[1]))
    for t in range(int(sys.argv[2])):
        cfg, items = busy(rng)
        t0 = time.time(); ref = settle.restore(cfg, items); t1 = time.time()
        tr, gl = settle.settle(cfg, items)
        nodes = sum(len(x[2]) for x in tr if x[0] == "gap")
        td = topdown.solve(cfg, items); t2 = time.time()
        assert td == ref
        res = []
        for name, fn in (("enumerate", lambda: brute.accounts(cfg, items)),
                         ("exist-nomemo", lambda: naive_exist.solve(cfg, items))):
            signal.alarm(30)
            t3 = time.time()
            try:
                out = fn()
                signal.alarm(0)
                res.append("%s %.1fs" % (name, time.time() - t3))
            except TO:
                res.append("%s >30s" % name)
        print(t, "settle %.3fs nodes %d | topdown %.3fs |" % (t1 - t0, nodes, t2 - t1), " | ".join(res), "|", ref[1:3], flush=True)
