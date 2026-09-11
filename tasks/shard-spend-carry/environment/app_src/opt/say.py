from opt import cut

TAG = ("val", "mom")


def own(r, k):
    at = cut.first(r, k)
    if at is None:
        r.out.append("own %d none" % k)
    else:
        r.out.append("own %d %s %d" % (k, at[0], at[1]))


def show(r, name, f):
    fold = []
    for c, x in r.par[name].runs(f):
        if fold and fold[-1][1] == x:
            fold[-1][0] += c
        else:
            fold.append([c, x])
    r.out.append("%s %s %s" % (TAG[f], name,
                               " ".join("%dx%d" % (c, x) for c, x in fold)))
