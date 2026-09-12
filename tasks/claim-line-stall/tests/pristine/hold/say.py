def grant(h, job, scope, mode):
    h.out.append("grant %s %s %s" % (job, scope, mode))


def wait(h, job, scope, mode):
    h.out.append("wait %s %s %s" % (job, scope, mode))


def free(h, job, scope, n):
    h.out.append("free %s %s %d" % (job, scope, n))


def over(h, job, n):
    h.out.append("end %s %d" % (job, n))


def stop(h, job, n):
    h.out.append("stop %s %d" % (job, n))


def show(h, unit, items, n):
    h.out.append("show %s %s %d" % (unit, items if items else "-", n))
