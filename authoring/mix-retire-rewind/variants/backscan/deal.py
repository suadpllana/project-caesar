def split(world, micro, accum, got):
    bins = {}
    for o, one in enumerate(got):
        bins.setdefault((o % world, (o // world) // micro), []).append(one)
    return [[bins.get((rank, seat), []) for seat in range(accum)] for rank in range(world)]
