def order(st, ready):
    return sorted(ready, key=lambda p: (str(p[0]), int(p[1])))
