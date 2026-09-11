def val(shown, value, home):
    return "val %s %d %d" % (shown, value, home)


def gone(shown):
    return "val %s gone" % shown


def loop(shown):
    return "val %s loop" % shown


def tot(shown, count):
    return "num %s %d" % (shown, count)
