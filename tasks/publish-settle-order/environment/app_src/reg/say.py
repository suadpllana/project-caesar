def up(out, name):
    out.append("up " + name)


def down(out, name):
    out.append("down " + name)


def ran(out, caller, sym, target):
    out.append("run %s %s %s" % (caller, sym, target))


def miss(out, caller, sym):
    out.append("miss %s %s" % (caller, sym))


def dead(out, caller, sym):
    out.append("dead %s %s" % (caller, sym))
