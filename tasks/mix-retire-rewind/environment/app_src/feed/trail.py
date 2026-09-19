def ids(box, got):
    return " ".join("%s.%d" % (box.names[j], x) for j, x in got)


def stand(box, seen):
    out = []
    for j, one in enumerate(seen):
        if one is None:
            out.append("%s:gone" % box.names[j])
        else:
            out.append("%s:%d:%d:%d" % (box.names[j], one[0], one[1], one[2]))
    return " ".join(out)


def show(box, run, step, rank, seat, got):
    box.out.append("show %s %d %d %d %s" % (run, step, rank, seat, ids(box, got)))


def save(box, tag, rec):
    box.out.append("save %s %d %d %d %s"
                   % (tag, rec["base"], rec["done"], rec["made"], stand(box, rec["at"])))


def load(box, run, base, seen):
    box.out.append("load %s %d %s" % (run, base, stand(box, seen)))
