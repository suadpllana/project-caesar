def vec(name, i):
    h = 2166136261
    for ch in name:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    h = ((h ^ (i + 1)) * 16777619) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) & 0xFFFFFFFF
    return [((h >> (7 * k)) % 9 - 4) / 4.0 for k in range(4)]
