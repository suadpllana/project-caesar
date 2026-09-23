"""Time the three tiers of the sealed model on generated launches of one large family.

  local   plans survive what their multiprocessor cannot observe   (the stated fast path)
  device  plans end whenever anything else issues anywhere          (a device-wide bulk step)
  spins   plans hold spinners only; every sum issue is stepped      (the probes' plan)

usage: python3 -u authoring/stale-line-spin/tiers.py <family> <seed> <count> <clock> [mode ...]
"""
import signal
import sys
import time

sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
sys.path.insert(0, "tasks/stale-line-spin/tests")
import gen  # noqa: E402
import model  # noqa: E402


class Late(Exception):
    pass


def late(*_):
    raise Late()


def main():
    fam, seed, count, clock = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    modes = sys.argv[5:] or ["local", "device", "spins"]
    signal.signal(signal.SIGALRM, late)
    import random
    rng = random.Random("%s:%s" % (seed, fam))
    for i in range(count):
        lines = gen.GEN[fam](rng)
        outs = {}
        for mode in modes:
            signal.alarm(clock)
            t0 = time.time()
            try:
                outs[mode] = model.expect(lines, mode)
                ends = [int(x.split()[7]) for x in outs[mode] if x.startswith("blk")]
                print("%s-%d %-6s %7.1fs  last exit %d  hang %s" % (
                    fam, i, mode, time.time() - t0, max(ends) if ends else -1,
                    any(x.startswith("hang") for x in outs[mode])), flush=True)
            except Late:
                print("%s-%d %-6s   over %ds" % (fam, i, mode, clock), flush=True)
            signal.alarm(0)
        done = list(outs.values())
        print("   agree:", all(o == done[0] for o in done), flush=True)


if __name__ == "__main__":
    main()
