def done(h, name, step, pos):
    h.out.append("done %s %d %d" % (name, step, pos))


def feed(h, rank, slot, items):
    h.out.append("feed %d %d %s" % (rank, slot, " ".join(items)))


def at(h, name, epoch, cur):
    if epoch is None:
        h.out.append("at %s out" % name)
    else:
        h.out.append("at %s %d %d" % (name, epoch, cur))
