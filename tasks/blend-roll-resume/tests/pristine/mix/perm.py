_W = 0xFFFFFFFFFFFFFFFF
_KEEP = 8
_rows = {}


def _turn(x):
    x = (x + 0x9E3779B97F4A7C15) & _W
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & _W
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & _W
    return x ^ (x >> 31)


def order(seed, idx, epoch, n):
    key = (seed, idx, epoch)
    row = _rows.get(key)
    if row is None:
        s = _turn(seed * 0x1000193 + idx * 0x01000193 + epoch)
        row = list(range(n))
        for i in range(n - 1, 0, -1):
            s = _turn(s)
            j = s % (i + 1)
            row[i], row[j] = row[j], row[i]
        if len(_rows) >= _KEEP:
            _rows.clear()
        _rows[key] = row
    return row
