def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    if not pool.full():
        return None
    gain = g - p
    if gain < 0:
        gain = 0
    return "bound" if best - p * step + gain * (cap - step) <= pool.worst() else None
