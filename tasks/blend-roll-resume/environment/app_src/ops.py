from mix import deck, keep, turn


def ex(h, p):
    kind = p[0]
    if kind == "seed":
        h.seed = int(p[1])
    elif kind == "src":
        deck.add(h, p[1], int(p[2]), int(p[3]), int(p[4]))
    elif kind == "wt":
        deck.weigh(h, p[1], int(p[2]))
    elif kind == "run":
        keep.start(h, int(p[1]), int(p[2]), int(p[3]))
    elif kind == "save":
        keep.save(h)
    elif kind == "stop":
        keep.stop(h)
    elif kind == "go":
        turn.go(h, int(p[1]))
    elif kind == "feed":
        turn.feed(h, int(p[1]), int(p[2]))
    elif kind == "at":
        deck.at(h, p[1])
    else:
        raise ValueError(kind)
