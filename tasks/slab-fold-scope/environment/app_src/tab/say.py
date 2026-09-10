def land(tab, tag, num, add, gone):
    tab.out.append("land %s %d %d %d" % (tag, num, add, gone))


def void(tab, tag):
    tab.out.append("void %s" % tag)


def rows(tab, buck, n):
    tab.out.append("rows %s %d" % (buck, n))


def at(tab, buck, key, sid):
    tab.out.append("at %s %d %s" % (buck, key, "none" if sid is None else sid))
