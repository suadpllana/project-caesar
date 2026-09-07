from prog.deck import CLASH


def line(un, x, b):
    if b is None:
        return "%s %s none" % (un, x)
    kind, tgt, rank = b
    if kind == CLASH:
        return "%s %s clash %d" % (un, x, rank)
    return "%s %s %s %s %d" % (un, x, kind, tgt, rank)
