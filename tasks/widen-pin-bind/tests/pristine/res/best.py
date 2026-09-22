def winner(vecs):
    low = min(sum(vec) for vec in vecs)
    same = [i for i, vec in enumerate(vecs) if sum(vec) == low]
    if len(same) == 1:
        return same[0]
    return None
