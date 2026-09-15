"""Correct variant: the segment end is bisected rather than solved for.

`pick.spot` is never used. The departure is found by asking `after` how far the segment has to
go before the source has taken its last permitted draw, and bisecting that distance, which is
what a caller with no closed form would do. The step layout, the feed and everything else are
the same contract.
"""
from mix import deck, lay, pick, say, walk


def go(h, count):
    wide = lay.width(h)
    base = h.step
    left = count * wide
    done = 0
    while left > 0:
        seen = sum(h.cnt[name] for name in h.book.live)
        near = _nearest(h, seen)
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


def _nearest(h, seen):
    """The smallest advance that finishes some capped source's cap, and which source."""
    best = None
    for name in h.book.live:
        room = walk.left(h, name)
        if room is None:
            continue
        want = h.cnt[name] + room
        lo, hi = 0, 1
        while pick.after(h, h.book.live, seen + hi)[name] < want:
            hi *= 2
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if pick.after(h, h.book.live, seen + mid)[name] < want:
                lo = mid
            else:
                hi = mid
        if best is None or hi < best[0]:
            best = (hi, name)
    return best


def _slide(h, seen, count):
    fresh = pick.after(h, h.book.live, seen + count)
    for name in h.book.live:
        walk.jump(h, name, fresh[name] - h.cnt[name])


def feed(h, rank, slot):
    lo, hi = lay.span(h, rank, slot)
    was = (list(h.book.live), dict(h.cnt), dict(h.epoch), dict(h.cur))
    got = []
    for pos in range(hi):
        name = pick.who(h)
        one = walk.take(h, name)
        if pos >= lo:
            got.append("%s:%d" % (name, one))
        if walk.spent(h, name):
            deck.drop(h, name)
    h.book.live[:], cnt, epoch, cur = was
    h.cnt.update(cnt)
    h.epoch.update(epoch)
    h.cur.update(cur)
    say.feed(h, rank, slot, got)
