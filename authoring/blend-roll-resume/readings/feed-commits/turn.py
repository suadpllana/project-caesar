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
    say.feed(h, rank, slot, got)
