def ran(f, name):
    f.out.append("run %s" % name)


def val(f, name, v):
    f.out.append("val %s %d" % (name, v))
