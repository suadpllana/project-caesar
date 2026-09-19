M = (1 << 64) - 1


def hand(seed, sid, ep, n):
    x = (seed * 6364136223846793005 + (sid + 1) * 1442695040888963407
         + ep * 2862933555777941757 + 1) & M or 1
    out = list(range(n))
    for i in range(n - 1, 0, -1):
        x ^= (x << 13) & M
        x &= M
        x ^= x >> 7
        x ^= (x << 17) & M
        x &= M
        j = x % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out
