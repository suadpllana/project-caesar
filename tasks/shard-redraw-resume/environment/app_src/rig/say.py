def feed(run, rank, ids):
    run.out.append("feed %d %s" % (rank, " ".join(str(i) for i in ids)))


def step(run, done, sc):
    run.out.append("step %d %d" % (done, sc))


def skip(run, sc):
    run.out.append("skip %d" % sc)


def save(run, done, epoch, seen):
    run.out.append("save %d %d %d" % (done, epoch, seen))


def kill(run, epoch, seen):
    run.out.append("kill %d %d" % (epoch, seen))


def back(run, rank):
    run.out.append("back %d" % rank)


def roll(run, epoch):
    run.out.append("roll %d" % epoch)


def halt(run, done):
    run.out.append("halt %d" % done)
