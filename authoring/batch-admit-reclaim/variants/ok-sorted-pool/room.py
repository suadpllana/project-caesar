def pick(pool):
    loose = [k for k in pool.blk if pool.blk[k].refs == 0]
    if not loose:
        return None
    return min(loose, key=lambda k: (pool.blk[k].touch, pool.blk[k].born))
