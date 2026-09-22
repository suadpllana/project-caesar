def take(cands, w):
    ranked = sorted(cands, key=lambda one: (-one[0], one[2], one[1]))
    return ranked[:w]
