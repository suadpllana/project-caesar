def why(step, cap, took, pool, best, p, g):
    if not took:
        return "dry"
    if step >= cap:
        return "cap"
    low = pool.worst()
    if low is None or not pool.full():
        return None
    room = cap - step
    lift = (g - p) * room if g > p else 0
    if best - p * step + lift <= low:
        return "bound"
    return None
