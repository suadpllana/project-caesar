def at(out, name, a, n):
    out.append("at %s %d %d" % (name, a, n))


def no(out, name):
    out.append("no %s" % name)


def same(out, name, n):
    out.append("same %s %d" % (name, n))
