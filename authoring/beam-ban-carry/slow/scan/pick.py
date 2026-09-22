def take(cands, w):
    out = []
    seen = set()
    for one in sorted(cands, key=lambda c: (-c[0], c[1], c[2])):
        if one[2] not in seen:
            seen.add(one[2])
            out.append(one)
            if len(out) >= w:
                break
    return out
