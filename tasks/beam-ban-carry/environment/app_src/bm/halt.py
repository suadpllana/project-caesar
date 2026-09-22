def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    low = pool.worst()
    if low is None:
        return None
    if best - p * step + g * (cap - step) <= low:
        return "bound"
    return None
