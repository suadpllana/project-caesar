def order(w, q):
    return sorted(q, key=lambda rq: rq.idx)


def victim(w, run):
    if not run:
        return None
    return max(run, key=lambda rq: rq.idx)
