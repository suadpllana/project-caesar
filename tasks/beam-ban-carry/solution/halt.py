def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    if not pool.full():
        return None
    low = pool.worst()
    if best - p * step + max(0, g - p) * (cap - step) <= low:
        return "bound"
    return None
