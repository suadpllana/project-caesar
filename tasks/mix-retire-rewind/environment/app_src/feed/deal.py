def split(world, micro, accum, got):
    out = []
    per = micro * accum
    for r in range(world):
        mine = got[r * per:(r + 1) * per]
        out.append([mine[i * micro:(i + 1) * micro] for i in range(accum)])
    return out
