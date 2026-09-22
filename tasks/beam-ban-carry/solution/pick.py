def take(cands, w):
    """Down the ranking, one beam per final token, at most w of them."""
    cands.sort(key=lambda one: (-one[0], one[1], one[2]))
    out, used = [], set()
    for one in cands:
        if one[2] in used:
            continue
        used.add(one[2])
        out.append(one)
        if len(out) == w:
            break
    return out
