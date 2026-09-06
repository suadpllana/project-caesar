def order(w, q):
    return sorted(q, key=lambda r: r.idx)


def victim(w, run):
    if not run:
        return None
    return max(run, key=lambda r: r.idx)
