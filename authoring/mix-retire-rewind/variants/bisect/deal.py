def split(world, micro, accum, got):
    out = []
    for rank in range(world):
        mine = []
        for seat in range(accum):
            mine.append([got[(seat * micro + p) * world + rank] for p in range(micro)])
        out.append(mine)
    return out
