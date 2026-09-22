def ask(name):
    return "ask %s" % name


def shut(step, ln, fin):
    return "shut %d %d %d" % (step, ln, fin)


def gone(step, ln, fin):
    return "gone %d %d %d" % (step, ln, fin)


def halt(step, why):
    return "halt %d %s" % (step, why)


def hyp(rank, fin, ln, toks):
    return "hyp %d %d %d%s" % (rank, fin, ln, "".join(" %d" % x for x in toks))
