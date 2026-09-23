"""Prototype of the large streaming family, and the three tiers timed on it.

Before the contract is frozen the scale gate has to be measured, not argued (CLAUDE.md,
reach-pair-sweep): the plain plan (plans for spinners only, every sum issue stepped), the
device-wide plan (plans that end whenever anything else issues anywhere) and the local plan
(plans that end only on what their own multiprocessor can observe) all run the same launch,
each under a wall clock, and must agree where they finish.

usage: python3 -u authoring/stale-line-spin/proto_stream.py [seed] [clock-seconds] [mode ...]
"""
import random
import signal
import sys
import time

sys.path.insert(0, "tasks/stale-line-spin/tests/seal")
import model  # noqa: E402


def stream(rng, R=6, C=32, NRED=8, T=33, N=20000, K=2000, W=2000):
    S = 16
    G = S * R
    DATA = 1 << 20
    RES = 4096
    PROG = 8192
    body = [
        "mov r1 %bid",
        "mov r2 %sm",
        "slt r3 r2 %d" % NRED,
        "brz r3 worker",
        "mov r4 0",
        "rloop:",
        "mul r5 r1 %d" % T,
        "add r5 r5 r4",
        "mul r6 r5 %d" % (4 * N),
        "add r6 r6 %d" % DATA,
        "%s r0 [r6+0] %d" % (rng.choice(("sum.ca", "sum.cg")), N),
        "st [r5+%d] r0" % RES,
        "add r4 r4 1",
        "sub r7 r4 %d" % T,
        "brnz r7 rloop",
        "out r0",
        "exit",
        "worker:",
        "mov r4 0",
        "wloop:",
        "mul r5 r4 %d" % rng.randint(3, 17),
        "add r5 r5 r1",
        "mod r5 r5 %d" % (W // 4),
        "add r5 r5 %d" % (W - W // 8),
        "work r5",
        "st [r1+%d] r4" % PROG,
        "add r4 r4 1",
        "sub r7 r4 %d" % K,
        "brnz r7 wloop",
        "exit",
    ]
    mem = []
    for _ in range(400):
        tile = rng.randrange(NRED * R * T)
        mem.append((DATA + tile * 4 * N + rng.randrange(4 * N), rng.randint(1, 9)))
    lines = ["dev %d %d %d" % (S, R, C), "grid %d" % G]
    lines += ["mem %d %d" % mv for mv in mem]
    lines.append("show %d %d" % (RES, PROG + G - 1))
    lines.append("prog")
    return lines + body


class Late(Exception):
    pass


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "p1"
    clock = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    modes = sys.argv[3:] or ["local", "device", "spins"]
    lines = stream(random.Random(seed))

    def late(*_):
        raise Late()

    signal.signal(signal.SIGALRM, late)
    outs = {}
    for mode in modes:
        signal.alarm(clock)
        t0 = time.time()
        try:
            outs[mode] = model.expect(lines, mode)
            dt = time.time() - t0
            ends = [int(x.split()[7]) for x in outs[mode] if x.startswith("blk")]
            print("%-7s %6.1fs  last exit %d" % (mode, dt, max(ends)), flush=True)
        except Late:
            print("%-7s  over %ds" % (mode, clock), flush=True)
        signal.alarm(0)
    done = list(outs.values())
    print("agree:", all(o == done[0] for o in done), flush=True)


if __name__ == "__main__":
    main()
