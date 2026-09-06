def pick(pool):
    best = None
    rank = None
    for tagged in pool.blk:
        b = pool.blk[tagged]
        if b.refs:
            continue
        rq = (b.touch, b.born)
        if rank is None or rq < rank:
            best = tagged
            rank = rq
    return best
