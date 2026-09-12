def take(job, bundle, unit):
    job.out.append("take %s %s" % (bundle, unit))


def dup(job, name, unit):
    job.out.append("dup %s %s" % (name, unit))


def at(job, name, spot):
    if spot is None:
        job.out.append("at %s none" % name)
    elif len(spot) == 3:
        job.out.append("at %s spare %s %d" % (name, spot[1], spot[2]))
    else:
        job.out.append("at %s %s %d" % (name, spot[0], spot[1]))


def img(job, pair):
    job.out.append("img %d %d" % (pair[0], pair[1]))
