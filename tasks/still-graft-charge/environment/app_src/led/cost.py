from led import hold


def charge(st, name):
    total = 0
    for b in st.lines[name].head.values():
        if hold.sole(st, b):
            total += b.size
    return total


def after(st, name, lo, hi, size):
    return charge(st, name) + (hi - lo + 1) * size
