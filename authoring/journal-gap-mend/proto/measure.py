import random, sys, time
from gen import random_journal
import settle
from readings import READINGS


def classify(out):
    kinds = {"full": 0, "partial": 0, "none": 0}
    cur = None
    n = 0
    for line in out:
        if line.startswith("gap"):
            if cur is not None:
                kinds[cur] += 1
            cur = "full"
            n = 0
        elif line.startswith("?"):
            cur = "partial" if n else "none"
        else:
            n += 1
    if cur is not None:
        kinds[cur] += 1
    return kinds


def run(seed, N, **kw):
    rng = random.Random(seed)
    moved = {k: 0 for k in READINGS}
    mix = {"full": 0, "partial": 0, "none": 0}
    t = time.time()
    for trial in range(N):
        cfg, items, events, spans = random_journal(rng, **kw)
        ref = settle.restore(cfg, items)
        for k, v in classify(ref).items():
            mix[k] += v
        for name, fn in READINGS.items():
            if fn(cfg, items) != ref:
                moved[name] += 1
    tot = sum(mix.values())
    print("journals %d  spans full %.0f%% partial %.0f%% none %.0f%%  (%.1fs)" % (
        N, 100 * mix["full"] / tot, 100 * mix["partial"] / tot, 100 * mix["none"] / tot,
        time.time() - t), flush=True)
    for name, c in moved.items():
        print("  %-16s moves %5.1f%% of journals" % (name, 100.0 * c / N), flush=True)


if __name__ == "__main__":
    run(int(sys.argv[1]), int(sys.argv[2]))
