from mix import deck, lay, pick, say, walk


def go(h, count):
    wide = lay.width(h)
    for _ in range(count):
        gone = []
        seen = set()
        for pos in range(wide):
            name = pick.who(h)
            walk.take(h, name)
            if name not in seen and walk.spent(h, name):
                seen.add(name)
                gone.append((name, pos))
        for name, pos in gone:
            say.done(h, name, h.step, pos)
            deck.drop(h, name)
        h.step += 1


def feed(h, rank, slot):
    lo, hi = lay.span(h, rank, slot)
    got = []
    for pos in range(hi):
        name = pick.who(h)
        sample = walk.take(h, name)
        if pos >= lo:
            got.append("%s:%d" % (name, sample))
        if walk.spent(h, name):
            say.done(h, name, h.step, pos)
            deck.drop(h, name)
    say.feed(h, rank, slot, got)
