def split(world, micro, accum, got):
    out = [[[] for _ in range(accum)] for _ in range(world)]
    for o, one in enumerate(got):
        seat = o // world
        out[o % world][seat // micro].append(one)
    return out
