def dev(blocks):
    return "dev %d" % blocks


def fresh(name):
    return "n %s" % name


def stamp(name, items):
    return "p %s items=%d" % (name, items)


def drop(name, rel):
    return "d %s rel=%d" % (name, rel)


def write(who, new, keep, rel):
    return "w %s new=%d keep=%d rel=%d" % (who, new, keep, rel)


def share(who, rel):
    return "s %s rel=%d" % (who, rel)


def trim(who, rel):
    return "t %s rel=%d" % (who, rel)


def erase(who, rel):
    return "x %s rel=%d" % (who, rel)


def vac(who, new, rel):
    return "v %s new=%d rel=%d" % (who, new, rel)


def charge(name, ref, excl):
    return "c %s ref=%d excl=%d" % (name, ref, excl)


def family(name, ref, excl):
    return "u %s ref=%d excl=%d" % (name, ref, excl)


def gone(names, rel):
    return "g %s rel=%d" % (names, rel)


def room(total, runs, big):
    return "f free=%d runs=%d big=%d" % (total, runs, big)


def chart(who, size, bits):
    head = "m %s size=%d" % (who, size)
    if not bits:
        return head
    return head + " " + " ".join("%d:%d+%d:%d" % b for b in bits)


def bad(cmd, who, code):
    if who is None:
        return "%s err=%s" % (cmd, code)
    return "%s %s err=%s" % (cmd, who, code)
