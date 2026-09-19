"""Does the gate bite? Measure the derived feeder against the families that walk.

Three correct families are timed at the scale the brief will state:

  walk       every slot, in order, keeping cursors                  (what ships)
  stream     pattern counts derived, but each source's own stream
             walked from its first sample to find where it stands
  jump       counts derived and the delivered count turned into an
             epoch and a position                                    (the reference)

and one that is correct and fat: every epoch's hand-over order kept.
"""
import resource
import sys
import time

sys.path.insert(0, ".")
from spec import Cfg, Jump, Walk, perm  # noqa: E402


def big(seed=7, k=4, n=400, cap=2048):
    import random
    rng = random.Random(seed)
    lens, names, allow = [], [], []
    for j in range(k):
        ls = [rng.randint(16, 3200) for _ in range(n)]
        if not any(v <= cap for v in ls):
            ls[0] = 100
        lens.append(ls)
        names.append("s%d" % j)
    good = [sum(1 for v in ls if v <= cap) for ls in lens]
    # one source retires early, one deep inside the run, two run forever
    allow = [0, 40, 0, 0]
    per = [0.25] * k
    mix = [0, 1, 2, 3, 0, 2, 3, 1]
    # place the deep retirement near slot 1.2e8: source 3 holds 2 of 8 pattern slots
    want = 120_000_000 * 2 // 8
    allow[3] = max(1, want // good[3])
    return Cfg(rng.getrandbits(48), cap, names, lens, allow, mix), good


def rate(cfg, slots):
    w = Walk(cfg)
    t0 = time.time()
    w.upto(slots)
    return slots / (time.time() - t0)


def stream_state(cfg, j, took):
    """Correct, and the first repair a walker reaches for: walk this source's own stream."""
    cur = ep = 0
    left = took
    while left:
        order = perm(cfg.seed, j, ep, cfg.n[j])
        while cur < cfg.n[j] and left:
            if cfg.lens[j][order[cur]] <= cfg.cap:
                left -= 1
            cur += 1
        if cur == cfg.n[j]:
            cur = 0
            ep += 1
    return (ep, cur)


def main():
    cfg, good = big()
    target = 200_000_000
    print("sources %d, samples each %d, within cap %s, allowances %s"
          % (len(cfg.lens), cfg.n[0], good, cfg.allow), flush=True)

    jm = Jump(cfg)
    t0 = time.time()
    st = jm.state(target)
    got = jm.slots(target, 256)
    jump_s = time.time() - t0
    print("jump   state+one step at slot %d: %.4f s  %s" % (target, jump_s, st), flush=True)

    t0 = time.time()
    for q in range(40):
        j2 = Jump(cfg)
        j2.state(target - q * 977_771)
        j2.slots(target - q * 977_771, 256)
    print("jump   40 cold queries: %.3f s" % (time.time() - t0), flush=True)

    probe = 400_000
    r = rate(cfg, probe)
    print("walk   %.0f slots/s measured over %d slots -> %.0f s for %d slots"
          % (r, probe, target / r, target), flush=True)

    took = jm.took(target)
    t0 = time.time()
    sub = 300_000
    stream_state(cfg, 0, sub)
    sr = sub / (time.time() - t0)
    print("stream %.0f samples/s -> %.0f s for source 0 alone (%d delivered)"
          % (sr, took[0] / sr, took[0]), flush=True)

    # the fat family: hold every epoch's hand-over order
    epochs = took[0] // good[0]
    print("fat    source 0 reaches epoch %d; %d ints of order kept = %.1f GB"
          % (epochs, epochs * cfg.n[0], epochs * cfg.n[0] * 28 / 1e9), flush=True)
    print("peak rss %.0f MB" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,),
          flush=True)


if __name__ == "__main__":
    main()
