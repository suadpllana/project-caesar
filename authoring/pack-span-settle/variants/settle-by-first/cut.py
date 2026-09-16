def fit(room, rem):
    most = room if room < rem else rem
    if most < 2:
        return None
    left = rem - most
    if left == 0 or left >= 2:
        return most
    if most > 2:
        return most - 1
    return None
