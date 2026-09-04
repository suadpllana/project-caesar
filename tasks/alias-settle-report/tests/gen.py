"""Build report sets from a nonce drawn after the agent has stopped.

Every collection this turns into a sequence is sorted before it is used. The
runner builds these sets in one process and the grader rebuilds them in another,
and Python randomises string hashing per process, so a set iterated directly
would produce a different file on each side and a correct submission would lose
whichever sets differed.

Legality is maintained while the script is written rather than checked
afterwards: a tie is only ever emitted between two cells that no bar separates,
and a bar is only ever emitted between two cells that are not already one. That
is the input space the instruction states, and it is what makes the question
"what could still happen" answerable at all.

This tracks welds as though every tie landed, which is coarser than what the
machine ends up holding, since a declaration naming a key that has gone is not
an event. Coarser is the safe direction for both rules above: a pair the machine
still holds apart is a pair this already held apart, so a script legal here is
legal there. It is also why nothing in this file may run the machine - what the
machine does depends on the policy under test, and the sets must not.

Watched keys are drawn first and the tag pools are built around them, so the
board is commonly owed several rows whose items one tag can reach.
"""

import random


def _cells(up):
    out = {}
    for k in sorted(up):
        r = k
        while up[r] != r:
            r = up[r]
        out.setdefault(r, []).append(k)
    return out


def _root(up, k):
    while up[k] != k:
        k = up[k]
    return k


def _weld(up, a, b):
    ra, rb = _root(up, a), _root(up, b)
    if ra != rb:
        up[max(ra, rb)] = min(ra, rb)


def _barred(up, bars, a, b):
    ra, rb = _root(up, a), _root(up, b)
    for x, y in sorted(bars):
        rx, ry = _root(up, x), _root(up, y)
        if (rx == ra and ry == rb) or (rx == rb and ry == ra):
            return True
    return False


def shape(rng, wide=False):
    if wide:
        nk = rng.randint(25, 30)
        keys = list(range(1, nk + 1))
        nw = rng.randint(4, 6)
        watch = sorted(rng.sample(keys[4:], nw))
        runs = {}
        for i, w in enumerate(watch):
            pad = rng.sample(keys, rng.randint(2, 5))
            runs["r%d" % i] = sorted(set(pad) | {w})
        tags = {"m0": list(keys)}
        if nk > 10:
            tags["m1"] = sorted(rng.sample(keys, rng.randint(8, 14)))
        return keys, runs, tags, watch
    nk = rng.randint(9, 15)
    keys = list(range(1, nk + 1))
    nw = rng.randint(4, 6)
    watch = sorted(rng.sample(keys, nw))
    rest = sorted(set(keys) - set(watch))
    nrun = rng.randint(2, 4)
    runs = {}
    left = list(watch)
    rng.shuffle(left)
    for i in range(nrun):
        take = sorted(left[i::nrun])
        pad = rng.sample(keys, rng.randint(1, 3))
        runs["r%d" % i] = sorted(set(take) | set(pad))
    for w in watch:
        if not any(w in runs[n] for n in runs):
            runs[sorted(runs)[0]] = sorted(set(runs[sorted(runs)[0]]) | {w})
    ntag = rng.randint(2, 4)
    tags = {}
    for i in range(ntag):
        seed = rng.sample(watch, min(len(watch), rng.randint(3, 4)))
        pad = rng.sample(keys, rng.randint(1, 3)) if rest else []
        tags["m%d" % i] = sorted(set(seed) | set(pad))
    return keys, runs, tags, watch


def script(rng, keys, runs, tags, watch, allow_bars=True):
    up = dict((k, k) for k in keys)
    bars = set()
    sent = set()
    live_r = sorted(runs)
    live_t = sorted(tags)
    owed = sorted(watch)
    out = []
    guard = 0
    while (live_r or live_t or owed) and guard < 80:
        guard += 1
        held = sorted(n for n in live_r
                      if any(w in runs[n] for w in owed))
        moves = []
        if owed:
            moves.append(("must", 5))
        if live_r:
            moves.append(("post", 5))
        if live_t:
            moves.append(("tie", 3))
            if allow_bars:
                moves.append(("bar", 5))
        if sorted(set(live_t) | (set(live_r) - set(held))):
            moves.append(("close", 2))
        if not moves:
            break
        pick = rng.choices([m for m, _ in moves], [w for _, w in moves])[0]
        if pick == "must":
            opts = sorted((n, w) for w in owed for n in live_r
                          if w in runs[n] and (n, w) not in sent)
            if not opts:
                break
            n, k = opts[rng.randrange(len(opts))]
            out.append("post %s %d %d" % (n, k, rng.randint(1, 99)))
            sent.add((n, k))
            owed = [w for w in owed if w != k]
        elif pick == "post":
            opts = sorted((n, k) for n in live_r for k in runs[n]
                          if (n, k) not in sent)
            if not opts:
                continue
            n, k = opts[rng.randrange(len(opts))]
            out.append("post %s %d %d" % (n, k, rng.randint(1, 99)))
            sent.add((n, k))
            owed = [w for w in owed if w != k]
        elif pick in ("tie", "bar"):
            opts = []
            for n in live_t:
                pool = tags[n]
                for i in range(len(pool)):
                    for j in range(i + 1, len(pool)):
                        a, b = pool[i], pool[j]
                        if _root(up, a) != _root(up, b) and not _barred(up, bars, a, b):
                            opts.append((n, a, b))
            if not opts:
                continue
            if pick == "bar":
                far = [o for o in opts
                       if not any(_root(up, w) in (_root(up, o[1]), _root(up, o[2]))
                                  for w in watch)]
                if far and rng.random() < 0.3:
                    opts = far
            n, a, b = opts[rng.randrange(len(opts))]
            if pick == "tie":
                out.append("tie %s %d %d" % (n, a, b))
                _weld(up, a, b)
            else:
                out.append("bar %s %d %d" % (n, a, b))
                bars.add((min(a, b), max(a, b)))
        else:
            pool = sorted(set(live_t) | (set(live_r) - set(held)))
            if not pool:
                continue
            n = pool[rng.randrange(len(pool))]
            out.append("shut %s" % n)
            live_r = [x for x in live_r if x != n]
            live_t = [x for x in live_t if x != n]
    for n in sorted(set(live_r) | set(live_t)):
        out.append("shut %s" % n)
    return out


def one(seed):
    rng = random.Random(seed)
    bits = str(seed).rsplit(":", 1)
    wide = len(bits) == 2 and bits[1].isdigit() and int(bits[1]) % 12 == 0
    keys, runs, tags, watch = shape(rng, wide=wide)
    body = script(rng, keys, runs, tags, watch, allow_bars=not wide)
    head = ["watch " + " ".join(str(k) for k in watch)]
    for n in sorted(runs):
        head.append("run %s %s" % (n, " ".join(str(k) for k in runs[n])))
    for n in sorted(tags):
        head.append("tag %s %s" % (n, " ".join(str(k) for k in tags[n])))
    head.append("go")
    return "\n".join(head + body) + "\n"


def batch(nonce, count):
    return [("g%04d" % i, one("%s:%d" % (nonce, i))) for i in range(count)]


def text(item):
    return item
