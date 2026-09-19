"""Agreement at depth: the derived feeder against the walker, across two retirements."""
import random
import sys
import time

sys.path.insert(0, ".")
from spec import Cfg, Jump, Walk  # noqa: E402


def cfg_for(seed=3, n=120, cap=2048):
    rng = random.Random(seed)
    lens = [[rng.randint(16, 3200) for _ in range(n)] for _ in range(4)]
    good = [sum(1 for v in ls if v <= cap) for ls in lens]
    mix = [0, 1, 2, 3, 0, 2, 3, 1]
    allow = [0, 0, 0, 0]
    allow[1] = max(1, (200_000 * 2 // 8) // good[1])       # retires near slot 200k
    allow[3] = max(1, (1_200_000 * 2 // 8) // good[3])     # and near slot 1.2M
    return Cfg(rng.getrandbits(48), cap, ["s0", "s1", "s2", "s3"], lens, allow, mix)


def main():
    cfg = cfg_for()
    jump = Jump(cfg)
    horizon = 2_000_000
    jump.grow(horizon)
    print("segments: %s" % ([(s, p) for s, p, _t in jump.segs],), flush=True)

    t0 = time.time()
    walk = Walk(cfg)
    rng = random.Random(11)
    marks = sorted(rng.sample(range(horizon), 30)) + [horizon]
    bad = 0
    for m in marks:
        walk.upto(m)
        w = [("gone",) if walk.gone[j] else (walk.ep[j], walk.cur[j], walk.took[j])
             for j in range(4)]
        g = jump.state(m)
        if w != g:
            print("state differs at %d:\n  walk %s\n  jump %s" % (m, w, g), flush=True)
            bad += 1
    print("walked %d slots in %.1f s" % (horizon, time.time() - t0), flush=True)

    # and the stream itself, in windows on both sides of each retirement
    for start, _p, _t in jump.segs:
        for at in (max(0, start - 30), start, start + 1):
            if Walk(cfg).slots(at, 64) != jump.slots(at, 64):
                print("stream differs at %d" % at, flush=True)
                bad += 1
    print("%d disagreements" % bad, flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
