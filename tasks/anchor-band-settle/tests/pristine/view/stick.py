def stuck(v, fl, s):
    out = set()
    for b, y in fl.top.items():
        if b.pin is not None and s + b.pin > y:
            out.add(b)
    return out
