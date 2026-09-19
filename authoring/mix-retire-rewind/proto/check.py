"""Differential test: the derived feeder against the one that walks every slot.

Both are driven over random configurations, including ones shaped so that a retirement lands
mid-stretch, an epoch's last sample is over the cap, and a source runs entirely inside it.
"""
import random
import sys

sys.path.insert(0, ".")
from spec import Cfg, Jump, Walk, deal  # noqa: E402


def make(rng):
    k = rng.randint(2, 5)
    cap = rng.choice([40, 64, 100])
    lens, allow, names = [], [], []
    for j in range(k):
        n = rng.randint(3, 14)
        shape = rng.choice(["clean", "hot", "mixed", "tail"])
        ls = []
        for i in range(n):
            if shape == "clean":
                ls.append(rng.randint(1, cap))
            elif shape == "hot":
                ls.append(rng.randint(1, cap * 2))
            elif shape == "tail":
                ls.append(cap + rng.randint(1, 50) if i >= n - 2 else rng.randint(1, cap))
            else:
                ls.append(rng.randint(1, cap) if rng.random() < 0.7 else cap + rng.randint(1, 60))
        if not any(v <= cap for v in ls):
            ls[rng.randrange(n)] = rng.randint(1, cap)
        lens.append(ls)
        names.append("s%d" % j)
        allow.append(0 if j == 0 else rng.choice([0, 1, 2, 3, rng.randint(4, 40)]))
    mix = []
    for _ in range(rng.randint(1, 4)):
        for j in range(k):
            if rng.random() < 0.7:
                mix.append(j)
    if not mix:
        mix = [0]
    if 0 not in mix:
        mix.append(0)
    rng.shuffle(mix)
    return Cfg(rng.getrandbits(48), cap, names, lens, allow, mix)


def main(rounds=400):
    bad = 0
    for t in range(rounds):
        rng = random.Random(t)
        cfg = make(rng)
        walk, jump = Walk(cfg), Jump(cfg)
        horizon = rng.randint(40, 900)
        a = walk.slots(0, horizon)
        b = jump.slots(0, horizon)
        if a != b:
            first = next(i for i in range(len(a)) if a[i] != b[i])
            print("round %d: stream differs at slot %d: %s vs %s" % (t, first, a[first], b[first]))
            bad += 1
            continue
        for slot in sorted(rng.sample(range(horizon), min(12, horizon))):
            w = Walk(cfg).state(slot)
            j = jump.state(slot)
            if w != j:
                print("round %d: state at %d differs: %s vs %s" % (t, slot, w, j))
                bad += 1
                break
        else:
            at = rng.randrange(max(1, horizon - 60))
            if Walk(cfg).slots(at, 40) != jump.slots(at, 40):
                print("round %d: mid-stream slots differ from %d" % (t, at))
                bad += 1
    print("%d rounds, %d disagreements" % (rounds, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 400))
