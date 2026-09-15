#!/bin/bash
set -euo pipefail

# the accumulation depth does not widen a step

cat > /app/mix/deck.py <<'PYEOF'
"""The manifest side: who is in the blend, what they weigh, and who has left.

Every change here is a blend change, and a blend change is what returns the draw counters to
zero. Declaring a source mid-run is one, reweighing is one whatever weight it names, and a
departure is one.
"""
from mix import say


def add(h, name, n, w, cap):
    b = h.book
    b.names.append(name)
    b.size[name] = n
    b.weight[name] = w
    b.cap[name] = cap
    b.live.append(name)
    h.epoch[name] = 0
    h.cur[name] = 0
    h.cnt[name] = 0
    rebase(h)


def weigh(h, name, w):
    h.book.weight[name] = w
    rebase(h)


def drop(h, name):
    h.book.live.remove(name)
    rebase(h)


def rebase(h):
    for name in h.book.live:
        h.cnt[name] = 0


def sig(h):
    """The blend as the draw rule sees it: who is live, in order, and what each weighs."""
    b = h.book
    return tuple(b.live), tuple(b.weight[name] for name in b.live)


def at(h, name):
    if name in h.book.live:
        say.at(h, name, h.epoch[name], h.cur[name])
    else:
        say.at(h, name, None, None)
PYEOF

cat > /app/mix/pick.py <<'PYEOF'
"""The draw rule, and the two arithmetic readings of it that let the run skip ahead.

A draw goes to the live source with the smallest counter over weight, the earlier declared
source taking a tie. Read as virtual time, source `s` takes its j-th draw of the segment at
time j / w[s], and draws are taken in increasing time with declaration order breaking a tie.
Two questions follow from that and neither needs the draws to be taken:

  after  - the counters once `seen` draws of the segment have gone, by binary search for the
           virtual time the last of them sits at, over the grid of the weights' lowest common
           multiple, where every candidate time lies;
  spot   - which draw of the segment is a given source's j-th, read straight off the same
           relation: everything strictly earlier, plus the source's place among the ties.
"""
from math import gcd


def who(h):
    b = h.book
    best = None
    for name in b.live:
        if best is None:
            best = name
        elif h.cnt[name] * b.weight[best] < h.cnt[best] * b.weight[name]:
            best = name
    return best


def _grid(h, live):
    """Every candidate virtual time j / w[s] lies on this many parts of one unit."""
    out = 1
    for name in live:
        w = h.book.weight[name]
        out = out * w // gcd(out, w)
    return out


def _before(h, live, m, grid):
    """Draws strictly before virtual time m / grid."""
    return sum((m * h.book.weight[name] + grid - 1) // grid for name in live)


def after(h, live, seen):
    """Counters after `seen` draws of a segment that began with every counter at zero."""
    if seen <= 0:
        return {name: 0 for name in live}
    grid = _grid(h, live)
    lo, hi = 0, 1
    while _before(h, live, hi, grid) <= seen:
        hi *= 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if _before(h, live, mid, grid) <= seen:
            lo = mid
        else:
            hi = mid
    out = {name: (lo * h.book.weight[name] + grid - 1) // grid for name in live}
    over = seen - _before(h, live, lo, grid)
    tied = [name for name in live if (lo * h.book.weight[name]) % grid == 0]
    for name in tied[:over]:
        out[name] += 1
    return out


def spot(h, live, name, j):
    """Which draw of the segment is `name`'s draw number j. Both counted from zero."""
    own = h.book.weight[name]
    before = sum((j * h.book.weight[other] + own - 1) // own for other in live)
    tied = [other for other in live if (j * h.book.weight[other]) % own == 0]
    return before + tied.index(name)
PYEOF

cat > /app/mix/walk.py <<'PYEOF'
"""One source's own progress: the sample a draw takes, and the cap boundary.

`take` is the per-draw reading, used where a step is actually laid out. `jump` is the same
advance done arithmetically, which is what makes a run of a million steps affordable: a source
that took `count` draws is `count` samples further along its permutation, whatever number of
epochs that crosses. `left` reads the cap the other way, as draws remaining before the source
finishes the last epoch it may serve.
"""
from mix import perm


def take(h, name):
    b = h.book
    row = perm.order(h.seed, b.names.index(name), h.epoch[name], b.size[name])
    sample = row[h.cur[name]]
    h.cnt[name] += 1
    h.cur[name] += 1
    if h.cur[name] == b.size[name]:
        h.cur[name] = 0
        h.epoch[name] += 1
    return sample


def jump(h, name, count):
    n = h.book.size[name]
    total = h.epoch[name] * n + h.cur[name] + count
    h.epoch[name] = total // n
    h.cur[name] = total % n
    h.cnt[name] += count


def spent(h, name):
    cap = h.book.cap[name]
    return cap and h.epoch[name] >= cap


def left(h, name):
    """Draws before this source finishes its cap, or None when it has no cap."""
    cap = h.book.cap[name]
    if not cap:
        return None
    n = h.book.size[name]
    return cap * n - (h.epoch[name] * n + h.cur[name])
PYEOF

cat > /app/mix/lay.py <<'PYEOF'
"""Where a step's draws go. The draws themselves know nothing about any of these three."""


def width(h):
    return h.ranks * h.micro


def span(h, rank, slot):
    lo = (slot * h.ranks + rank) * h.micro
    return lo, lo + h.micro
PYEOF

cat > /app/mix/keep.py <<'PYEOF'
"""The checkpoint, which holds the run and not the blend.

What goes back on a stop is the step, and the epoch, cursor and counter of every source the
checkpoint holds. Who is live and what they weigh is the manifest's, and the manifest is
durable: a departure or a reweighing since the checkpoint stands. Which is why the restored
counters cannot simply be believed - they were written under a blend that may no longer be the
one in force, and when the two differ they are worth nothing and the segment starts again.
"""
from mix import deck


def start(h, ranks, micro, accum):
    h.ranks = ranks
    h.micro = micro
    h.accum = accum


def save(h):
    h.mark = {
        "step": h.step,
        "epoch": dict(h.epoch),
        "cur": dict(h.cur),
        "cnt": dict(h.cnt),
        "sig": deck.sig(h),
    }


def stop(h):
    mark = h.mark
    h.step = mark["step"]
    for name in mark["epoch"]:
        h.epoch[name] = mark["epoch"][name]
        h.cur[name] = mark["cur"][name]
        h.cnt[name] = mark["cnt"][name]
    if deck.sig(h) != mark["sig"]:
        deck.rebase(h)
    h.ranks = 0
    h.micro = 0
    h.accum = 0
PYEOF

cat > /app/mix/turn.py <<'PYEOF'
"""Running steps, and showing the one that has not been taken yet.

A go is a walk over segments, not over steps. Inside one segment nothing about the blend
changes, so the counters at any distance are arithmetic and so is the draw at which the next
capped source finishes. The run therefore advances to whichever comes first - the end of the
go, or the departure - settles that whole stretch in one move, prints the departure where it
fell, and starts the next segment. The cost follows the number of blend changes, and a go of
four million steps costs the same as a go of one.

A feed is the opposite shape: one step, laid out draw by draw, because the samples themselves
are wanted and a departure inside the step has to land in the right place. It is a question,
so everything it touched goes back afterwards and the departure it saw is not announced.
"""
from mix import deck, lay, pick, say, walk


def go(h, count):
    wide = lay.width(h)
    base = h.step
    left = count * wide
    done = 0
    while left > 0:
        seen = sum(h.cnt[name] for name in h.book.live)
        near = None
        for name in h.book.live:
            room = walk.left(h, name)
            if room is None:
                continue
            need = pick.spot(h, h.book.live, name, h.cnt[name] + room - 1) + 1 - seen
            if near is None or need < near[0]:
                near = (need, name)
        if near is not None and near[0] <= left:
            _slide(h, seen, near[0])
            done += near[0]
            left -= near[0]
            say.done(h, near[1], base + (done - 1) // wide, (done - 1) % wide)
            deck.drop(h, near[1])
        else:
            _slide(h, seen, left)
            done += left
            left = 0
    h.step = base + count


def _slide(h, seen, count):
    """Take `count` draws of the current segment without laying any of them out."""
    fresh = pick.after(h, h.book.live, seen + count)
    for name in h.book.live:
        walk.jump(h, name, fresh[name] - h.cnt[name])


def feed(h, rank, slot):
    lo, hi = lay.span(h, rank, slot)
    was_live = list(h.book.live)
    was_cnt = dict(h.cnt)
    was_ep = dict(h.epoch)
    was_cur = dict(h.cur)
    got = []
    for pos in range(hi):
        name = pick.who(h)
        sample = walk.take(h, name)
        if pos >= lo:
            got.append("%s:%d" % (name, sample))
        if walk.spent(h, name):
            deck.drop(h, name)
    h.book.live[:] = was_live
    h.cnt.update(was_cnt)
    h.epoch.update(was_ep)
    h.cur.update(was_cur)
    say.feed(h, rank, slot, got)
PYEOF

