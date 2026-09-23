"""Launch files generated from a seed drawn after the agent's container is gone.

The families are shaped around the machine's rules rather than sampled from the space of
programs. An unshaped population almost never makes a cached line go stale, almost never
places a later block where an earlier one cached something, and almost never has a spinner
whose line another block's fill pushes out, so every wrong reading would score like the right
one on it. Each family below is a real inter-block pattern of ML kernels, written with the
choices that decide what the machine does - cached or bypassing, fenced or not, flag set by a
store or by an atomic, a cache of one line or of several - drawn at random.

  fixup     split-K partials: every segment stores its partial and raises a flag, the last
            segment of each tile waits for the others and sums what it reads
  barrier   every block counts in and waits for the whole grid, which hangs when the grid is
            larger than the device can hold, and may hang anyway on a cached count
  chain     each block waits for the one before it and bumps a shared accumulator
  queue     persistent blocks claim tiles with an atomic counter; the last block waits for
            all tiles and reads the results back
  stats     early blocks cache a statistics line, one block rewrites it, and blocks placed
            later on the same multiprocessors read it after a flag says it is ready
  thrash    more spun-on lines than a multiprocessor's cache holds, with stores and fills
            arriving from elsewhere
  mix       short random programs of loads, stores, atomics and fences over a few shared
            lines, on caches of one or two lines
  evict     a stale spinner sharing a small cache with a spinner whose misses push lines out,
            while another block is busy or everything else has finished
  wide      the fixup pattern at scale: thousands of blocks, long work, waiting owners
  deep      the chain pattern at scale: one block at a time works while the rest wait
"""
import random

FAMILIES = (
    ("fixup", False),
    ("barrier", False),
    ("chain", False),
    ("queue", False),
    ("stats", False),
    ("thrash", False),
    ("mix", False),
    ("evict", False),
    ("reduce", False),
    ("wide", True),
    ("deep", True),
    ("stream", True),
)

BIG = 3


def _head(dev, grid, mem=(), show=()):
    lines = ["dev %d %d %d" % dev, "grid %d" % grid]
    lines += ["mem %d %d" % (a, v) for a, v in mem]
    if show:
        lines.append("show " + " ".join(str(a) for a in show))
    lines.append("prog")
    return lines


def _lines_after(a):
    """The first word address on a line boundary at or after a."""
    return (a + 3) // 4 * 4


def fixup(rng, big=False):
    if big:
        S, R, C = 16, rng.randint(4, 6), 16
        K, T = 4, rng.randint(800, 1100)
    else:
        S, R, C = rng.randint(2, 4), rng.randint(1, 3), rng.randint(1, 4)
        K, T = rng.randint(2, 4), rng.randint(2, 5)
    G = T * K
    stride = rng.choice((1, 2))
    P = 0
    F = 1 if stride == 2 else _lines_after(G) + 4 * rng.randint(0, 2)
    O = _lines_after(max(P + stride * G, F + stride * G) + 1) + 4
    spin = "spin.cg" if big else rng.choice(("spin.ca", "spin.cg"))
    read = rng.choice(("ld.ca", "ld.cg"))
    raise_flag = rng.choice(("st", "atom"))
    fence_after_store = (not big) and rng.random() < 0.3
    fence_after_spin = (not big) and rng.random() < 0.3
    prefetch = (not big) and rng.random() < 0.5
    if big:
        base = rng.randint(20000, 60000)
        slope = -int(base * rng.uniform(0.7, 0.9) / (K - 1))
    else:
        slope, base = rng.randint(-8, 8), rng.randint(9, 40)
    body = [
        "mov r1 %bid",
        "mod r2 r1 %d" % K,
        "sub r3 r1 r2",
        "mul r5 r1 %d" % stride,
    ]
    if prefetch:
        body.append("ld.ca r7 [r5+%d]" % P)
    body += [
        "mul r6 r2 %d" % slope,
        "add r6 r6 %d" % base,
        "work r6",
        "mul r7 r1 3",
        "add r7 r7 1",
        "st [r5+%d] r7" % P,
    ]
    if fence_after_store:
        body.append("fence")
    body += ["sub r6 r2 %d" % (K - 1), "brz r6 owner"]
    if raise_flag == "st":
        body.append("st [r5+%d] 1" % F)
    else:
        body.append("atom.add r6 [r5+%d] 1" % F)
    body += [
        "exit",
        "owner:",
        "mov r4 0",
        "mov r0 r7",
        "loop:",
        "sub r6 r4 %d" % (K - 1),
        "brz r6 done",
        "add r2 r3 r4",
        "mul r2 r2 %d" % stride,
        "%s r6 [r2+%d] eq 1" % (spin, F),
    ]
    if fence_after_spin:
        body.append("fence")
    body += [
        "%s r6 [r2+%d]" % (read, P),
        "add r0 r0 r6",
        "add r4 r4 1",
        "bra loop",
        "done:",
        "st [r3+%d] r0" % O,
        "out r0",
        "exit",
    ]
    show = [O + K * t for t in range(min(T, 4))]
    return _head((S, R, C), G, show=show) + body


def barrier(rng):
    S, R, C = rng.randint(2, 4), rng.randint(1, 3), rng.randint(1, 4)
    G = rng.randint(2, S * R + 2)
    D = 0
    CNT = _lines_after(G) + 4 * rng.randint(0, 1) + rng.randint(0, 3)
    spin = rng.choice(("spin.ca", "spin.cg"))
    read = rng.choice(("ld.ca", "ld.cg"))
    body = ["mov r1 %bid", "add r5 r1 1", "mod r5 r5 %d" % G]
    if rng.random() < 0.5:
        body.append("ld.ca r7 [r5+%d]" % D)
    body += ["mul r2 r1 3", "add r2 r2 1", "st [r1+%d] r2" % D]
    if rng.random() < 0.6:
        body += ["mul r6 r1 %d" % rng.randint(-5, 5), "add r6 r6 %d" % rng.randint(6, 30),
                 "work r6"]
    body += ["atom.add r3 [%d] 1" % CNT, "%s r4 [%d] ge %%nb" % (spin, CNT)]
    if rng.random() < 0.3:
        body.append("fence")
    body += ["%s r6 [r5+%d]" % (read, D), "out r6", "exit"]
    return _head((S, R, C), G, show=[CNT]) + body


def chain(rng, big=False):
    if big:
        S, R, C = 8, 8, 8
        G = rng.randint(2200, 2800)
        slope, base = rng.randint(1, 3), rng.randint(3000, 9000)
        spin, read = "spin.cg", rng.choice(("ld.ca", "ld.cg"))
    else:
        S, R, C = rng.randint(2, 4), rng.randint(1, 3), rng.randint(1, 4)
        G = rng.randint(3, 10)
        slope, base = rng.randint(-3, 3), rng.randint(4, 25)
        spin, read = rng.choice(("spin.ca", "spin.cg")), rng.choice(("ld.ca", "ld.cg"))
    F = 0
    ACC = _lines_after(G) + rng.randint(0, 3)
    fence = (not big) and rng.random() < 0.3
    raise_flag = rng.choice(("st", "atom"))
    body = ["mov r1 %bid", "brz r1 go", "sub r2 r1 1",
            "%s r3 [r2+%d] eq 1" % (spin, F), "go:"]
    if fence:
        body.append("fence")
    body += ["%s r4 [%d]" % (read, ACC), "add r4 r4 1", "st [%d] r4" % ACC, "out r4",
             "mul r6 r1 %d" % slope, "add r6 r6 %d" % base, "work r6"]
    if raise_flag == "st":
        body.append("st [r1+%d] 1" % F)
    else:
        body.append("atom.add r6 [r1+%d] 1" % F)
    body.append("exit")
    return _head((S, R, C), G, show=[ACC]) + body


def queue(rng):
    S, R, C = rng.randint(2, 4), rng.randint(1, 3), rng.randint(1, 4)
    G = rng.randint(2, 8)
    T = rng.randint(3, 12)
    Q = 0
    DONE = 4 * rng.randint(1, 2)
    RES = DONE + 4 + 4 * rng.randint(0, 1)
    spin = rng.choice(("spin.ca", "spin.cg"))
    read = rng.choice(("ld.ca", "ld.cg"))
    accumulate = rng.random() < 0.6
    body = ["mov r1 %bid", "sub r2 r1 %d" % (G - 1), "brz r2 reducer", "loop:",
            "atom.add r3 [%d] 1" % Q, "slt r4 r3 %d" % T, "brz r4 finish",
            "mul r5 r3 %d" % rng.randint(-2, 4), "add r5 r5 %d" % rng.randint(6, 30),
            "work r5", "mul r6 r3 5", "add r6 r6 2"]
    if accumulate:
        body += ["ld.ca r0 [r3+%d]" % RES, "add r6 r6 r0"]
    body += ["st [r3+%d] r6" % RES, "atom.add r7 [%d] 1" % DONE, "bra loop",
             "finish:", "exit", "reducer:", "%s r3 [%d] ge %d" % (spin, DONE, T)]
    if rng.random() < 0.3:
        body.append("fence")
    body += ["mov r4 0", "mov r0 0", "rl:", "slt r5 r4 %d" % T, "brz r5 rdone",
             "%s r6 [r4+%d]" % (read, RES), "add r0 r0 r6", "add r4 r4 1", "bra rl",
             "rdone:", "out r0", "exit"]
    mem = [(RES + i, rng.randint(0, 3)) for i in range(T) if rng.random() < 0.4]
    return _head((S, R, C), G, mem=mem, show=[Q, DONE]) + body


def stats(rng):
    S, R, C = rng.randint(2, 3), rng.randint(1, 2), rng.randint(1, 4)
    G = rng.randint(6, 12)
    H = rng.randint(1, G - 2)          # blocks 0..H-1 cache the line, block H rewrites it
    STAT = 4 * rng.randint(0, 2) + rng.randint(0, 3)
    READY = STAT if rng.random() < 0.2 else _lines_after(STAT + 1) + 4 * rng.randint(0, 1)
    OUT = 32
    read = rng.choice(("ld.ca", "ld.cg"))
    body = ["mov r1 %bid", "slt r2 r1 %d" % H, "brz r2 later",
            "ld.ca r3 [%d]" % STAT,
            "mul r6 r1 %d" % rng.randint(-3, 3), "add r6 r6 %d" % rng.randint(5, 25),
            "work r6", "add r3 r3 r1", "st [r1+%d] r3" % OUT, "exit",
            "later:", "sub r2 r1 %d" % H, "brnz r2 wait",
            "work %d" % rng.randint(3, 40), "st [%d] %d" % (STAT, rng.randint(5, 99))]
    if READY == STAT:
        body += ["exit", "wait:", "spin.cg r4 [%d] ge 5" % READY]
    else:
        body += ["st [%d] 1" % READY, "exit", "wait:", "spin.cg r4 [%d] eq 1" % READY]
    if rng.random() < 0.25:
        body.append("fence")
    body += ["%s r5 [%d]" % (read, STAT), "out r5", "exit"]
    mem = [(STAT, rng.randint(1, 4))]
    return _head((S, R, C), G, mem=mem, show=[STAT]) + body


def thrash(rng):
    S = rng.randint(1, 2)
    spinners = rng.randint(2, 5)
    setters = rng.randint(1, 2)
    G = spinners + setters
    R = -(-G // S) + rng.randint(0, 1)          # every block resident at once
    per_sm = max(1, spinners // S)
    C = max(1, per_sm + rng.choice((-2, -1, -1, 0, 1)))
    FL = 4
    body = ["mov r1 %bid", "slt r2 r1 %d" % spinners, "brz r2 setter",
            "mul r3 r1 4"]
    if rng.random() < 0.6:
        body.append("ld.ca r5 [r3+%d]" % FL)
    body += ["spin.ca r4 [r3+%d] ge 1" % FL, "out r4", "exit", "setter:",
             "sub r3 r1 %d" % spinners]
    set_all = rng.random() < 0.8
    body += ["work %d" % rng.randint(2, 30)]
    for i in range(spinners):
        if set_all or rng.random() < 0.5:
            how = rng.choice(("st", "atom"))
            if how == "st":
                body.append("st [%d] 1" % (FL + 4 * i))
            else:
                body.append("atom.add r6 [%d] 1" % (FL + 4 * i))
            if rng.random() < 0.4:
                body.append("ld.ca r7 [%d]" % (64 + 4 * rng.randint(0, 6)))
            if rng.random() < 0.3:
                body.append("work %d" % rng.randint(1, 12))
    body.append("exit")
    return _head((S, R, C), G, show=[FL + 4 * i for i in range(spinners)]) + body


def mix(rng):
    S, R, C = rng.randint(2, 3), rng.randint(1, 2), rng.randint(1, 2)
    G = rng.randint(3, 6)
    lines = rng.sample(range(0, 6), 3)
    words = [4 * ln + w for ln in lines for w in range(4)]
    body = ["mov r1 %bid", "mul r2 r1 %d" % rng.randint(1, 3), "add r2 r2 1"]
    for _ in range(rng.randint(6, 12)):
        k = rng.random()
        a = rng.choice(words)
        if k < 0.30:
            body += ["%s r3 [%d]" % (rng.choice(("ld.ca", "ld.ca", "ld.cg")), a), "out r3"]
        elif k < 0.48:
            body.append("st [%d] r2" % a)
        elif k < 0.58:
            body.append("atom.add r4 [%d] 1" % a)
        elif k < 0.68:
            body.append("fence")
        elif k < 0.88:
            body += ["mul r5 r1 %d" % rng.randint(-3, 3), "add r5 r5 %d" % rng.randint(2, 14),
                     "work r5"]
        else:
            body.append("add r2 r2 %d" % rng.randint(1, 4))
    body.append("exit")
    mem = [(w, rng.randint(0, 9)) for w in words if rng.random() < 0.4]
    return _head((S, R, C), G, mem=mem, show=sorted(rng.sample(words, 3))) + body


def evict(rng):
    """A stale spinner released only by a second spinner's miss on the same multiprocessor.

    Block 0 caches its flag and then spins on it; block 3 raises the flag with an atomic after
    that fill, so block 0's copy is stale and every attempt it makes hits and fails. Block 2
    starts spinning later, on a line that is not cached: its miss pushes block 0's line out
    when the cache holds one line, or its bypassing attempt drops the line when the two flags
    share it. Block 1 works for a long stretch on the other multiprocessor - sometimes ending
    before block 2 arrives, so every block left is spinning, and sometimes still busy then.
    """
    S, R = 2, rng.randint(2, 3)
    C = rng.choice((1, 1, 1, 2))
    FA = 4 * rng.randint(20, 22)
    same_line = rng.random() < 0.25
    FB = FA + rng.randint(1, 3) if same_line else FA + 4 * rng.randint(1, 3)
    b_spin = rng.choice(("spin.cg", "spin.ca")) if same_line else rng.choice(
        ("spin.ca", "spin.ca", "spin.cg"))
    b_work = rng.randint(22, 40)
    w_work = rng.randint(8, 16) if rng.random() < 0.5 else rng.randint(60, 120)
    body = ["mov r1 %bid", "brz r1 a", "sub r2 r1 1", "brz r2 w", "sub r2 r1 2", "brz r2 b",
            "work %d" % rng.randint(10, 16), "atom.add r6 [%d] 1" % FA, "exit",
            "a:", "ld.ca r5 [%d]" % FA, "work %d" % rng.randint(2, 8),
            "spin.ca r4 [%d] eq 1" % FA, "out r4", "exit",
            "b:", "work %d" % b_work, "%s r4 [%d] eq 1" % (b_spin, FB), "out r4", "exit",
            "w:", "work %d" % w_work]
    if rng.random() < 0.5:
        body.append(rng.choice(("st [%d] 1", "atom.add r6 [%d] 1")) % FB)
    body.append("exit")
    return _head((S, R, C), 4, show=[FA, FB]) + body


def reduce(rng):
    """A tile summed by one block while the machine around it moves the tile's lines.

    The tile is n lines. What varies is the one thing that decides the total or the timing:
      stale     the reducer cached a line of the tile before a writer changed it; whether its
                sum still finds the copy depends on how many lines a neighbour's sum filled since
      release   a waiter holds a stale copy of its flag; it is let go only when a neighbour's
                cached sum pushes the line out, or a bypassing sum passes over it and drops it
      race      writers on a lower- and a higher-numbered multiprocessor store into the tile
                around the cycles the sum reaches those lines
      trail     two sums on one multiprocessor cover overlapping lines, one behind the other,
                while a writer changes a shared line between their reads
    Every block is resident from the start: block b is on multiprocessor b mod S.
    """
    S = rng.randint(2, 4)
    shape = rng.choice(("stale", "release", "race", "trail"))
    R = rng.randint(2, 3)
    C = rng.randint(1, 6)
    n = rng.randint(2, 8)
    TILE = 4 * rng.randint(2, 6)
    FLAG = TILE + 4 * n + 4 * rng.randint(0, 2) + rng.randint(0, 3)
    SIDE = (FLAG // 4 + 1 + rng.randint(0, 2)) * 4        # lines a bystander streams over
    tile_words = [TILE + i for i in range(4 * n)]
    mem = [(w, rng.randint(1, 9)) for w in tile_words if rng.random() < 0.4]
    mem += [(SIDE + i, rng.randint(1, 5)) for i in range(0, 32, 5) if rng.random() < 0.5]
    kind = lambda: rng.choice(("sum.ca", "sum.ca", "sum.cg"))  # noqa: E731
    scripts = {}

    def at(sm, slot=0):
        return sm + S * slot

    def writer(times):
        out = []
        for w, v in times:
            out += ["work %d" % w, "st [%d] %d" % (rng.choice(tile_words), v)]
        return out

    if shape == "stale":
        d = rng.randint(0, n - 1)
        red = ["ld.ca r7 [%d]" % (TILE + 4 * d + rng.randint(0, 3)),
               "spin.cg r6 [%d] ge 1" % FLAG]
        if rng.random() < 0.2:
            red.append("fence")
        red += ["%s r0 [%d] %d" % (kind(), TILE + rng.randint(0, 3), n), "out r0"]
        scripts[at(0)] = red
        scripts[at(1)] = ["work %d" % rng.randint(2, 12),
                          "st [%d] %d" % (TILE + 4 * d + rng.randint(0, 3), rng.randint(10, 40))]
        scripts[at(1)] += writer([(rng.randint(0, 4), rng.randint(10, 40))
                                  for _ in range(rng.randint(0, 2))])
        scripts[at(1)].append(rng.choice(("st [%d] 1", "atom.add r6 [%d] 1")) % FLAG)
        if R > 1 and rng.random() < 0.8:
            scripts[at(0, 1)] = ["work %d" % rng.randint(1, 20),
                                 "sum.ca r0 [%d] %d" % (SIDE, rng.randint(1, 3 * C + 2)), "out r0"]
    elif shape == "release":
        waiter = ["ld.ca r7 [%d]" % FLAG, "spin.ca r6 [%d] ge 1" % FLAG, "out r6"]
        scripts[at(0)] = waiter
        scripts[at(1)] = ["work %d" % rng.randint(1, 8),
                          rng.choice(("st [%d] 1", "atom.add r6 [%d] 1")) % FLAG]
        how = rng.choice(("evict", "evict", "drop"))
        if how == "evict":
            scripts[at(0, 1)] = ["work %d" % rng.randint(8, 20),
                                 "sum.ca r0 [%d] %d" % (SIDE, rng.randint(1, C + 3)), "out r0"]
        else:
            lo = FLAG // 4 - rng.randint(0, 2)
            scripts[at(0, 1)] = ["work %d" % rng.randint(8, 20),
                                 "sum.cg r0 [%d] %d" % (4 * lo, rng.randint(1, 5)), "out r0"]
        if R > 2 and rng.random() < 0.5:
            scripts[at(0, 2)] = ["work %d" % rng.randint(1, 30),
                                 "%s r0 [%d] %d" % (kind(), SIDE + 16, rng.randint(1, 6)), "out r0"]
    elif shape == "race":
        red_sm = rng.randint(1, S - 1) if S > 2 else 1
        w0 = rng.randint(0, 6)
        scripts[at(red_sm)] = ["work %d" % w0, "%s r0 [%d] %d" % (kind(), TILE, n), "out r0"]
        for sm in {0, rng.randint(0, S - 1)} | ({S - 1} if S > 2 else set()):
            if sm == red_sm:
                continue
            scripts[at(sm)] = writer([(rng.randint(w0, w0 + 2 * n), rng.randint(10, 60))
                                      for _ in range(rng.randint(1, 3))])
        if R > 1 and rng.random() < 0.6:
            scripts[at(red_sm, 1)] = ["work %d" % rng.randint(0, 4),
                                      "%s r0 [%d] %d" % (kind(), SIDE, rng.randint(1, 2 * n)),
                                      "out r0"]
    else:
        lag = rng.randint(1, 3)
        scripts[at(0)] = ["%s r0 [%d] %d" % (kind(), TILE, n), "out r0"]
        scripts[at(0, 1)] = ["work %d" % rng.randint(0, 2 * lag + 2),
                             "%s r0 [%d] %d" % (kind(), TILE + 4 * rng.randint(0, 1), n),
                             "out r0"]
        scripts[at(1)] = writer([(rng.randint(0, 3 * n), rng.randint(10, 60))
                                 for _ in range(rng.randint(1, 2))])
    G = max(scripts) + 1
    R = max(R, -(-G // S))
    body = ["mov r1 %bid"]
    for b in sorted(scripts):
        body += ["sub r2 r1 %d" % b, "brz r2 b%d" % b]
    body.append("exit")
    for b in sorted(scripts):
        body.append("b%d:" % b)
        body += scripts[b]
        body.append("exit")
    show = [TILE, TILE + 4 * (n - 1) + 3, FLAG]
    return _head((S, R, C), G, mem=sorted(set(mem)), show=show) + body


def stream(rng):
    """Persistent reducers on most multiprocessors, persistent workers on the rest.

    Every block is resident from cycle 0, and a block's role comes from its multiprocessor:
    one multiprocessor in four runs workers. A reducer sums T tiles of N lines each - cached on
    even multiprocessors, bypassing on odd ones - touching a line a few lines into each tile
    first, and counts every tile done with an atomic. A worker loops K times: work, then a
    store a fixed stride further down through the tiles, each worker at its own pace, so a few
    stores land in a tile while its reducer is reading it and most land far away. A few blocks on bypassing multiprocessors
    watch the done-count through their own cache and are only let go when a fence on their
    multiprocessor drops the stale copy.
    """
    S, P = 16, 4
    R = rng.randint(5, 6)
    C = rng.choice((16, 24, 32, 48))
    G = S * R
    off = rng.randint(0, P - 1)
    T = rng.randint(30, 50)
    N = rng.randint(30000, 50000)
    K = rng.randint(7000, 9000)
    DATA = 1 << 20
    DONE = 64
    RES = 128
    SPAN = G * T * 4 * N
    fence = rng.random() < 0.6
    ahead = rng.randint(0, 6)
    workers = [s for s in range(S) if s % P == off]
    odd = [s for s in range(1, S, 2) if s % P != off]
    watchers = set()
    for s in rng.sample(odd, rng.randint(0, min(3, len(odd)))):
        watchers.add(s + S * rng.randint(0, R - 1))
    reducers = (S - len(workers)) * R - len(watchers)
    target = rng.randint(T, reducers * T // 2)
    body = ["mov r1 %bid"]
    for b in sorted(watchers):
        body += ["sub r2 r1 %d" % b, "brz r2 watch"]
    body += ["mov r2 %sm", "mod r7 r2 %d" % P]
    if off:
        body.append("sub r7 r7 %d" % off)
    body += ["brz r7 worker", "mod r7 r2 2", "mul r5 r1 %d" % T, "mov r4 %d" % T,
             "brnz r7 cg"]
    for tag, op in (("ca", "sum.ca"), ("cg", "sum.cg")):
        body += ["%s:" % tag,
                 "mul r6 r5 %d" % (4 * N),
                 "ld.ca r7 [r6+%d]" % (DATA + 4 * ahead),
                 "%s r0 [r6+%d] %d" % (op, DATA, N),
                 "add r3 r3 r0"]
        if fence:
            body.append("fence")
        body += ["atom.add r7 [%d] 1" % DONE,
                 "add r5 r5 1",
                 "sub r4 r4 1",
                 "brnz r4 %s" % tag,
                 "st [r1+%d] r3" % RES,
                 "out r3",
                 "exit"]
    step = rng.randint(SPAN // K // 2, SPAN // K)
    body += ["watch:",
             "ld.ca r7 [%d]" % DONE,
             "spin.ca r6 [%d] ge %d" % (DONE, target),
             "out r6",
             "exit",
             "worker:",
             "mul r5 r1 %d" % rng.randint(3, 40),
             "mod r5 r5 %d" % 300,
             "add r5 r5 %d" % rng.randint(1000, 1400),
             "mov r6 %d" % (K * step),
             "wloop:",
             "work r5",
             "st [r6+%d] r1" % DATA,
             "sub r6 r6 %d" % step,
             "brnz r6 wloop",
             "exit"]
    mem = set()
    for _ in range(rng.randint(200, 400)):
        tile = rng.randrange(G * T)
        mem.add((DATA + tile * 4 * N + rng.randrange(4 * N), rng.randint(1, 9)))
    show = [DONE, RES + rng.randrange(G), RES + rng.randrange(G)]
    return _head((S, R, C), G, mem=sorted(mem), show=show) + body


GEN = {
    "fixup": lambda rng: fixup(rng),
    "barrier": barrier,
    "chain": lambda rng: chain(rng),
    "queue": queue,
    "stats": stats,
    "thrash": thrash,
    "mix": mix,
    "evict": evict,
    "reduce": reduce,
    "wide": lambda rng: fixup(rng, big=True),
    "deep": lambda rng: chain(rng, big=True),
    "stream": stream,
}


def programs(seed, per):
    """Every generated launch for this seed: (family, name, lines)."""
    out = []
    for fam, big in FAMILIES:
        rng = random.Random("%s:%s" % (seed, fam))
        for i in range(BIG if big else per):
            out.append((fam, "%s-%03d" % (fam, i), GEN[fam](rng)))
    return out
