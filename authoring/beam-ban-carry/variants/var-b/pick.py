def take(cands, w):
    best, seen = [], set()
    pool = sorted(cands, key=lambda c: (-c[0], c[1], c[2]))
    i = 0
    while i < len(pool) and len(best) < w:
        if pool[i][2] not in seen:
            seen.add(pool[i][2])
            best.append(pool[i])
        i += 1
    return best
