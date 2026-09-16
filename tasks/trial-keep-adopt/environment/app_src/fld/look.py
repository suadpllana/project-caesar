from fld import keep


def fresh(f, name):
    held = keep.held(f, name)
    if held is not None:
        return held
    return keep.get(f, name)


def under(f, roots):
    gone = set(roots)
    while True:
        more = set()
        for who, args in f.args.items():
            if who in gone or who not in f.keep:
                continue
            for a in args:
                if a in gone:
                    more.add(who)
                    break
        if not more:
            return gone
        gone |= more


def sweep(f, roots):
    for who in under(f, roots):
        keep.cut(f, who)
