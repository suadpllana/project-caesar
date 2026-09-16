def fit(room, rem):
    most = room if room < rem else rem
    if most < 1:
        return None
    return most
