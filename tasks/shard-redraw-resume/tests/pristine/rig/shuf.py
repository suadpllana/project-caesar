M64 = (1 << 64) - 1

_SET = {}


def _mix(z):
    z = (z + 0x9E3779B97F4A7C15) & M64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return (z ^ (z >> 31)) & M64


def _wide(rows):
    k = 1
    while (1 << k) < rows:
        k += 1
    return k + (k & 1)


def _setup(seed, epoch, rank, rows):
    key = (seed, epoch, rank, rows)
    got = _SET.get(key)
    if got is None:
        k = _wide(rows)
        half = k >> 1
        salt = _mix(_mix(seed * 0x9E3779B1 + epoch) * 0xC2B2AE3D + rank)
        got = (half, (1 << half) - 1, salt)
        _SET[key] = got
    return got


def at(seed, epoch, rank, rows, i):
    half, mask, salt = _setup(seed, epoch, rank, rows)
    y = i
    while True:
        lo = y & mask
        hi = y >> half
        for rnd in range(4):
            hi, lo = lo, hi ^ (_mix(salt + (lo << 6) + rnd) & mask)
        y = (hi << half) | lo
        if y < rows:
            return y
