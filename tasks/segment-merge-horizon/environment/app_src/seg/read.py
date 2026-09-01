from seg import rec


def resolve(rs):
    acc = 0
    n = 0
    for r in rs:
        if r.t == rec.ADD:
            acc += r.v
            n += 1
        elif r.t == rec.PUT:
            return acc + r.v
        else:
            return acc if n else None
    return acc if n else None
