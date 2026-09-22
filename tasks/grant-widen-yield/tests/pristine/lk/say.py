def hold(t, res, m):
    return "hold %s %s %s" % (t, res, m)


def thin(t, res, m):
    return "thin %s %s %s" % (t, res, m)


def give(t, res, m):
    return "give %s %s %s" % (t, res, m)


def free(t, res):
    return "free %s %s" % (t, res)


def wait(t, res, m):
    return "wait %s %s %s" % (t, res, m)


def wide(t, res, m, n):
    return "wide %s %s %s %d" % (t, res, m, n)


def shut(t):
    return "shut %s" % (t,)


def own(t, res, m):
    return "own %s %s %s" % (t, res, m)


def due(t, res, m):
    return "due %s %s %s" % (t, res, m)
