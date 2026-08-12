MASK = 0xFFFFFFFF


def mix(a, b):
    v = (a * 2654435761 + b * 40503 + 0x9E37) & MASK
    v ^= v >> 13
    v = (v * 1274126177) & MASK
    return v ^ (v >> 16)
