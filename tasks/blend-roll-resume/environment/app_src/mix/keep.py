def start(h, ranks, micro, accum):
    h.ranks = ranks
    h.micro = micro
    h.accum = accum


def save(h):
    b = h.book
    h.mark = {
        "step": h.step,
        "epoch": dict(h.epoch),
        "cur": dict(h.cur),
        "cnt": dict(h.cnt),
        "live": list(b.live),
        "weight": dict(b.weight),
    }


def stop(h):
    b = h.book
    mark = h.mark
    h.step = mark["step"]
    for name in mark["epoch"]:
        h.epoch[name] = mark["epoch"][name]
        h.cur[name] = mark["cur"][name]
        h.cnt[name] = mark["cnt"][name]
    b.live[:] = mark["live"]
    b.weight.update(mark["weight"])
    h.ranks = 0
    h.micro = 0
    h.accum = 0
