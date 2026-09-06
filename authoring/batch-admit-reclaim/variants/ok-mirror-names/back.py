from eng.pool import keys


def at(pool, span, rq):
    aim = rq.plen if rq.have == 0 else rq.have
    clone = 0
    for tagged in keys(rq.toks, span, aim):
        if not pool.has(tagged):
            break
        clone += 1
    return clone * span
