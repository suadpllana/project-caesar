def add(h, r):
    h.seq.append(r)


def drop(h, r):
    for n, x in enumerate(h.seq):
        if x is r:
            del h.seq[n]
            return


def live(h):
    return list(h.seq)
